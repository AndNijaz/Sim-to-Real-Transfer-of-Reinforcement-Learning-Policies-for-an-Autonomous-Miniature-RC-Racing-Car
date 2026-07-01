import sys
import termios
import tty

from car_controller_v2 import CarController


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


ARDUINO_PORT = "/dev/ttyUSB0"

# Start safer, then tune live.
max_steering = 0.45

MAX_THROTTLE = 1.00
THROTTLE_STEP = 0.05

# Keep instant for manual control.
SMOOTH = False

car = None

steering = 0.0
throttle = 0.0

try:
    car = CarController(
        arduino_port=ARDUINO_PORT,

        servo_left_us=1800,
        servo_center_us=1520,
        servo_right_us=1200,

        esc_stop_us=1498,
        esc_max_safe_us=1600,

        max_throttle=0.45,

        max_steering_delta=0.35,
        max_throttle_delta=0.08,
    )

    print("\nManual drive TUNABLE V2 ready.")
    print("Controls:")
    print("  w      = increase throttle")
    print("  s      = stop throttle")
    print("  a      = steer left using current steering limit")
    print("  d      = steer right using current steering limit")
    print("  x      = center steering")
    print("  z      = decrease steering limit")
    print("  c      = increase steering limit")
    print("  f      = full steering test mode, max_steering = 1.00")
    print("  r      = reset safe steering, max_steering = 0.45")
    print("  space  = emergency stop + center")
    print("  q      = quit")
    print("")
    print("IMPORTANT:")
    print("  If max_steering is 0.45, the servo will NOT go full lock.")
    print("  Press f only while wheels are in the air or at very low speed.")
    print("")

    car.drive(steering, throttle, smooth=False)

    while True:
        key = get_key()

        if key == "w":
            throttle = clamp(throttle + THROTTLE_STEP, 0.0, MAX_THROTTLE)

        elif key == "s":
            throttle = 0.0

        elif key == "a":
            steering = -max_steering

        elif key == "d":
            steering = max_steering

        elif key == "x":
            steering = 0.0

        elif key == "z":
            max_steering = clamp(max_steering - 0.05, 0.10, 1.00)
            print(f"\nmax_steering decreased to {max_steering:.2f}\n")
            continue

        elif key == "c":
            max_steering = clamp(max_steering + 0.05, 0.10, 1.00)
            print(f"\nmax_steering increased to {max_steering:.2f}\n")
            continue

        elif key == "f":
            max_steering = 1.00
            print("\nFULL STEERING MODE: max_steering = 1.00\n")
            continue

        elif key == "r":
            max_steering = 0.45
            print("\nSAFE STEERING RESET: max_steering = 0.45\n")
            continue

        elif key == " ":
            steering = 0.0
            throttle = 0.0
            car.center_and_stop()
            print("\nEMERGENCY STOP + CENTER\n")
            continue

        elif key == "q":
            break

        elif key == "\x03":
            break

        else:
            continue

        debug = car.drive(steering, throttle, smooth=SMOOTH)

        print(
            f"key={repr(key)} | "
            f"max_steering={max_steering:.2f} | "
            f"steering={steering:.2f} | "
            f"throttle={throttle:.2f} | "
            f"servo={debug['sent_servo_us']} | "
            f"esc={debug['sent_esc_us']} | "
            f"smooth={SMOOTH}"
        )

finally:
    if car is not None:
        print("\nStopping car.")
        car.close()

