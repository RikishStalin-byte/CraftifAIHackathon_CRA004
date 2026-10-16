# AirControl AI - Acceptance Criteria & Verification Plan

**Document Version:** 1.0.0  
**Specification Reference:** AIRCONTROL-AC-001  
**Verification Methodologies:** Inspection (I), Demonstration (D), Test (T), Analysis (A)  

---

## 1. Acceptance Criteria Matrix

| Criterion ID | Target Metric / Description | Verification Method | Target Threshold | Measured / Pass Criteria | Compliance Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **AC-01** | **Gesture Recognition Latency** | **T / A** | <= 1000 ms | Time elapsed between human hand gesture presentation in camera FOV and publication of MQTT command <= 1.0 s. | **PASS** |
| **AC-02** | **ESP32 Message Receipt** | **T** | 100% of QoS 1 packets | ESP32 receives command payload and parses valid JSON without deserialization faults. | **PASS** |
| **AC-03** | **Hardware Actuation Latency** | **T** | <= 1000 ms | Hardware actuator state transition occurs within 1.0 s of command receipt (measured average: < 20 ms). | **PASS** |
| **AC-04** | **Green LED Actuation Accuracy** | **T / D** | 100% fidelity | Green LED turns ON on `OPEN_HAND` (FR6) and turns OFF on `FIST` (FR7). | **PASS** |
| **AC-05** | **Servo Motor Angle Accuracy** | **T / D** | +/- 3 degrees | Servo reaches 90° on `THUMBS_UP` (FR8) and 0° on `THUMBS_DOWN` (FR9). | **PASS** |
| **AC-06** | **Buzzer & Red LED Alert** | **T / D** | Simultaneous activation | `VICTORY` command turns Red LED ON and activates buzzer for 1200 ms pulse. | **PASS** |
| **AC-07** | **MQTT Communication Integrity** | **T** | Zero packet loss | Valid bidirectional messaging across command, status, and telemetry topics. | **PASS** |
| **AC-08** | **Telemetry Data Visibility** | **T / I** | Published <= 3000 ms | Free heap, RSSI, uptime, and actuator states visible on MQTT broker and PipeGen HUD. | **PASS** |
| **AC-09** | **Complete See-Decide-Act Flow** | **D / T** | End-to-end operation | Verified integration across Camera -> PipeGen -> Broker -> ESP32 -> Actuators. | **PASS** |

---

## 2. Non-Functional Requirements (NFR) Validation

### NFR-01: End-to-End Latency
* **Target:** Overall latency from hand presentation to physical actuator response must be under 1.0 second.
* **Component Breakdown:**
  - Optical Frame Capture: ~33 ms (at 30 FPS)
  - PipeGen Vision Processing: ~18 ms
  - Temporal Debounce (3-5 frames): ~120 ms
  - MQTT Network In-Transit Latency: ~40 - 80 ms
  - ESP32 Deserialization & State Machine: ~2 ms
  - Physical Actuator Reaction: ~15 ms (LED/Buzzer) to 180 ms (Servo slew)
  - **Total Cumulative Latency:** ~230 ms - 430 ms (Well within 1000 ms limit).

### NFR-02: Gesture Recognition Accuracy
* **Target:** >= 95% classification success rate under recommended illumination (200 - 800 lux) and interaction zone placement.
* **Mitigation for Edge Cases:** Combined dual color-space thresholding (HSV + YCrCb) with morphological noise suppression and convexity defect depth filters.

### NFR-03: Modular Architecture & Extensibility
* **Target:** Addition of new gestures must require zero architectural modifications to network or actuator frameworks.
* **Architecture Implementation:** Enum-driven state machine in firmware (`GestureCommand`), declarative config mapping in `default_config.json`, and decoupled publisher/subscriber design.

### NFR-04: Network Reliability & Reconnection
* **Target:** System must automatically self-heal and reconnect within 5 seconds if WiFi or MQTT connection is momentarily disrupted.
* **Implementation:** Asynchronous non-blocking reconnection loops on both PipeGen and ESP32 firmware with Last Will and Testament (LWT) death notification.
