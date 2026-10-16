# AirControl AI - Functional Requirements Specification

**Document Version:** 1.0.0  
**Specification Reference:** AIRCONTROL-FRS-001  
**Traceability Category:** Functional Requirements (FR1 - FR12)  

---

## Detailed Functional Requirements

### FR1: Live Camera Feed Acquisition
* **Requirement Statement:** The system shall capture continuous video frames from a live video capture device (USB camera) or a calibrated fallback synthetic video stream.
* **Input:** Optical sensor stream at minimum 640x480 resolution.
* **Processing:** Frame capture, horizontal mirror inversion (to provide an intuitive interaction mirror), format validation, and conversion to standard BGR matrix representation.
* **Output:** Valid NumPy BGR image matrix delivered to the classification pipeline.
* **Preconditions:** Camera device connected and accessible, or fallback mock stream active.
* **Postconditions:** Frame buffer populated without memory leakage.

---

### FR2: Real-Time Frame Processing
* **Requirement Statement:** The system shall continuously process incoming video frames in real time with an end-to-end pipeline processing rate of at least 20 frames per second (FPS).
* **Input:** Raw BGR image frames from FR1.
* **Processing:** Skin chrominance segmentation (HSV + YCrCb color spaces), morphological filtering (opening and closing), contour identification, and convex hull computation.
* **Output:** Cleaned binary mask and dominant hand contour coordinates.
* **Temporal Constraint:** Per-frame computation budget must not exceed 50 milliseconds.

---

### FR3: Discrete Gesture Classification
* **Requirement Statement:** The system shall classify extracted hand features into one of five discrete predefined gesture commands: `OPEN_HAND`, `FIST`, `THUMBS_UP`, `THUMBS_DOWN`, `VICTORY`, or `NONE`.
* **Input:** Hand contour, bounding box, convexity defects, and centroid moments.
* **Processing Decision Rules:**
  - `OPEN_HAND`: Convexity defects count >= 3, solidity < 0.75, confidence >= 0.70.
  - `FIST`: Bounding box aspect ratio ~1.0, solidity > 0.85, defects count <= 1.
  - `THUMBS_UP`: Single dominant upper protrusion relative to centroid; upward vertical protrusion ratio > 1.35.
  - `THUMBS_DOWN`: Single dominant lower protrusion relative to centroid; downward vertical protrusion ratio > 1.35.
  - `VICTORY`: Exactly two extended fingers, deep inter-digit defect, solidity between 0.60 and 0.82.
* **Debounce & Filtering:** Requires 5 consecutive identical frames before confirming state transition; enforces 1.0-second cooldown between repeated dispatches.
* **Output:** `GestureResult` object containing classification label, confidence score (0.0 to 1.0), and geometric telemetry.

---

### FR4: MQTT Command Publishing
* **Requirement Statement:** The system shall serialize confirmed gesture commands into a validated JSON payload and publish the message over MQTT to the command topic `aircontrol/commands/gesture` using Quality of Service level 1 (QoS 1).
* **Input:** Confirmed `GestureResult` from FR3.
* **Payload Format:**
  ```json
  {
    "gesture": "THUMBS_UP",
    "timestamp": "2026-10-16T18:00:00Z"
  }
  ```
* **Output:** MQTT PUBLISH packet acknowledged (PUBACK) by the broker.
* **Error Handling:** Automatic reconnection with exponential backoff if socket drops.

---

### FR5: ESP32 MQTT Command Subscription
* **Requirement Statement:** The ESP32 firmware shall maintain an active subscription to the MQTT command topic `aircontrol/commands/gesture` and parse incoming payloads without blocking the main execution loop.
* **Input:** MQTT message stream from broker.
* **Processing:** Zero-copy string deserialization using `ArduinoJson`, schema validation, extraction of `"gesture"` string token, and routing to the actuator state machine.
* **Output:** Decoded command token passed to State Machine.
* **Preconditions:** ESP32 successfully connected to WiFi and MQTT broker.

---

### FR6: Green LED Illumination (Open Hand)
* **Requirement Statement:** The ESP32 shall assert GPIO 27 to logic HIGH upon receiving an `OPEN_HAND` gesture command, turning ON the green indicator LED.
* **Input:** Command `"gesture": "OPEN_HAND"`.
* **Action:** `digitalWrite(PIN_GREEN_LED, HIGH);`
* **Output:** Green LED turns ON; internal state `_greenLedState` set to `true`.
* **Latency Constraint:** Actuation response time <= 100 ms from message receipt.

---

### FR7: Green LED Deactivation (Fist)
* **Requirement Statement:** The ESP32 shall assert GPIO 27 to logic LOW upon receiving a `FIST` gesture command, turning OFF the green indicator LED.
* **Input:** Command `"gesture": "FIST"`.
* **Action:** `digitalWrite(PIN_GREEN_LED, LOW);`
* **Output:** Green LED turns OFF; internal state `_greenLedState` set to `false`.
* **Latency Constraint:** Actuation response time <= 100 ms from message receipt.

---

### FR8: Servo Motor Open Position (Thumbs Up)
* **Requirement Statement:** The ESP32 shall rotate the servo motor to the 90-degree position upon receiving a `THUMBS_UP` gesture command.
* **Input:** Command `"gesture": "THUMBS_UP"`.
* **Action:** Generate 50 Hz PWM pulse train corresponding to 90 degrees (`_servo.write(90)`).
* **Output:** Physical servo horn rotates to 90° (open barrier / latch state); `_currentServoAngle` set to 90.
* **Latency Constraint:** Pulse width updated within 50 ms of message receipt.

---

### FR9: Servo Motor Closed Position (Thumbs Down)
* **Requirement Statement:** The ESP32 shall rotate the servo motor to the 0-degree position upon receiving a `THUMBS_DOWN` gesture command.
* **Input:** Command `"gesture": "THUMBS_DOWN"`.
* **Action:** Generate 50 Hz PWM pulse train corresponding to 0 degrees (`_servo.write(0)`).
* **Output:** Physical servo horn rotates to 0° (closed barrier / latch state); `_currentServoAngle` set to 0.
* **Latency Constraint:** Pulse width updated within 50 ms of message receipt.

---

### FR10: Alert Actuation (Victory Sign)
* **Requirement Statement:** The ESP32 shall activate the red LED (GPIO 26) and the active acoustic buzzer (GPIO 25) upon receiving a `VICTORY` gesture command.
* **Input:** Command `"gesture": "VICTORY"`.
* **Action:** Assert GPIO 26 HIGH and GPIO 25 HIGH for a duration of 1200 milliseconds using non-blocking software timers.
* **Output:** Red warning strobe illuminated and acoustic warning alarm sounded simultaneously; both automatically deactivate after timeout without stalling system loops.
* **Postconditions:** Actuator states revert to safe idle upon timer expiration.

---

### FR11: Device Status Reporting & LWT
* **Requirement Statement:** The firmware shall maintain and publish device connection status to `aircontrol/device/status`, utilizing MQTT Last Will and Testament (LWT) to ensure accurate connectivity tracking.
* **Payload Details:**
  - Online Payload (retained): `{"device_id": "...", "status": "ONLINE", "firmware_version": "1.0.0-firmgen", "ip_address": "..."}`
  - Offline Payload (LWT retained): `{"device_id": "...", "status": "OFFLINE"}`
* **Trigger:** Published immediately on connection and broker-broadcasted on ungraceful disconnect.

---

### FR12: Real-Time Runtime Telemetry Streaming
* **Requirement Statement:** The firmware shall gather system health metrics and actuator telemetry, and publish a structured JSON report to `aircontrol/device/telemetry` at periodic intervals (default 3000 ms) and immediately following state changes.
* **Reported Metrics:**
  - System: `uptime_ms`, `wifi_rssi`, `free_heap_bytes`.
  - Actuators: `green_led`, `red_led`, `servo_angle`, `buzzer_active`.
  - Operational: `commands_received`, `commands_executed`, `last_gesture`, `execution_latency_ms`.
