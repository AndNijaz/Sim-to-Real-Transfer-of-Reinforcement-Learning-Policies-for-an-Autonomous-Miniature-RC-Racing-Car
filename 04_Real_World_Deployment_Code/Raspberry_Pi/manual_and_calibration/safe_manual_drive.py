import sys
import termios
import tty
import time
from car_controller import CarController


def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return key


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


car = None

steering = 0.0
throttle = 0.0

STEERING_STEP = 0.60
THROTTLE_STEP = 0.05

# This is an extra manual layer limit.
# The controller also has its own internal max_throttle.
MAX_THROTTLE = 0.45

try:
    car = CarController(
        arduino_port="/dev/ttyUSB0",
        max_throttle=MAX_THROTTLE,
        max_steering_delta=0.15,
        max_throttle_delta=0.06,
    )

    print("\nSafe manual drive ready.")
    print("Controls:")
    print("  w      = increase throttle")
    print("  s      = throttle stop")
    print("  a      = steer left")
    print("  d      = steer right")
    print("  x      = center steering")
    print("  SPACE  = EMERGENCY STOP + center")
    print("  q      = quit")
    print("  CTRL+C = emergency stop")
    print("\nStart slowly. Press SPACE anytime for emergency stop.\n")

    car.center_and_stop()

    while True:
        key = get_key()

        if key == "w":
            throttle = clamp(throttle + THROTTLE_STEP, 0.0, MAX_THROTTLE)

        elif key == "s":
            throttle = 0.0
            car.stop()
            print(f"steering={steering:.2f}, throttle={throttle:.2f} | SOFT STOP")
            continue

        elif key == "a":
            steering = clamp(steering - STEERING_STEP, -1.0, 1.0)

        elif key == "d":
            steering = clamp(steering + STEERING_STEP, -1.0, 1.0)

        elif key == "x":
            steering = 0.0

        elif key == " ":
            steering = 0.0
            throttle = 0.0
            car.emergency_stop()
            print("EMERGENCY STOP")
            continue

        elif key == "q":
            break

        elif key == "\x03":  # CTRL+C
            break

        car.drive(steering, throttle, smooth=False)
        print(f"steering={steering:.2f}, throttle={throttle:.2f}")

finally:
    if car is not None:
        print("\nFinal emergency stop.")
        car.close()
