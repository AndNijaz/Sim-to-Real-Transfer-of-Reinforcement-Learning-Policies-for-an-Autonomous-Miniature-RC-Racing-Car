import time
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

SERVO_CHANNEL = 1

def set_pwm_us(channel, pulse_us):
    pulse_length_us = 1_000_000 / pca.frequency
    duty_cycle = int((pulse_us / pulse_length_us) * 65535)
    pca.channels[channel].duty_cycle = duty_cycle

try:
    print("Center")
    set_pwm_us(SERVO_CHANNEL, 1500)
    time.sleep(2)

    print("Small left")
    set_pwm_us(SERVO_CHANNEL, 1450)
    time.sleep(1)

    print("Center")
    set_pwm_us(SERVO_CHANNEL, 1500)
    time.sleep(1)

    print("Small right")
    set_pwm_us(SERVO_CHANNEL, 1550)
    time.sleep(1)

    print("Center")
    set_pwm_us(SERVO_CHANNEL, 1500)
    time.sleep(1)

finally:
    set_pwm_us(SERVO_CHANNEL, 1500)
    time.sleep(1)
    pca.deinit()
