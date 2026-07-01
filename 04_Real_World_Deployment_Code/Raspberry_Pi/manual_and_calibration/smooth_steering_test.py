import time
import serial

ARDUINO_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600

# Servo calibration values
SERVO_LEFT_US = 1200
SERVO_CENTER_US = 1520
SERVO_RIGHT_US = 1800

# ESC safe stop value
ESC_STOP_US = 1498


def send_command(arduino, servo_us, esc_us=ESC_STOP_US):
    command = f"S {servo_us} E {esc_us}\n"
    arduino.write(command.encode("utf-8"))
    print(command.strip())

    # Read Arduino response if available
    time.sleep(0.02)
    while arduino.in_waiting:
        response = arduino.readline().decode("utf-8", errors="ignore").strip()
        if response:
            print("Arduino:", response)


def smooth_move(arduino, start_us, end_us, step=10, delay=0.015):
    """
    Smoothly moves the steering servo from start_us to end_us.
    Bigger step and smaller delay = faster movement.
    """
    if start_us < end_us:
        values = range(start_us, end_us + 1, step)
    else:
        values = range(start_us, end_us - 1, -step)

    for value in values:
        send_command(arduino, value, ESC_STOP_US)
        time.sleep(delay)


def main():
    print("Connecting to Arduino...")
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)

    # Arduino resets when serial opens
    time.sleep(3)

    try:
        print("Centering steering.")
        send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)
        time.sleep(2)

        print("Starting smooth steering loop.")
        print("Press CTRL + C to stop.")

        while True:
            print("Smooth left")
            smooth_move(
                arduino,
                SERVO_CENTER_US,
                SERVO_LEFT_US,
                step=10,
                delay=0.015
            )
            time.sleep(0.4)

            print("Back to center")
            smooth_move(
                arduino,
                SERVO_LEFT_US,
                SERVO_CENTER_US,
                step=10,
                delay=0.015
            )
            time.sleep(0.4)

            print("Smooth right")
            smooth_move(
                arduino,
                SERVO_CENTER_US,
                SERVO_RIGHT_US,
                step=10,
                delay=0.015
            )
            time.sleep(0.4)

            print("Back to center")
            smooth_move(
                arduino,
                SERVO_RIGHT_US,
                SERVO_CENTER_US,
                step=10,
                delay=0.015
            )
            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\nStopping test.")

    finally:
        print("Returning to center and ESC stop.")
        send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)
        time.sleep(1)
        arduino.close()
        print("Finished.")


if __name__ == "__main__":
    main()
