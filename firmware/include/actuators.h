/**
 * @file actuators.h
 * @brief Actuator subsystem interface managing LEDs, Servo, and Buzzer.
 */

#pragma once

#include <Arduino.h>
#include <ESP32Servo.h>
#include "config.h"

class ActuatorManager {
public:
    ActuatorManager();

    /**
     * @brief Configures GPIO pin modes, PWM timer channels, and attaches servo.
     */
    void begin();

    /**
     * @brief Periodic non-blocking update loop for alarm pulse timings.
     */
    void update();

    // Actuator Controls
    void setGreenLed(bool state);
    void setRedLed(bool state);
    void setServoAngle(int angle);
    void triggerAlarm(uint32_t durationMs = ALARM_PULSE_DURATION_MS);

    // State Accessors (for Telemetry & Status Reporting)
    bool isGreenLedOn() const { return _greenLedState; }
    bool isRedLedOn() const { return _redLedState; }
    int getServoAngle() const { return _currentServoAngle; }
    bool isBuzzerActive() const { return _buzzerState; }

private:
    bool _greenLedState;
    bool _redLedState;
    bool _buzzerState;
    int _currentServoAngle;

    Servo _servo;

    // Non-blocking alarm timing
    bool _alarmRunning;
    uint32_t _alarmStartTime;
    uint32_t _alarmDurationMs;
};
