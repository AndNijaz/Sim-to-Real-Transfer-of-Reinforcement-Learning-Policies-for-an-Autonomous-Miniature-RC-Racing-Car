import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import time
import csv
import select
import termios
import tty
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch as th
import torch.nn as nn

from stable_baselines3 import SAC
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from real_camera_adapter import RealCameraAdapter
from car_controller_v2 import CarController


class CustomCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=128):
        super().__init__(observation_space, features_dim)

        n_input_channels = observation_space.shape[0]

        self.net = nn.Sequential(
            nn.Conv2d(n_input_channels, 16, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
        )

        self.linear = nn.Linear(64, features_dim)

    def forward(self, observations):
        return self.linear(self.net(observations))


class NonBlockingKeyboard:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self):
        readable, _, _ = select.select([sys.stdin], [], [], 0)
        if readable:
            return sys.stdin.read(1)
        return None


MODEL_PATH = "/home/na-33/best_model_sac.zip"
ARDUINO_PORT = "/dev/ttyUSB0"

CAM_WIDTH = 160
CAM_HEIGHT = 80
FRAME_STACK = 2

max_model_steering = 0.85
fixed_throttle = 0.45
THROTTLE_STEP = 0.025
MAX_FIXED_THROTTLE = 0.65

invert_steering = False
SMOOTH = False

CONTROL_HZ = 8.0
CONTROL_DT = 1.0 / CONTROL_HZ

MAX_ARMED_SECONDS = 30.0

VIDEO_FPS = 10.0
VIDEO_SCALE = 4

# Save one preprocessed camera frame every N control steps.
# These images show what the model sees after preprocessing.
IMAGE_SAVE_EVERY_N = 5

# Tuning for real-world SAC deployment
START_BOOST_THROTTLE = 0.70
START_BOOST_SECONDS = 0.35

MANUAL_BOOST_THROTTLE = 0.85
MANUAL_BOOST_SECONDS = 0.35

# 1.0 = no smoothing, lower = smoother but slower response
STEERING_SMOOTH_ALPHA = 0.70

# If steering is very high, reduce throttle so the car does not push hard into the wall.
ANTI_WALL_STEERING_THRESHOLD = 0.85
ANTI_WALL_THROTTLE = 0.40

# Positive value reduces the current left bias
STEERING_OFFSET = 0.10


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def load_sac_model(model_path):
    custom_objects = {
        "policy_kwargs": {
            "features_extractor_class": CustomCNN,
            "features_extractor_kwargs": {
                "features_dim": 128,
            },
            "normalize_images": False,
        },
        "replay_buffer": None,
        "buffer_size": 1,
        "learning_starts": 0,
    }

    return SAC.load(model_path, device="cpu", custom_objects=custom_objects)


def obs_to_video_frame(obs, armed, raw_steering, sent_steering, throttle):
    latest_rgb_chw = obs[-3:, :, :]
    latest_rgb_hwc = np.transpose(latest_rgb_chw, (1, 2, 0))
    latest_rgb_hwc = np.clip(latest_rgb_hwc * 255.0, 0, 255).astype(np.uint8)

    frame_bgr = cv2.cvtColor(latest_rgb_hwc, cv2.COLOR_RGB2BGR)

    frame_bgr = cv2.resize(
        frame_bgr,
        (CAM_WIDTH * VIDEO_SCALE, CAM_HEIGHT * VIDEO_SCALE),
        interpolation=cv2.INTER_NEAREST,
    )

    cv2.putText(
        frame_bgr,
        f"armed={armed} raw={raw_steering:.2f} sent={sent_steering:.2f} thr={throttle:.2f}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return frame_bgr


def main():
    global fixed_throttle
    global max_model_steering
    global invert_steering

    try:
        th.set_num_threads(1)
    except Exception:
        pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"real_sac_record_{timestamp}.csv"
    video_path = f"real_sac_camera_{timestamp}.avi"
    image_dir = Path(f"real_sac_frames_{timestamp}")
    image_dir.mkdir(exist_ok=True)

    print("\nLoading SAC model...")
    model = load_sac_model(MODEL_PATH)
    print("SAC model loaded.")
    print(f"Model observation space: {model.observation_space}")
    print(f"Model action space: {model.action_space}")

    camera = RealCameraAdapter(
        width=CAM_WIDTH,
        height=CAM_HEIGHT,
        channels_first=True,
        normalize=True,
        convert_bgr_to_rgb=True,
        frame_stack=FRAME_STACK,
    )

    car = None
    log_file = None
    writer = None

    print("\nREAL SAC TRACK RECORD V1")
    print("Controls:")
    print("  g = ARM autonomous run")
    print("  h = DISARM, center and stop")
    print("  w = increase fixed throttle")
    print("  s = decrease fixed throttle")
    print("  b = short manual boost")
    print("  z = decrease max steering")
    print("  c = increase max steering")
    print("  i = invert steering")
    print("  x = center and stop")
    print("  space = emergency stop")
    print("  q = quit")
    print("")
    print(f"CSV log: {log_path}")
    print(f"Camera video: {video_path}")
    print(f"Image frames folder: {image_dir}")
    print("Recommended: w, w, g. Stop with space or h.\n")

    armed = False
    armed_start_time = None

    last_control_time = 0.0
    last_print_time = 0.0
    frame_save_count = 0
    control_step_count = 0
    manual_boost_until = 0.0
    smoothed_steering = 0.0

    try:
        log_file = open(log_path, "w", newline="")
        logger = csv.writer(log_file)

        logger.writerow([
            "time_s",
            "armed",
            "raw_steering",
            "raw_model_throttle",
            "model_steering",
            "sent_steering",
            "fixed_throttle",
            "servo_us",
            "esc_us",
            "max_model_steering",
            "invert_steering",
            "camera_fps",
        ])

        writer = cv2.VideoWriter(
            video_path,
            cv2.VideoWriter_fourcc(*"MJPG"),
            VIDEO_FPS,
            (CAM_WIDTH * VIDEO_SCALE, CAM_HEIGHT * VIDEO_SCALE),
        )

        if not writer.isOpened():
            raise RuntimeError("Could not open video writer.")

        camera.start()

        car = CarController(
            arduino_port=ARDUINO_PORT,

            servo_left_us=1800,
            servo_center_us=1520,
            servo_right_us=1200,

            esc_stop_us=1498,
            esc_max_safe_us=1600,

            max_throttle=1.00,

            max_steering_delta=0.35,
            max_throttle_delta=0.08,
        )

        car.drive(0.0, 0.0, smooth=False, print_arduino=False)

        test_start_time = time.time()

        with NonBlockingKeyboard() as keyboard:
            while True:
                key = keyboard.get_key()

                if key == "g":
                    armed = True
                    armed_start_time = time.time()
                    print(f"\nARMED for max {MAX_ARMED_SECONDS:.1f}s.\n")

                elif key == "h":
                    armed = False
                    armed_start_time = None
                    car.center_and_stop()
                    print("\nDISARMED: centered and stopped.\n")

                elif key == "w":
                    fixed_throttle = clamp(fixed_throttle + THROTTLE_STEP, 0.0, MAX_FIXED_THROTTLE)
                    print(f"\nfixed_throttle increased to {fixed_throttle:.2f}\n")

                elif key == "s":
                    fixed_throttle = clamp(fixed_throttle - THROTTLE_STEP, 0.0, MAX_FIXED_THROTTLE)
                    print(f"\nfixed_throttle decreased to {fixed_throttle:.2f}\n")

                elif key == "b":
                    manual_boost_until = time.time() + MANUAL_BOOST_SECONDS
                    print(f"\nMANUAL BOOST for {MANUAL_BOOST_SECONDS:.2f}s at throttle {MANUAL_BOOST_THROTTLE:.2f}\n")

                elif key == "z":
                    max_model_steering = clamp(max_model_steering - 0.05, 0.10, 1.00)
                    print(f"\nmax_model_steering decreased to {max_model_steering:.2f}\n")

                elif key == "c":
                    max_model_steering = clamp(max_model_steering + 0.05, 0.10, 1.00)
                    print(f"\nmax_model_steering increased to {max_model_steering:.2f}\n")

                elif key == "i":
                    invert_steering = not invert_steering
                    print(f"\ninvert_steering = {invert_steering}\n")

                elif key == "x":
                    armed = False
                    armed_start_time = None
                    car.center_and_stop()
                    print("\nCENTER + STOP\n")

                elif key == " ":
                    armed = False
                    armed_start_time = None
                    car.center_and_stop()
                    print("\nEMERGENCY STOP\n")

                elif key == "q" or key == "\x03":
                    break

                now = time.time()

                if armed and armed_start_time is not None:
                    if now - armed_start_time >= MAX_ARMED_SECONDS:
                        armed = False
                        armed_start_time = None
                        car.center_and_stop()
                        print("\nAUTO DISARM: max armed time reached. Centered and stopped.\n")

                if now - last_control_time < CONTROL_DT:
                    time.sleep(0.002)
                    continue

                last_control_time = now

                obs = camera.get_observation().astype(np.float32)

                action, _ = model.predict(obs, deterministic=True)
                action = np.array(action).flatten()

                raw_steering = float(action[0])
                raw_model_throttle = float(action[1])

                steering_for_model = -raw_steering if invert_steering else raw_steering

                # Small right-side correction because the real camera/model currently has left bias.
                steering_for_model = steering_for_model + STEERING_OFFSET

                target_steering = clamp(
                    steering_for_model,
                    -max_model_steering,
                    max_model_steering,
                )

                smoothed_steering = (
                    STEERING_SMOOTH_ALPHA * target_steering
                    + (1.0 - STEERING_SMOOTH_ALPHA) * smoothed_steering
                )

                model_steering = clamp(
                    smoothed_steering,
                    -max_model_steering,
                    max_model_steering,
                )

                if armed:
                    sent_steering = model_steering

                    # Start boost helps overcome static friction.
                    in_start_boost = (
                        armed_start_time is not None
                        and (now - armed_start_time) < START_BOOST_SECONDS
                    )

                    # Manual boost is triggered with key 'b'.
                    in_manual_boost = now < manual_boost_until

                    if in_start_boost:
                        sent_throttle = max(fixed_throttle, START_BOOST_THROTTLE)
                    elif in_manual_boost:
                        sent_throttle = max(fixed_throttle, MANUAL_BOOST_THROTTLE)
                    else:
                        if abs(sent_steering) >= ANTI_WALL_STEERING_THRESHOLD:
                            sent_throttle = min(fixed_throttle, ANTI_WALL_THROTTLE)
                        else:
                            sent_throttle = fixed_throttle
                else:
                    sent_steering = 0.0
                    sent_throttle = 0.0
                    smoothed_steering = 0.0

                debug = car.drive(
                    sent_steering,
                    sent_throttle,
                    smooth=SMOOTH,
                    print_arduino=False,
                )

                info = camera.get_info()
                time_s = now - test_start_time

                video_frame = obs_to_video_frame(
                    obs,
                    armed,
                    raw_steering,
                    sent_steering,
                    sent_throttle,
                )
                writer.write(video_frame)

                control_step_count += 1

                if armed and control_step_count % IMAGE_SAVE_EVERY_N == 0:
                    frame_filename = (
                        image_dir
                        / f"frame_{frame_save_count:05d}_t{time_s:.2f}_steer{sent_steering:.2f}_thr{sent_throttle:.2f}.jpg"
                    )
                    cv2.imwrite(str(frame_filename), video_frame)
                    frame_save_count += 1

                logger.writerow([
                    f"{time_s:.3f}",
                    armed,
                    f"{raw_steering:.4f}",
                    f"{raw_model_throttle:.4f}",
                    f"{model_steering:.4f}",
                    f"{sent_steering:.4f}",
                    f"{sent_throttle:.4f}",
                    debug["sent_servo_us"],
                    debug["sent_esc_us"],
                    f"{max_model_steering:.2f}",
                    invert_steering,
                    f"{info['average_fps']:.2f}",
                ])
                log_file.flush()

                if now - last_print_time >= 0.25:
                    print(
                        f"armed={armed} | "
                        f"raw=[{raw_steering:.3f}, {raw_model_throttle:.3f}] | "
                        f"sent_steer={sent_steering:.3f} | "
                        f"thr={sent_throttle:.2f} | "
                        f"servo={debug['sent_servo_us']} | "
                        f"esc={debug['sent_esc_us']} | "
                        f"max_steer={max_model_steering:.2f} | "
                        f"invert={invert_steering} | "
                        f"fps={info['average_fps']:.1f}"
                    )

                    last_print_time = now

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        print("\nStopping car and camera.")

        if car is not None:
            car.close()

        camera.stop()

        if writer is not None:
            writer.release()

        if log_file is not None:
            log_file.close()

        print(f"Video saved: {video_path}")
        print(f"Log saved: {log_path}")
        print(f"Image frames saved in: {image_dir}")


if __name__ == "__main__":
    main()
