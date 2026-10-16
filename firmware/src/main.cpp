/**
 * @file main.cpp
 * @brief AirControl AI - Production ESP32 Firmware Entry Point
 * 
 * Generated following FirmGen best practices for Physical AI hardware actuation.
 * Aligned with Physical AI "See -> Decide -> Act" paradigm.
 */

#include <Arduino.h>
#include "config.h"
#include "actuators.h"
#include "state_machine.h"
#include "mqtt_manager.h"
#include "telemetry.h"

// Subsystem Instances
ActuatorManager  actuatorManager;
StateMachine     stateMachine(actuatorManager);
MqttManager      mqttManager(stateMachine);
TelemetryManager telemetryManager(actuatorManager, stateMachine, mqttManager);

void setup() {
    // 1. Initialize High-Speed Serial Debug Port
    Serial.begin(115200);
    delay(500);

    Serial.println("\n");
    Serial.println("=====================================================");
    Serial.println("         AIRCONTROL AI - ESP32 FIRMGEN FIRMWARE      ");
    Serial.println("=====================================================");
    Serial.printf("Firmware Version : %s\n", FIRMWARE_VERSION);
    Serial.printf("Hardware ID      : %s\n", DEVICE_HARDWARE_ID);
    Serial.printf("Actuator Pins    : Green=%d, Red=%d, Buzz=%d, Servo=%d\n",
                  PIN_GREEN_LED, PIN_RED_LED, PIN_BUZZER, PIN_SERVO);
    Serial.println("=====================================================");

    // 2. Initialize Hardware Actuators (FR6 - FR10)
    actuatorManager.begin();

    // 3. Initialize WiFi and MQTT Client (FR4, FR5, FR11)
    mqttManager.begin();

    // 4. Initialize Telemetry System (FR11, FR12)
    telemetryManager.begin();

    Serial.println("[SETUP] ESP32 Ready to receive gesture commands.\n");
}

void loop() {
    // 1. Maintain WiFi and MQTT connection state, dispatch inbound messages
    mqttManager.loop();

    // 2. Non-blocking update of hardware timers (e.g. alarm pulse turn-off)
    actuatorManager.update();

    // 3. Periodic broadcast of runtime telemetry
    telemetryManager.publishIfDue();

    // Yield short CPU slice to ESP32 RTOS IDLE task
    delay(5);
}
