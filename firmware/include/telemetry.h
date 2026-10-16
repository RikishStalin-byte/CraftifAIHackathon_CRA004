/**
 * @file telemetry.h
 * @brief Telemetry subsystem gathering system health, actuator states, and command execution stats.
 * 
 * Implements FR11 and FR12.
 */

#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include "config.h"
#include "actuators.h"
#include "state_machine.h"
#include "mqtt_manager.h"

class TelemetryManager {
public:
    TelemetryManager(ActuatorManager& actuators, StateMachine& stateMachine, MqttManager& mqttManager);

    void begin();
    void publishIfDue();
    void forcePublish();

private:
    ActuatorManager& _actuators;
    StateMachine& _stateMachine;
    MqttManager& _mqttManager;

    uint32_t _lastPublishTime;

    void buildAndSendTelemetry();
};
