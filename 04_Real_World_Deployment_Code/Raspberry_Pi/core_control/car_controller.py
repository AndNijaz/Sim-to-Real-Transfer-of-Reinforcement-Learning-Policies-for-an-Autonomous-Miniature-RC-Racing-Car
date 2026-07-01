import time
import serial


class CarController:
    """
    Safe high-level vehicle controller.

    Raspberry Pi sends normalized steering/throttle commands.
    Arduino converts them into real PWM microsecond values for servo and ESC.

    Safety features:
    - startup stop command
    - hard throttle limit
    - smooth steering limiting
    - smooth throttle limiting
    - emergency stop method
    """

    def __init__(
        self,
        arduino_port="/dev/ttyUSB0",
        baud_rate=9600,

        # Servo calibration
        servo_left_us=1800,      # inverted so keyboard 'a' goes left if needed
        servo_center_us=1520,
        servo_right_us=1200,

        # ESC calibration
        esc_stop_us=1498,
        esc_max_safe_us=1600,

        # Normalized safety limits
        max_throttle=0.45,

        # Smoothing limits per command update
        max_steering_delta=0.12,
        max_throttle_delta=0.06,
    ):
        self.arduino_port = arduino_port
        self.baud_rate = baud_rate

        self.servo_left_us = servo_left_us
        self.servo_center_us = servo_center_us
        self.servo_right_us = servo_right_us

        self.esc_stop_us = esc_stop_us
        self.esc_max_safe_us = esc_max_safe_us

        self.max_throttle = max_throttle

        self.max_steering_delta = max_steering_delta
        self.max_throttle_delta = max_throttle_delta

        self.current_steering = 0.0
        self.current_throttle = 0.0

        print(f"Connecting to Arduino on {arduino_port}...")
        self.arduino = serial.Serial(arduino_port, baud_rate, timeout=1)

        # Arduino usually resets when the serial connection opens.
        time.sleep(3)

        # Startup safety command.
        print("Sending startup STOP command...")
        self.emergency_stop()
        time.sleep(1)

        print("CarController ready.")

    def clamp(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def map_range(self, value, in_min, in_max, out_min, out_max):
        value = self.clamp(value, in_min, in_max)
        return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

    def limit_delta(self, target, current, max_delta):
        difference = target - current

        if difference > max_delta:
            return current + max_delta

        if difference < -max_delta:
            return current - max_delta

        return target

    def steering_to_us(self, steering):
        """
        steering:
        -1.0 = left
         0.0 = center
         1.0 = right
        """
        steering = self.clamp(steering, -1.0, 1.0)

        if steering < 0:
            return int(self.map_range(
                steering,
                -1.0,
                0.0,
                self.servo_left_us,
                self.servo_center_us,
            ))

        return int(self.map_range(
            steering,
            0.0,
            1.0,
            self.servo_center_us,
            self.servo_right_us,
        ))

    def throttle_to_us(self, throttle):
        """
        throttle:
        0.0 = stop
        1.0 = internal max, but still limited by max_throttle
        """
        throttle = self.clamp(throttle, 0.0, self.max_throttle)

        return int(self.map_range(
            throttle,
            0.0,
            1.0,
            self.esc_stop_us,
            self.esc_max_safe_us,
        ))

    def send_raw(self, servo_us, esc_us, read_response=True):
        command = f"S {servo_us} E {esc_us}\n"
        self.arduino.write(command.encode("utf-8"))

        time.sleep(0.015)

        if read_response:
            while self.arduino.in_waiting:
                response = self.arduino.readline().decode("utf-8", errors="ignore").strip()
                if response:
                    print("Arduino:", response)

    def drive(self, steering, throttle, smooth=True):
        """
        Main driving method.

        If smooth=True, sudden jumps are limited.
        If smooth=False, command is applied immediately.
        """
        steering = self.clamp(steering, -1.0, 1.0)
        throttle = self.clamp(throttle, 0.0, self.max_throttle)

        if smooth:
            steering = self.limit_delta(
                steering,
                self.current_steering,
                self.max_steering_delta,
            )
            throttle = self.limit_delta(
                throttle,
                self.current_throttle,
                self.max_throttle_delta,
            )

        self.current_steering = steering
        self.current_throttle = throttle

        servo_us = self.steering_to_us(self.current_steering)
        esc_us = self.throttle_to_us(self.current_throttle)

        self.send_raw(servo_us, esc_us)

    def stop(self):
        """
        Soft stop: throttle to zero, steering stays current.
        """
        self.current_throttle = 0.0
        servo_us = self.steering_to_us(self.current_steering)
        self.send_raw(servo_us, self.esc_stop_us)

    def center_and_stop(self):
        """
        Safe stop with centered steering.
        """
        self.current_steering = 0.0
        self.current_throttle = 0.0
        self.send_raw(self.servo_center_us, self.esc_stop_us)

    def emergency_stop(self):
        """
        Immediate hard stop. No smoothing.
        """
        self.current_steering = 0.0
        self.current_throttle = 0.0

        for _ in range(3):
            self.send_raw(self.servo_center_us, self.esc_stop_us, read_response=False)
            time.sleep(0.05)

    def close(self):
        self.emergency_stop()
        time.sleep(0.5)
        self.arduino.close()
        print("CarController closed.")
