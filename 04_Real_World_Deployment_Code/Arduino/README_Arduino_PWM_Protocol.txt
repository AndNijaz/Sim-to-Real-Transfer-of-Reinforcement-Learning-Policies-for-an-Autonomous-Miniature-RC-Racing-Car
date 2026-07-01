Actuator control setup:
Raspberry Pi sends serial commands to Arduino.
Arduino generates PWM for steering servo and ESC.

Arduino pins:
D9  = ESC signal
D10 = steering servo signal
GND = shared ground

Steering:
center = 1520 µs
left/right safe range = 1200–1800 µs

ESC:
stop/arm = 1498 µs
tested safe throttle range ≈ 1498–1600 µs
manual drive currently limited by software max throttle