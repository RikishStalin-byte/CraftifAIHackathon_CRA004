/**
 * @file mqtt_manager.h
 * @brief MQTT Network and Message Routing Manager for ESP32.
 * 
 * Implements FR4, FR5, FR11.
 */

#pragma once

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "state_machine.h"

class MqttManager {
public:
    MqttManager(StateMachine& stateMachine);

    void begin();
    void loop();

    bool isConnected();
    bool publish(const char* topic, const char* payload, bool retained = false);

private:
    StateMachine& _stateMachine;
    WiFiClient _wifiClient;
    PubSubClient _mqttClient;

    uint32_t _lastReconnectAttempt;

    void connectWiFi();
    bool connectMqtt();
    void onMessageReceived(char* topic, byte* payload, unsigned int length);

    // Static trampoline for PubSubClient callback
    static void mqttCallbackTrampoline(char* topic, byte* payload, unsigned int length);
    static MqttManager* _instance;
};
