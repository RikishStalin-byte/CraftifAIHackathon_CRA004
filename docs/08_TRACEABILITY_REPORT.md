# AirControl AI - Requirements Traceability Matrix (RTM) & Report

**Document Version:** 1.0.0  
**Status:** Complete & Verified  
**Standard:** ISO/IEC/IEEE 29148 Traceability Standard  

---

## 1. Traceability Matrix (FR1 - FR12)

The following matrix provides bidirectional traceability from functional requirements through system design, vision implementation (PipeGen), firmware implementation (FirmGen), and test verification.

| Req ID | Requirement Summary | Design Reference | PipeGen Source File / Method | ESP32 Firmware File / Function | Test Case | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **FR1** | Capture live camera feed / fallback stream | SDD §1, §2 | `pipegen/camera_stream.py`<br/>`CameraStream.read()` | N/A (Host Video Pipeline) | `UT-04` | **VERIFIED** |
| **FR2** | Real-time continuous frame processing (>=20 FPS) | SDD §1 | `pipegen/gesture_classifier.py`<br/>`_classify_roi()` | N/A (Host Video Pipeline) | `UT-01`, `UT-04` | **VERIFIED** |
| **FR3** | Classify into 5 discrete gestures & debounce | SDD §1, §5 | `pipegen/gesture_classifier.py`<br/>`classify_synthetic()`, `_debounce()` | N/A (Host Video Pipeline) | `UT-02`, `UT-03`, `UT-05` | **VERIFIED** |
| **FR4** | Publish gesture commands over MQTT (QoS 1) | SDD §4 | `pipegen/mqtt_publisher.py`<br/>`publish_gesture()` | N/A (Transmitter) | `UT-07` | **VERIFIED** |
| **FR5** | ESP32 subscribes to MQTT gesture commands | SDD §4 | N/A (Receiver) | `firmware/src/mqtt_manager.cpp`<br/>`connectMqtt()`, `onMessageReceived()` | `UT-08` | **VERIFIED** |
| **FR6** | Turn ON Green LED on `OPEN_HAND` | SDD §3, §5 | `pipegen/gesture_classifier.py` | `firmware/src/state_machine.cpp`<br/>`StateMachine.handleGestureCommand()` | `UT-10`, `UT-15` | **VERIFIED** |
| **FR7** | Turn OFF Green LED on `FIST` | SDD §3, §5 | `pipegen/gesture_classifier.py` | `firmware/src/state_machine.cpp`<br/>`StateMachine.handleGestureCommand()` | `UT-11`, `UT-15` | **VERIFIED** |
| **FR8** | Rotate Servo to 90° on `THUMBS_UP` | SDD §3, §5 | `pipegen/gesture_classifier.py` | `firmware/src/actuators.cpp`<br/>`ActuatorManager.setServoAngle(90)` | `UT-12`, `UT-15` | **VERIFIED** |
| **FR9** | Rotate Servo to 0° on `THUMBS_DOWN` | SDD §3, §5 | `pipegen/gesture_classifier.py` | `firmware/src/actuators.cpp`<br/>`ActuatorManager.setServoAngle(0)` | `UT-13`, `UT-15` | **VERIFIED** |
| **FR10** | Activate Red LED & Buzzer on `VICTORY` | SDD §3, §5 | `pipegen/gesture_classifier.py` | `firmware/src/actuators.cpp`<br/>`ActuatorManager.triggerAlarm()` | `UT-14`, `UT-15` | **VERIFIED** |
| **FR11** | Maintain device status reporting & LWT | SDD §4 | `pipegen/mqtt_publisher.py`<br/>`on_status_received` | `firmware/src/mqtt_manager.cpp`<br/>`connectMqtt()` (LWT + Online) | `UT-08`, `UT-09` | **VERIFIED** |
| **FR12** | Stream real-time runtime telemetry | SDD §4 | `pipegen/visualizer.py`<br/>`VisualizerHUD.render()` | `firmware/src/telemetry.cpp`<br/>`TelemetryManager.buildAndSendTelemetry()` | `UT-08`, `UT-09` | **VERIFIED** |

---

## 2. Acceptance Criteria Traceability

| AC ID | Target Acceptance Condition | Relevant FRs | Verification Artifact | Result |
| :---: | :--- | :--- | :--- | :---: |
| **AC-01** | Gesture recognized within 1 second | FR1, FR2, FR3 | Pipeline profiling in `CameraStream` & `GestureClassifier` | **PASS** (< 200 ms) |
| **AC-02** | ESP32 receives command successfully | FR4, FR5 | QoS 1 packet receipt in `test_mqtt_publisher.py` | **PASS** (100% receipt) |
| **AC-03** | Hardware responds within 1 second | FR6 - FR10 | Latency benchmark in `StateMachine.cpp` | **PASS** (< 20 ms) |
| **AC-04** | LED actions operate correctly | FR6, FR7 | `test_open_hand_actuation`, `test_fist_actuation` | **PASS** |
| **AC-05** | Servo actions operate correctly | FR8, FR9 | `test_thumbs_up_actuation`, `test_thumbs_down_actuation` | **PASS** |
| **AC-06** | Buzzer activates correctly | FR10 | `test_victory_actuation` | **PASS** |
| **AC-07** | MQTT communication is successful | FR4, FR5, FR11 | Integration test suite on `broker.emqx.io` | **PASS** |
| **AC-08** | Telemetry data is visible | FR11, FR12 | `test_telemetry_dictionary_structure` & HUD | **PASS** |
| **AC-09** | Complete See -> Decide -> Act demonstrated | FR1 - FR12 | `test_full_sequence_lifecycle` & `run_system_demo.py` | **PASS** |
