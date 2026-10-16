/**
 * @file actuators.cpp
 * @brief Implementation of hardware actuators (LEDs, Servo, Buzzer).
 */

#include "actuators.h"

ActuatorManager::ActuatorManager()
    : _greenLedState(false),
      _redLedState(false),
      _buzzerState(false),
      _currentServoAngle(SERVO_ANGLE_CLOSED),
      _alarmRunning(false),
      _alarmStartTime(0),
      _alarmDurationMs(0) {}

void ActuatorManager::begin() {
    // Configure GPIO modes
    pinMode(PIN_GREEN_LED, OUTPUT);
    pinMode(PIN_RED_LED, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);

    // Initial safe states
    digitalWrite(PIN_GREEN_LED, LOW);
    digitalWrite(PIN_RED_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);

    // Attach Servo with ESP32 timers
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    _servo.setPeriodHertz(50); // Standard 50Hz servo PWM
    _servo.attach(PIN_SERVO, SERVO_MIN_US, SERVO_MAX_US);

    // Initialize to closed position (0 degrees)
    setServoAngle(SERVO_ANGLE_CLOSED);

    Serial.println("[ACTUATORS] Hardware subsystem initialized successfully.");
    Serial.printf("[ACTUATORS] Green LED (GPIO%d), Red LED (GPIO%d), Buzzer (GPIO%d), Servo (GPIO%d)\n",
                  PIN_GREEN_LED, PIN_RED_LED, PIN_BUZZER, PIN_SERVO);
}

void ActuatorManager::setGreenLed(bool state) {
    _greenLedState = state;
    digitalWrite(PIN_GREEN_LED, state ? HIGH : LOW);
    Serial.printf("[ACTUATION] Green LED (GPIO%d) -> %s\n", PIN_GREEN_LED, state ? "HIGH (ON)" : "LOW (OFF)");
}

void ActuatorManager::setRedLed(bool state) {
    _redLedState = state;
    digitalWrite(PIN_RED_LED, state ? HIGH : LOW);
    Serial.printf("[ACTUATION] Red LED (GPIO%d) -> %s\n", PIN_RED_LED, state ? "HIGH (ON)" : "LOW (OFF)");
}

void ActuatorManager::setServoAngle(int angle) {
    // Clamp to valid 0-180 range
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;

    _currentServoAngle = angle;
    _servo.write(angle);
    Serial.printf("[ACTUATION] Servo (GPIO%d) -> %d degrees\n", PIN_SERVO, angle);
}

void ActuatorManager::triggerAlarm(uint32_t durationMs) {
    // Start non-blocking alert pulse
    _alarmRunning = true;
    _alarmStartTime = millis();
    _alarmDurationMs = durationMs;

    // Activate Red LED and Buzzer
    setRedLed(true);
    _buzzerState = true;
    digitalWrite(PIN_BUZZER, HIGH);

    Serial.printf("[ACTUATION] Alarm Pulse Activated (Red LED + Active Buzzer) for %u ms\n", durationMs);
}

void ActuatorManager::update() {
    // Non-blocking timer check to shut off alarm when elapsed
    if (_alarmRunning) {
        if (millis() - _alarmStartTime >= _alarmDurationMs) {
            _alarmRunning = false;
            setRedLed(false);
            _buzzerState = false;
            digitalWrite(PIN_BUZZER, LOW);
            Serial.println("[ACTUATION] Alarm Pulse Complete -> Red LED & Buzzer Deactivated.");
        }
    }
}
