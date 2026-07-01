#include <Servo.h>

Servo esc;
Servo steering;

const int ESC_PIN = 9;
const int SERVO_PIN = 10;

// ESC values
const int ESC_STOP_US = 1498;
const int ESC_MIN_US = 1498;
const int ESC_MAX_SAFE_US = 1560;

// Servo values
const int SERVO_LEFT_US = 1200;
const int SERVO_CENTER_US = 1520;
const int SERVO_RIGHT_US = 1800;

int currentEscPulse = ESC_STOP_US;
int currentServoPulse = SERVO_CENTER_US;

void setup() {
  Serial.begin(9600);

  esc.attach(ESC_PIN);
  steering.attach(SERVO_PIN);

  esc.writeMicroseconds(ESC_STOP_US);
  steering.writeMicroseconds(SERVO_CENTER_US);

  delay(3000);

  Serial.println("Arduino actuator controller ready.");
  Serial.println("Format: S <servo_us> E <esc_us>");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    int sIndex = command.indexOf('S');
    int eIndex = command.indexOf('E');

    if (sIndex != -1 && eIndex != -1) {
      int servoValue = command.substring(sIndex + 1, eIndex).toInt();
      int escValue = command.substring(eIndex + 1).toInt();

      if (servoValue >= SERVO_LEFT_US && servoValue <= SERVO_RIGHT_US &&
          escValue >= ESC_MIN_US && escValue <= ESC_MAX_SAFE_US) {

        currentServoPulse = servoValue;
        currentEscPulse = escValue;

        steering.writeMicroseconds(currentServoPulse);
        esc.writeMicroseconds(currentEscPulse);

        Serial.print("OK servo=");
        Serial.print(currentServoPulse);
        Serial.print(" esc=");
        Serial.println(currentEscPulse);
      } else {
        Serial.println("Invalid command range.");
      }
    } else {
      Serial.println("Invalid format.");
    }
  }

  steering.writeMicroseconds(currentServoPulse);
  esc.writeMicroseconds(currentEscPulse);

  delay(20);
}
