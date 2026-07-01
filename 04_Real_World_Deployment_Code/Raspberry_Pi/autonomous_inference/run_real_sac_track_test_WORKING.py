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


# =========================
# SETTINGS
# =========================

MODEL_PATH = "/home/na-33/best_model_sac.zip"
ARDUINO_PORT = "/dev/ttyUSB0"

CAM_WIDTH = 160
CAM_HEIGHT = 80
FRAME_STACK = 2

# Start safe. Increase later if it is too weak.
max_model_steering = 1.00

fixed_throttle = 0.00
THROTTLE_STEP = 0.05
MAX_FIXED_THROTTLE = 0.35

# If model turns opposite direction, press i to invert steering.
invert_steering = False

SMOOTH = False

CONTROL_HZ = 10.0
CONTROL_DT = 1.0 / CONTROL_HZ

# Safety: each ARM run automatically stops after this many seconds.
MAX_ARMED_SECONDS = 120


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


def main():
    global fixed_throttle
    global max_model_steering
    global invert_steering

    try:
        th.set_num_threads(1)
    except Exception:
        pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"real_sac_track_test_{timestamp}.csv"

    print("\nLoading SAC model...")
    model = load_sac_model(MODEL_PATH)
    print("SAC model loaded.")

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

    print("\nREAL SAC TRACK TEST V1")
    print("Safety behavior:")
    print(f"  g = arm for max {MAX_ARMED_SECONDS:.1f} seconds")
    print("  h / x / space = stop immediately")
    print("")
    print("Controls:")
    print("  g = ARM short autonomous run")
    print("  h = DISARM, center and stop")
    print("  w = increase fixed throttle")
    print("  s = decrease fixed throttle")
    print("  z = decrease max steering")
    print("  c = increase max steering")
    print("  i = invert steering direction")
    print("  x = center and stop")
    print("  space = emergency stop")
    print("  q = quit")
    print("")
    print("Recommended first run:")
    print("  w once -> fixed_throttle 0.05")
    print("  g -> watch for 3 seconds")
    print("  h/space if needed")
    print("")
    print(f"CSV log: {log_path}\n")

    armed = False
    armed_start_time = None

    last_control_time = 0.0
    last_print_time = 0.0

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
                    fixed_throttle = clamp(
                        fixed_throttle + THROTTLE_STEP,
                        0.0,
                        MAX_FIXED_THROTTLE,
                    )
                    print(f"\nfixed_throttle increased to {fixed_throttle:.2f}\n")

                elif key == "s":
                    fixed_throttle = clamp(
                        fixed_throttle - THROTTLE_STEP,
                        0.0,
                        MAX_FIXED_THROTTLE,
                    )
                    print(f"\nfixed_throttle decreased to {fixed_throttle:.2f}\n")

                elif key == "z":
                    max_model_steering = clamp(
                        max_model_steering - 0.05,
                        0.10,
                        1.00,
                    )
                    print(f"\nmax_model_steering decreased to {max_model_steering:.2f}\n")

                elif key == "c":
                    max_model_steering = clamp(
                        max_model_steering + 0.05,
                        0.10,
                        1.00,
                    )
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

                # Auto-disarm safety timer
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

                if invert_steering:
                    raw_steering = -raw_steering

                model_steering = clamp(
                    raw_steering,
                    -max_model_steering,
                    max_model_steering,
                )

                if armed:
                    sent_steering = model_steering
                    sent_throttle = fixed_throttle
                else:
                    sent_steering = 0.0
                    sent_throttle = 0.0

                debug = car.drive(
                    sent_steering,
                    sent_throttle,
                    smooth=SMOOTH,
                    print_arduino=False,
                )

                info = camera.get_info()
                time_s = now - test_start_time

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
                        f"model_steer={model_steering:.3f} | "
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

        if log_file is not None:
            log_file.close()
            print(f"Log saved: {log_path}")


if __name__ == "__main__":
    main()
