import time
from car_controller import CarController

car = None

try:
    car = CarController(arduino_port="/dev/ttyUSB0")

    print("Center + stop")
    car.stop()
    time.sleep(2)

    print("Small left")
    car.drive(steering=-0.4, throttle=0.0)
    time.sleep(1)

    print("Small right")
    car.drive(steering=0.4, throttle=0.0)
    time.sleep(1)

    print("Center")
    car.drive(steering=0.0, throttle=0.0)
    time.sleep(1)

    print("Low throttle straight")
    car.drive(steering=0.0, throttle=0.3)
    time.sleep(1)

    print("Stop")
    car.stop()
    time.sleep(2)

finally:
    if car is not None:
        car.close()
