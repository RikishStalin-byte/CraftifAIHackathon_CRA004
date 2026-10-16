/**
 * @file state_machine.h
 * @brief Gesture Command State Machine mapping discrete gestures to hardware actions.
 * 
 * Implements FR6, FR7, FR8, FR9, FR10.
 */

#pragma once

#include <Arduino.h>
#include "actuators.h"

enum class GestureCommand {
    UNKNOWN = 0,
    OPEN_HAND,      // FR6: Turn ON Green LED
    FIST,           // FR7: Turn OFF Green LED
    THUMBS_UP,      // FR8: Rotate Servo to 90 deg (Open)
    THUMBS_DOWN,    // FR9: Rotate Servo to 0 deg (Closed)
    VICTORY         // FR10: Activate Red LED & Buzzer Alarm
};

class StateMachine {
public:
    explicit StateMachine(ActuatorManager& actuators);

    /**
     * @brief Parses and executes an incoming gesture command string.
     * @param gestureStr Name of gesture (e.g. "THUMBS_UP")
     * @return true if command was recognized and executed, false otherwise.
     */
    bool handleGestureCommand(const String& gestureStr);

    // Metrics & Telemetry
    uint32_t getCommandsReceived() const { return _commandsReceived; }
    uint32_t getCommandsExecuted() const { return _commandsExecuted; }
    String getLastGesture() const { return _lastGesture; }
    uint32_t getLastCommandTimeMs() const { return _lastCommandTimeMs; }
    uint32_t getLastExecutionLatencyMs() const { return _lastExecutionLatencyMs; }

    static GestureCommand parseGestureString(const String& str);
    static const char* gestureToString(GestureCommand cmd);

private:
    ActuatorManager& _actuators;

    uint32_t _commandsReceived;
    uint32_t _commandsExecuted;
    String _lastGesture;
    uint32_t _lastCommandTimeMs;
    uint32_t _lastExecutionLatencyMs;
};
