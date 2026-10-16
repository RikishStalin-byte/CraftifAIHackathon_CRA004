/**
 * @file telemetry.cpp
 * @brief Telemetry serialization and periodic dispatch implementation.
 */

#include "telemetry.h"

TelemetryManager::TelemetryManager(ActuatorManager& actuators, StateMachine& stateMachine, MqttManager& mqttManager)
    : _actuators(actuators),
      _stateMachine(stateMachine),
      _mqttManager(mqttManager),
      _lastPublishTime(0) {}

void TelemetryManager::begin() {
    _lastPublishTime = millis();
    Serial.println("[TELEMETRY] Subsystem initialized.");
}

void TelemetryManager::publishIfDue() {
    uint32_t now = millis();
    if (now - _lastPublishTime >= TELEMETRY_INTERVAL_MS) {
        _lastPublishTime = now;
        buildAndSendTelemetry();
    }
}

void TelemetryManager::forcePublish() {
    buildAndSendTelemetry();
}

void TelemetryManager::buildAndSendTelemetry() {
    if (!_mqttManager.isConnected()) return;

    StaticJsonDocument<512> doc;

    // Device Metadata
    doc["device_id"] = DEVICE_HARDWARE_ID;
    doc["uptime_ms"] = millis();
    doc["wifi_rssi"] = WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0;
    doc["free_heap_bytes"] = ESP.getFreeHeap();

    // Actuator States
    JsonObject actObj = doc.createNestedObject("actuators");
    actObj["green_led"] = _actuators.isGreenLedOn();
    actObj["red_led"] = _actuators.isRedLedOn();
    actObj["servo_angle"] = _actuators.getServoAngle();
    actObj["buzzer_active"] = _actuators.isBuzzerActive();

    // Metrics & Performance
    JsonObject metObj = doc.createNestedObject("metrics");
    metObj["commands_received"] = _stateMachine.getCommandsReceived();
    metObj["commands_executed"] = _stateMachine.getCommandsExecuted();
    metObj["last_gesture"] = _stateMachine.getLastGesture();
    metObj["last_command_time_ms"] = _stateMachine.getLastCommandTimeMs();
    metObj["execution_latency_ms"] = _stateMachine.getLastExecutionLatencyMs();

    char payload[512];
    serializeJson(doc, payload);

    _mqttManager.publish(TOPIC_TELEMETRY, payload, false);
}
