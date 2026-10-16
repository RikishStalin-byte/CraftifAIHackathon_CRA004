# AirControl AI - Telemetry Subsystem Design Document

**Document Version:** 1.0.0  
**Specification Reference:** AIRCONTROL-TEL-001  
**Protocols:** MQTT v3.1.1 / JSON (RFC 8259)  

---

## 1. Overview & Objectives

The Telemetry Subsystem provides real-time observability into the physical state and runtime performance of the ESP32 edge actuator node. Aligned with requirements **FR11** and **FR12**, the subsystem accomplishes three goals:
1. **Health & Reliability Telemetry:** Tracks heap memory, network signal strength (RSSI), and uptime to prevent system crashes and diagnose connectivity degradation.
2. **Actuator State Observability:** Streams instantaneous physical states (Green LED, Red LED, Servo Angle, Buzzer state) so the supervisory system (PipeGen) can confirm that the physical actuator matches the classified gesture.
3. **Operational Metrics:** Measures command execution latencies, total commands received vs. executed, and identifies anomalies.

---

## 2. Telemetry Channels & Topics

| Channel Name | MQTT Topic | Direction | QoS | Transmission Trigger |
| :--- | :--- | :---: | :---: | :--- |
| **Device Status (LWT)** | `aircontrol/device/status` | ESP32 → Broker | 1 (Retained) | On boot connection (ONLINE) & on broker disconnection (OFFLINE) |
| **Runtime Telemetry** | `aircontrol/device/telemetry` | ESP32 → Broker | 0 | Periodic (every 3000 ms) + Immediate on actuator state change |

---

## 3. Data Schema & Field Specifications

### 3.1 Runtime Telemetry JSON Payload
```json
{
  "device_id": "ESP32_AIRCONTROL_DEV01",
  "uptime_ms": 125430,
  "wifi_rssi": -58,
  "free_heap_bytes": 184512,
  "actuators": {
    "green_led": true,
    "red_led": false,
    "servo_angle": 90,
    "buzzer_active": false
  },
  "metrics": {
    "commands_received": 14,
    "commands_executed": 14,
    "last_gesture": "THUMBS_UP",
    "last_command_time_ms": 124900,
    "execution_latency_ms": 12
  },
  "timestamp": "2026-10-16T20:56:23Z"
}
```

### 3.2 Data Dictionary

| Field | JSON Path | Data Type | Units / Format | Description |
| :--- | :--- | :---: | :---: | :--- |
| `device_id` | `$.device_id` | String | UTF-8 String | Unique hardware device identifier |
| `uptime_ms` | `$.uptime_ms` | Integer | Milliseconds | Time elapsed since ESP32 boot |
| `wifi_rssi` | `$.wifi_rssi` | Integer | dBm | Received Signal Strength Indication (-30 to -90 dBm) |
| `free_heap_bytes` | `$.free_heap_bytes` | Integer | Bytes | Available unallocated SRAM in bytes |
| `green_led` | `$.actuators.green_led` | Boolean | `true` / `false` | Current state of GPIO 27 (Green LED) |
| `red_led` | `$.actuators.red_led` | Boolean | `true` / `false` | Current state of GPIO 26 (Red LED) |
| `servo_angle` | `$.actuators.servo_angle` | Integer | Degrees (0 - 180) | Current angular position of the servo motor |
| `buzzer_active` | `$.actuators.buzzer_active` | Boolean | `true` / `false` | Current activation state of GPIO 25 (Buzzer) |
| `commands_received` | `$.metrics.commands_received` | Integer | Counter | Cumulative gesture commands received over MQTT |
| `commands_executed` | `$.metrics.commands_executed` | Integer | Counter | Cumulative commands successfully dispatched to actuators |
| `last_gesture` | `$.metrics.last_gesture` | String | Token | String name of most recent gesture executed |
| `last_command_time_ms`| `$.metrics.last_command_time_ms`| Integer | Milliseconds | System timestamp when last command was received |
| `execution_latency_ms`| `$.metrics.execution_latency_ms`| Integer | Milliseconds | Time taken to decode command and assert GPIO/PWM |
| `timestamp` | `$.timestamp` | String | ISO-8601 UTC | UTC timestamp of packet assembly |

---

## 4. Edge Memory & Bandwidth Budget

- **Serialized Payload Size:** ~350 - 420 bytes per JSON frame.
- **Bandwidth Consumption:** At a 3-second broadcast interval, bandwidth usage is under 1.2 kbps, ensuring negligible network overhead.
- **Microcontroller Memory Footprint:** Built using `StaticJsonDocument<512>`, requiring zero heap allocation (`malloc`/`free`) and eliminating memory fragmentation risks.
