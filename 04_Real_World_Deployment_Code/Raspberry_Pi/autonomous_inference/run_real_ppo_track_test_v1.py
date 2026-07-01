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
import cv2
import depthai as dai
import torch as th

from stable_baselines3 import PPO

from car_controller_v2 import CarController


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


class PPOCameraAdapter:
    """
    PPO-specific camera adapter.

    PPO model expects:
        (3, 640, 250), uint8

    OAK-D captures landscape frame, then we resize to the exact PPO input.
    """

    def __init__(self):
        self.pipeline = None
        self.rgb_queue = None
        self.started = False
        self.frame_count = 0
        self.start_time = None

    def start(self):
        if self.started:
            return

        self.pipeline = dai.Pipeline()

        cam = self.pipeline.create(dai.node.Camera).build()

        rgb_output = cam.requestOutput(
            (CAPTURE_WIDTH, CAPTURE_HEIGHT),
            type=dai.ImgFrame.Type.BGR888p,
        )

        self.rgb_queue = rgb_output.createOutputQueue()

        self.pipeline.start()

        self.started = True
        self.frame_count = 0
        self.start_time = time.time()

        print("PPOCameraAdapter started.")
        print(f"Capture size: {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
        print(f"Model observation: (3, {MODEL_HEIGHT}, {MODEL_WIDTH}) uint8")

    def stop(self):
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
            except Exception:
                pass

        self.pipeline = None
        self.rgb_queue = None
        self.started = False

        print("PPOCameraAdapter stopped.")

    def get_latest_raw_frame(self, timeout_seconds=2.0):
        if not self.started:
            raise RuntimeError("Camera not started.")

        start = time.time()
        latest = None

        while time.time() - start < timeout_seconds:
            while self.rgb_queue.has():
                latest = self.rgb_queue.get()

            if latest is not None:
                self.frame_count += 1
                return latest.getCvFrame()

            time.sleep(0.001)

        raise TimeoutError("No OAK-D frame received.")

    def get_observation(self):
        frame_bgr = self.get_latest_raw_frame()

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        frame_resized = cv2.resize(
            frame_rgb,
            (MODEL_WIDTH, MODEL_HEIGHT),
            interpolation=cv2.INTER_AREA,
        )

        obs = np.transpose(frame_resized, (2, 0, 1)).astype(np.uint8)

        return obs

    def get_average_fps(self):
        if self.start_time is None:
            return 0.0

        elapsed = time.time() - self.start_time

        if elapsed <= 0:
            return 0.0

        return self.frame_count / elapsed


# =========================
# SETTINGS
# =========================

MODEL_PATH = "/home/na-33/best_model_ppo.zip"
ARDUINO_PORT = "/dev/ttyUSB0"

# PPO observation space:
# Box(0, 255, (3, 640, 250), uint8)
MODEL_HEIGHT = 640
MODEL_WIDTH = 250

# OAK-D capture before resizing
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 360

# Servo/ESC calibration
SERVO_LEFT_US = 1800
SERVO_CENTER_US = 1520
SERVO_RIGHT_US = 1200

ESC_STOP_US = 1498
ESC_MAX_SAFE_US = 1600

# Start with steering cap. You can increase with C.
max_model_steering = 0.95
STEERING_GAIN = 2.0

# PPO controls steering only, throttle is fixed manually.
fixed_throttle = 0.40
THROTTLE_STEP = 0.05
MAX_FIXED_THROTTLE = 0.60

# Short boost to overcome static friction at the start of each run
START_BOOST_THROTTLE = 0.55
START_BOOST_SECONDS = 0.60

# If PPO turns wrong direction, press I.
invert_steering = False

SMOOTH = False

# PPO camera/model is slower, around 6 FPS, so use 5 Hz control.
CONTROL_HZ = 5.0
CONTROL_DT = 1.0 / CONTROL_HZ

# Safety: every autonomous run stops automatically.
MAX_ARMED_SECONDS = 120.0


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def load_ppo_model(model_path):
    custom_objects = {
        "policy_kwargs": {
            "features_extractor_kwargs": {
                "features_dim": 128,
            },
            "net_arch": [64, 64],
            "normalize_images": True,
        },
        "lr_schedule": lambda _: 0.0,
        "clip_range": lambda _: 0.2,
    }

    return PPO.load(
        model_path,
        device="cpu",
        custom_objects=custom_objects,
    )


def main():
    global fixed_throttle
    global max_model_steering
    global invert_steering

    try:
        th.set_num_threads(1)
    except Exception:
        pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"real_ppo_track_test_{timestamp}.csv"

    print("\nLoading PPO model...")
    model = load_ppo_model(MODEL_PATH)
    print("PPO model loaded.")
    print(f"Observation space: {model.observation_space}")
    print(f"Action space: {model.action_space}")

    camera = PPOCameraAdapter()
    car = None
    log_file = None

    print("\nREAL PPO TRACK TEST V1")
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

            servo_left_us=SERVO_LEFT_US,
            servo_center_us=SERVO_CENTER_US,
            servo_right_us=SERVO_RIGHT_US,

            esc_stop_us=ESC_STOP_US,
            esc_max_safe_us=ESC_MAX_SAFE_US,

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

                obs = camera.get_observation()

                action, _ = model.predict(obs, deterministic=True)
                action = np.array(action).flatten()

                raw_steering = float(action[0])

                if invert_steering:
                    raw_steering = -raw_steering

                model_steering = clamp(
                    raw_steering * STEERING_GAIN,
                    -max_model_steering,
                    max_model_steering,
                )

                if armed:
                    sent_steering = model_steering

                    # Short boost at the beginning of each armed run.
                    # This replaces pushing the car by hand.
                    if armed_start_time is not None and (now - armed_start_time) < START_BOOST_SECONDS:
                        sent_throttle = max(fixed_throttle, START_BOOST_THROTTLE)
                    else:
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

                camera_fps = camera.get_average_fps()
                time_s = now - test_start_time

                logger.writerow([
                    f"{time_s:.3f}",
                    armed,
                    f"{raw_steering:.4f}",
                    f"{model_steering:.4f}",
                    f"{sent_steering:.4f}",
                    f"{sent_throttle:.4f}",
                    debug["sent_servo_us"],
                    debug["sent_esc_us"],
                    f"{max_model_steering:.2f}",
                    invert_steering,
                    f"{camera_fps:.2f}",
                ])
                log_file.flush()

                if now - last_print_time >= 0.30:
                    print(
                        f"armed={armed} | "
                        f"raw={raw_steering:.3f} | "
                        f"model_steer={model_steering:.3f} | "
                        f"sent_steer={sent_steering:.3f} | "
                        f"thr={sent_throttle:.2f} | "
                        f"servo={debug['sent_servo_us']} | "
                        f"esc={debug['sent_esc_us']} | "
                        f"max_steer={max_model_steering:.2f} | "
                        f"invert={invert_steering} | "
                        f"fps={camera_fps:.1f}"
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
