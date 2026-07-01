import time
import serial

ARDUINO_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600

SERVO_CENTER_US = 1500
SERVO_LEFT_US = 1450
SERVO_RIGHT_US = 1550

ESC_STOP_US = 1498
ESC_LOW_US = 1530
ESC_MED_US = 1560


def send_command(arduino, servo_us, esc_us):
    command = f"S {servo_us} E {esc_us}\n"
    arduino.write(command.encode("utf-8"))
    print("Sent:", command.strip())
    time.sleep(0.2)

    while arduino.in_waiting:
        print("Arduino:", arduino.readline().decode(errors="ignore").strip())


arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
time.sleep(3)

try:
    print("Center + stop")
    send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)

    print("Now connect LiPo if not connected.")
    time.sleep(8)

    print("Small left")
    send_command(arduino, SERVO_LEFT_US, ESC_STOP_US)
    time.sleep(1)

    print("Small right")
    send_command(arduino, SERVO_RIGHT_US, ESC_STOP_US)
    time.sleep(1)

    print("Center")
    send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)
    time.sleep(1)

    print("Low forward straight")
    send_command(arduino, SERVO_CENTER_US, ESC_LOW_US)
    time.sleep(1)

    print("Stop")
    send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)
    time.sleep(2)

finally:
    send_command(arduino, SERVO_CENTER_US, ESC_STOP_US)
    arduino.close()

