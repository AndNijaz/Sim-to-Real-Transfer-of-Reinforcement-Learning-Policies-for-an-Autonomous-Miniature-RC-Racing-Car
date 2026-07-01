import time
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

ESC_CHANNEL = 1

# Values measured from your receiver CH2
ARM_BRAKE_US = 1490
NEUTRAL_US = 1425
LOW_FORWARD_US = 1410
MEDIUM_FORWARD_US = 1390
FULL_FORWARD_US = 1355  # Do not use this yet in testing

def set_pwm_us(channel, pulse_us):
    pulse_length_us = 1_000_000 / pca.frequency
    duty_cycle = int((pulse_us / pulse_length_us) * 65535)
    pca.channels[channel].duty_cycle = duty_cycle

try:
    print("LiPo must be disconnected now.")
    print(f"Sending ARM/BRAKE signal: {ARM_BRAKE_US} us")
    set_pwm_us(ESC_CHANNEL, ARM_BRAKE_US)

    print("Now connect LiPo to ESC.")
    print("Holding arm/brake signal for 8 seconds...")
    time.sleep(8)

    print(f"Switching to NEUTRAL: {NEUTRAL_US} us")
    set_pwm_us(ESC_CHANNEL, NEUTRAL_US)
    time.sleep(5)

    print(f"Trying VERY LOW forward throttle: {LOW_FORWARD_US} us")
    set_pwm_us(ESC_CHANNEL, LOW_FORWARD_US)
    time.sleep(1)

    print("Back to neutral")
    set_pwm_us(ESC_CHANNEL, NEUTRAL_US)
    time.sleep(3)

    print(f"Trying slightly stronger forward throttle: {MEDIUM_FORWARD_US} us")
    set_pwm_us(ESC_CHANNEL, MEDIUM_FORWARD_US)
    time.sleep(1)

    print("Back to neutral")
    set_pwm_us(ESC_CHANNEL, NEUTRAL_US)
    time.sleep(3)

finally:
    print("Final neutral")
    set_pwm_us(ESC_CHANNEL, NEUTRAL_US)
    time.sleep(1)
    pca.deinit()
