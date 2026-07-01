import time
import board
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

ESC_CHANNEL = 1

def set_pwm_us(channel, pulse_us):
    pulse_length_us = 1_000_000 / pca.frequency
    duty_cycle = int((pulse_us / pulse_length_us) * 65535)
    pca.channels[channel].duty_cycle = duty_cycle

try:
    print("LiPo must be disconnected.")
    print("Sending stable RC neutral 1500us.")
    
    # Send neutral for a while before ESC gets power
    set_pwm_us(ESC_CHANNEL, 1500)
    time.sleep(5)

    print("Now connect LiPo to ESC.")
    print("Keeping 1500us neutral for 30 seconds.")
    time.sleep(30)

    print("Done. Still neutral.")

finally:
    print("Returning to neutral.")
    set_pwm_us(ESC_CHANNEL, 1500)
    time.sleep(1)
    pca.deinit()

