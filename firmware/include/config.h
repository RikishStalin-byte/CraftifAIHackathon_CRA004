/**
 * @file config.h
 * @brief System configuration, hardware pinouts, and network credentials for AirControl AI.
 * 
 * Aligned with Physical AI "Act" stage and Functional Requirements FR5 - FR12.
 */

#pragma once

#include <Arduino.h>

// ==========================================
// 1. HARDWARE PIN DEFINITIONS (ESP32)
// ==========================================
#define PIN_GREEN_LED       27      // FR6, FR7: Open Hand (ON), Fist (OFF)
#define PIN_RED_LED         26      // FR10: Victory Sign Alert
#define PIN_BUZZER          25      // FR10: Active Buzzer Alarm
#define PIN_SERVO           13      // FR8, FR9: Thumbs Up (90 deg), Thumbs Down (0 deg)

// ==========================================
// 2. SERVO PWM CONFIGURATION
// ==========================================
#define SERVO_ANGLE_OPEN    90      // FR8: Thumbs Up position (degrees)
#define SERVO_ANGLE_CLOSED  0       // FR9: Thumbs Down position (degrees)
#define SERVO_MIN_US        500     // Minimum pulse width in microseconds
#define SERVO_MAX_US        2400    // Maximum pulse width in microseconds

// ==========================================
// 3. ACTUATION TIMINGS
// ==========================================
#define ALARM_PULSE_DURATION_MS   1200   // FR10: Active alert pulse duration
#define TELEMETRY_INTERVAL_MS     3000   // FR11, FR12: Telemetry transmission period

// ==========================================
// 4. NETWORK & MQTT BROKER CONFIGURATION
// ==========================================
#define WIFI_SSID           "YOUR_WIFI_SSID"
#define WIFI_PASSWORD       "YOUR_WIFI_PASSWORD"

#define MQTT_BROKER_HOST    "broker.emqx.io"
#define MQTT_BROKER_PORT    1883
#define MQTT_CLIENT_ID      "ESP32_AirControl_FirmGen"

// MQTT Topics
#define TOPIC_GESTURE_CMD   "aircontrol/commands/gesture"    // FR4, FR5: Inbound gesture commands
#define TOPIC_DEVICE_STATUS "aircontrol/device/status"      // FR11: Online/Offline LWT status
#define TOPIC_TELEMETRY     "aircontrol/device/telemetry"   // FR12: Runtime telemetry stream

// Firmware Metadata
#define FIRMWARE_VERSION    "1.0.0-firmgen"
#define DEVICE_HARDWARE_ID  "ESP32_AIRCONTROL_DEV01"
