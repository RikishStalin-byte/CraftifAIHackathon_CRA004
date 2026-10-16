/**
 * @file mqtt_manager.cpp
 * @brief MQTT network connection and message parsing implementation.
 */

#include "mqtt_manager.h"

MqttManager* MqttManager::_instance = nullptr;

MqttManager::MqttManager(StateMachine& stateMachine)
    : _stateMachine(stateMachine),
      _mqttClient(_wifiClient),
      _lastReconnectAttempt(0) {
    _instance = this;
}

void MqttManager::begin() {
    _mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    _mqttClient.setCallback(MqttManager::mqttCallbackTrampoline);
    _mqttClient.setBufferSize(768); // Allow large telemetry and command JSON payloads

    connectWiFi();
    connectMqtt();
}

void MqttManager::connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.printf("[WIFI] Connecting to SSID: '%s'...\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    uint32_t startAttemptTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 8000) {
        delay(300);
        Serial.print(".");
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[WIFI] Connected! IP Address: %s (RSSI: %d dBm)\n",
                      WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        Serial.println("[WIFI WARNING] WiFi connection not established. Will retry in loop.");
    }
}

bool MqttManager::connectMqtt() {
    if (_mqttClient.connected()) return true;
    if (WiFi.status() != WL_CONNECTED) return false;

    Serial.printf("[MQTT] Connecting to broker %s:%d as '%s'...\n",
                  MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_CLIENT_ID);

    // Prepare Last Will and Testament (LWT)
    StaticJsonDocument<128> lwtDoc;
    lwtDoc["device_id"] = DEVICE_HARDWARE_ID;
    lwtDoc["status"] = "OFFLINE";
    char lwtPayload[128];
    serializeJson(lwtDoc, lwtPayload);

    // Connect with LWT
    if (_mqttClient.connect(MQTT_CLIENT_ID, TOPIC_DEVICE_STATUS, 1, true, lwtPayload)) {
        Serial.println("[MQTT] Connected successfully!");

        // Publish ONLINE status (retained)
        StaticJsonDocument<256> statusDoc;
        statusDoc["device_id"] = DEVICE_HARDWARE_ID;
        statusDoc["status"] = "ONLINE";
        statusDoc["firmware_version"] = FIRMWARE_VERSION;
        statusDoc["ip_address"] = WiFi.localIP().toString();
        statusDoc["mac_address"] = WiFi.macAddress();
        char statusPayload[256];
        serializeJson(statusDoc, statusPayload);
        _mqttClient.publish(TOPIC_DEVICE_STATUS, statusPayload, true);

        // Subscribe to gesture commands (FR5)
        _mqttClient.subscribe(TOPIC_GESTURE_CMD, 1);
        Serial.printf("[MQTT] Subscribed to command topic: '%s'\n", TOPIC_GESTURE_CMD);
        return true;
    } else {
        Serial.printf("[MQTT ERROR] Connection failed, rc=%d. Will retry.\n", _mqttClient.state());
        return false;
    }
}

void MqttManager::loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    if (!_mqttClient.connected()) {
        uint32_t now = millis();
        if (now - _lastReconnectAttempt > 5000) {
            _lastReconnectAttempt = now;
            connectMqtt();
        }
    } else {
        _mqttClient.loop();
    }
}

bool MqttManager::isConnected() {
    return _mqttClient.connected();
}

bool MqttManager::publish(const char* topic, const char* payload, bool retained) {
    if (!_mqttClient.connected()) return false;
    return _mqttClient.publish(topic, payload, retained);
}

void MqttManager::mqttCallbackTrampoline(char* topic, byte* payload, unsigned int length) {
    if (_instance != nullptr) {
        _instance->onMessageReceived(topic, payload, length);
    }
}

void MqttManager::onMessageReceived(char* topic, byte* payload, unsigned int length) {
    // Zero-terminate payload buffer
    char jsonBuffer[length + 1];
    memcpy(jsonBuffer, payload, length);
    jsonBuffer[length] = '\0';

    Serial.printf("[MQTT RECV] Topic: %s | Payload: %s\n", topic, jsonBuffer);

    if (strcmp(topic, TOPIC_GESTURE_CMD) == 0) {
        StaticJsonDocument<256> doc;
        DeserializationError err = deserializeJson(doc, jsonBuffer);
        if (err) {
            Serial.printf("[MQTT ERROR] Failed to parse command JSON: %s\n", err.c_str());
            return;
        }

        const char* gesture = doc["gesture"];
        if (gesture != nullptr) {
            _stateMachine.handleGestureCommand(String(gesture));
        } else {
            Serial.println("[MQTT WARNING] Missing 'gesture' field in command payload.");
        }
    }
}
