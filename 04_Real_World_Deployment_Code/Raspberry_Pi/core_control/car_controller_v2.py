import time
import re
import serial


class CarController:
    """
    Safe high-level vehicle controller with debugging support.

    Raspberry Pi sends normalized steering/throttle commands.
    Arduino converts them into real PWM microsecond values for servo and ESC.

    steering:
        -1.0 = left
         0.0 = center
         1.0 = right

    throttle:
         0.0 = stop
         1.0 = max internal command, still limited by max_throttle
    """

    def __init__(
        self,
        arduino_port="/dev/ttyUSB0",
        baud_rate=9600,

        # Servo calibration
        servo_left_us=1800,
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

    def parse_arduino_ok(self, response):
        """
        Parses Arduino response like:
        OK servo=1520 esc=1498
        """
        match = re.search(r"OK\s+servo=(\d+)\s+esc=(\d+)", response)

        if not match:
            return None, None

        return int(match.group(1)), int(match.group(2))

    def send_raw(self, servo_us, esc_us, read_response=True):
        """
        Sends raw PWM values to Arduino.

        Returns:
            responses: list of raw response strings
            arduino_servo_us: last parsed servo value, if available
            arduino_esc_us: last parsed esc value, if available
        """
        command = f"S {servo_us} E {esc_us}\n"
        self.arduino.write(command.encode("utf-8"))

        # Small wait so Arduino has time to respond.
        time.sleep(0.015)

        responses = []
        arduino_servo_us = None
        arduino_esc_us = None

        if read_response:
            while self.arduino.in_waiting:
                response = self.arduino.readline().decode("utf-8", errors="ignore").strip()

                if response:
                    responses.append(response)
                    parsed_servo, parsed_esc = self.parse_arduino_ok(response)

                    if parsed_servo is not None:
                        arduino_servo_us = parsed_servo
                        arduino_esc_us = parsed_esc

        return {
            "command": command.strip(),
            "responses": responses,
            "arduino_servo_us": arduino_servo_us,
            "arduino_esc_us": arduino_esc_us,
        }

    def drive(self, steering, throttle, smooth=True, print_arduino=True):
        """
        Main driving method.

        If smooth=True, sudden jumps are limited.
        If smooth=False, command is applied immediately.

        Returns debug info dictionary.
        """
        requested_steering = self.clamp(steering, -1.0, 1.0)
        requested_throttle = self.clamp(throttle, 0.0, self.max_throttle)

        target_servo_us = self.steering_to_us(requested_steering)
        target_esc_us = self.throttle_to_us(requested_throttle)

        applied_steering = requested_steering
        applied_throttle = requested_throttle

        if smooth:
            applied_steering = self.limit_delta(
                requested_steering,
                self.current_steering,
                self.max_steering_delta,
            )

            applied_throttle = self.limit_delta(
                requested_throttle,
                self.current_throttle,
                self.max_throttle_delta,
            )

        self.current_steering = applied_steering
        self.current_throttle = applied_throttle

        sent_servo_us = self.steering_to_us(self.current_steering)
        sent_esc_us = self.throttle_to_us(self.current_throttle)

        raw_result = self.send_raw(sent_servo_us, sent_esc_us, read_response=True)

        if print_arduino:
            for response in raw_result["responses"]:
                print("Arduino:", response)

        debug = {
            "timestamp": time.time(),

            "smooth": smooth,

            "requested_steering": requested_steering,
            "requested_throttle": requested_throttle,

            "applied_steering": applied_steering,
            "applied_throttle": applied_throttle,

            "target_servo_us": target_servo_us,
            "target_esc_us": target_esc_us,

            "sent_servo_us": sent_servo_us,
            "sent_esc_us": sent_esc_us,

            "arduino_servo_us": raw_result["arduino_servo_us"],
            "arduino_esc_us": raw_result["arduino_esc_us"],

            "arduino_command": raw_result["command"],
            "arduino_responses": " | ".join(raw_result["responses"]),
        }

        return debug

    def stop(self, smooth=False):
        """
        Stop throttle. Steering stays current.
        """
        return self.drive(
            steering=self.current_steering,
            throttle=0.0,
            smooth=smooth,
        )

    def center_and_stop(self):
        """
        Safe stop with centered steering.
        """
        self.current_steering = 0.0
        self.current_throttle = 0.0

        raw_result = self.send_raw(self.servo_center_us, self.esc_stop_us, read_response=True)

        for response in raw_result["responses"]:
            print("Arduino:", response)

        return raw_result

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

