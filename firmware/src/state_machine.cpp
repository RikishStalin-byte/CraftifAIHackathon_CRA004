/**
 * @file state_machine.cpp
 * @brief Implementation of gesture command mapping to physical actuators.
 */

#include "state_machine.h"

StateMachine::StateMachine(ActuatorManager& actuators)
    : _actuators(actuators),
      _commandsReceived(0),
      _commandsExecuted(0),
      _lastGesture("NONE"),
      _lastCommandTimeMs(0),
      _lastExecutionLatencyMs(0) {}

GestureCommand StateMachine::parseGestureString(const String& str) {
    String upper = str;
    upper.trim();
    upper.toUpperCase();

    if (upper == "OPEN_HAND") return GestureCommand::OPEN_HAND;
    if (upper == "FIST") return GestureCommand::FIST;
    if (upper == "THUMBS_UP") return GestureCommand::THUMBS_UP;
    if (upper == "THUMBS_DOWN") return GestureCommand::THUMBS_DOWN;
    if (upper == "VICTORY") return GestureCommand::VICTORY;

    return GestureCommand::UNKNOWN;
}

const char* StateMachine::gestureToString(GestureCommand cmd) {
    switch (cmd) {
        case GestureCommand::OPEN_HAND:   return "OPEN_HAND";
        case GestureCommand::FIST:        return "FIST";
        case GestureCommand::THUMBS_UP:   return "THUMBS_UP";
        case GestureCommand::THUMBS_DOWN: return "THUMBS_DOWN";
        case GestureCommand::VICTORY:     return "VICTORY";
        default:                          return "UNKNOWN";
    }
}

bool StateMachine::handleGestureCommand(const String& gestureStr) {
    uint32_t startTime = millis();
    _commandsReceived++;

    GestureCommand cmd = parseGestureString(gestureStr);

    switch (cmd) {
        case GestureCommand::OPEN_HAND:
            // FR6: The ESP32 shall turn ON the green LED when an Open Hand gesture is received.
            _actuators.setGreenLed(true);
            break;

        case GestureCommand::FIST:
            // FR7: The ESP32 shall turn OFF the green LED when a Fist gesture is received.
            _actuators.setGreenLed(false);
            break;

        case GestureCommand::THUMBS_UP:
            // FR8: The ESP32 shall rotate a servo motor to 90 degrees when a Thumbs Up gesture is received.
            _actuators.setServoAngle(SERVO_ANGLE_OPEN);
            break;

        case GestureCommand::THUMBS_DOWN:
            // FR9: The ESP32 shall rotate the servo motor to 0 degrees when a Thumbs Down gesture is received.
            _actuators.setServoAngle(SERVO_ANGLE_CLOSED);
            break;

        case GestureCommand::VICTORY:
            // FR10: The ESP32 shall activate a red LED and buzzer when a Victory Sign gesture is received.
            _actuators.triggerAlarm(ALARM_PULSE_DURATION_MS);
            break;

        default:
            Serial.printf("[STATE_MACHINE WARNING] Unrecognized gesture command: '%s'\n", gestureStr.c_str());
            return false;
    }

    _commandsExecuted++;
    _lastGesture = gestureToString(cmd);
    _lastCommandTimeMs = millis();
    _lastExecutionLatencyMs = millis() - startTime;

    Serial.printf("[STATE_MACHINE] Executed '%s' in %u ms (Total Executed: %u)\n",
                  _lastGesture.c_str(), _lastExecutionLatencyMs, _commandsExecuted);
    return true;
}
