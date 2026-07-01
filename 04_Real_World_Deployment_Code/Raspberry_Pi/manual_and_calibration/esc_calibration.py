import time
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

ESC_CHANNEL = 0

def set_pwm_us(channel, pulse_us):
    pulse_length_us = 1_000_000 / pca.frequency
    duty_cycle = int((pulse_us / pulse_length_us) * 65535)
    pca.channels[channel].duty_cycle = duty_cycle

try:
    print("LiPo must be disconnected.")
    print("Sending MAX throttle 2000us.")
    set_pwm_us(ESC_CHANNEL, 2000)
    time.sleep(3)

    print("Now connect LiPo to ESC.")
    print("Wait for ESC calibration beeps, then it will switch to MIN.")
    time.sleep(6)

    print("Sending MIN throttle 1000us.")
    set_pwm_us(ESC_CHANNEL, 1000)
    time.sleep(8)

    print("Calibration attempt finished. Staying at MIN 1000us.")
    set_pwm_us(ESC_CHANNEL, 1000)
    time.sleep(3)

finally:
    print("Returning to safe minimum 1000us.")
    set_pwm_us(ESC_CHANNEL, 1000)
    time.sleep(1)
    pca.deinit()
