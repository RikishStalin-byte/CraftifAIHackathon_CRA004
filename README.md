# AirControl AI ✋🤖⚡
**Touchless Physical AI Device Control System**

[![Physical AI](https://img.shields.io/badge/Paradigm-See%20→%20Decide%20→%20Act-blue.svg)](https://github.com)
[![ESP32](https://img.shields.io/badge/Microcontroller-ESP32%20(FirmGen)-red.svg)](https://espressif.com)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV%20PipeGen-green.svg)](https://opencv.org)
[![MQTT](https://img.shields.io/badge/Protocol-MQTT%20QoS1-orange.svg)](https://mqtt.org)
[![Tests](https://img.shields.io/badge/Unit%20Tests-15%20Passed-brightgreen.svg)](tests/)

AirControl AI is an end-to-end Physical AI system that enables intuitive, touchless control of physical hardware using real-time computer vision gesture recognition and low-latency embedded firmware. The system is designed for laboratories, sterile hospital operating rooms, cleanrooms, and automated smart environments where physical contact with switches is unsafe, unhygienic, or impractical.

---

## 🔄 The Physical AI Workflow

AirControl AI strictly adheres to the **"See → Decide → Act"** Physical AI paradigm:

```
    ┌───────────────┐
    │  HUMAN USER   │
    └───────┬───────┘
            │ Hand Gesture
            ▼
┌───────────────────────┐
│     1. SEE (Vision)   │  Camera captures 30 FPS video feed;
│       Optical Feed    │  automatic fallback to synthetic virtual stream if no camera.
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│   2. DECIDE (Compute) │  PipeGen analyzes skin contours, aspect ratios, and
│   PipeGen Classifier  │  convexity defects; debounces and maps to command tokens.
└───────────┬───────────┘
            │ Dispatches JSON payload over MQTT (QoS 1)
            ▼
┌───────────────────────┐
│    3. ACT (Physical)  │  ESP32 microcontroller executes hardware action
│   ESP32 FirmGen Code  │  (LEDs, Servo Motor, Active Buzzer) and streams telemetry.
└───────────────────────┘
```

---

## ✋ Supported Gestures & Hardware Actions

| # | Gesture | Visual Representation | Target Actuator | Physical Action |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Open Hand** | 🖐️ All 5 fingers extended | Green LED (GPIO 27) | **Turn ON Green LED** |
| **2** | **Fist** | ✊ Closed hand | Green LED (GPIO 27) | **Turn OFF Green LED** |
| **3** | **Thumbs Up** | 👍 Thumb pointing upwards | Micro Servo (GPIO 13) | **Rotate Servo to 90° (Open)** |
| **4** | **Thumbs Down**| 👎 Thumb pointing downwards| Micro Servo (GPIO 13) | **Rotate Servo to 0° (Closed)** |
| **5** | **Victory Sign**| ✌️ Index & middle fingers V | Red LED & Buzzer (GPIO 26 & 25) | **Activate Red Strobe & Buzzer Alert** |

---

## 📁 Repository Structure

```
AirControl AI/
├── config/
│   └── default_config.json        # Centralized system, broker & camera settings
├── docs/                          # Complete Engineering Deliverables Documentation
│   ├── 01_REQUIREMENTS_SPECIFICATION.md
│   ├── 02_FUNCTIONAL_REQUIREMENTS.md
│   ├── 03_ACCEPTANCE_CRITERIA.md
│   ├── 04_SYSTEM_DESIGN_DOCUMENT.md
│   ├── 05_IMPLEMENTATION_TASKS.md
│   ├── 06_UNIT_TESTS_SPECIFICATION.md
│   ├── 07_FIRMWARE_STRUCTURE.md
│   ├── 08_TRACEABILITY_REPORT.md
│   ├── 09_TELEMETRY_DESIGN.md
│   └── 10_ESP32_FIRMWARE_GUIDE.md
├── firmware/                      # ESP32 C++ Production Firmware (FirmGen)
│   ├── platformio.ini             # PlatformIO build definition
│   ├── include/
│   │   ├── config.h               # Pin assignments & MQTT parameters
│   │   ├── actuators.h            # Hardware abstraction layer
│   │   ├── state_machine.h        # Gesture command parsing state machine
│   │   ├── mqtt_manager.h         # WiFi & MQTT manager with LWT
│   │   └── telemetry.h            # Runtime telemetry serialization
│   └── src/
│       ├── main.cpp               # Setup & non-blocking execution loop
│       ├── actuators.cpp          # Non-blocking PWM & GPIO actuation
│       ├── state_machine.cpp      # Action execution & latency tracking
│       ├── mqtt_manager.cpp       # Network client loop & JSON router
│       └── telemetry.cpp          # Periodic telemetry reporter
├── pipegen/                       # Computer Vision Gesture Engine ("See" & "Decide")
│   ├── config.py                  # Config loader
│   ├── camera_stream.py           # Video capture with synthetic fallback
│   ├── gesture_classifier.py      # Real-time contour & convexity defect classifier
│   ├── mqtt_publisher.py          # Paho MQTT publisher with ISO-8601 timestamps
│   ├── visualizer.py              # Real-time HUD overlay with telemetry cards
│   └── main.py                    # PipeGen main application entrypoint
├── simulator/                     # Virtual ESP32 Hardware Simulator
│   ├── esp32_simulator.py         # Simulates physical ESP32 state machine over MQTT
│   └── run_system_demo.py         # Launches simulator + PipeGen for instant demo
├── tests/                         # Pytest Automated Test Suite
│   ├── test_gesture_classifier.py # Vision & debounce unit tests
│   ├── test_mqtt_publisher.py     # JSON payload formatting tests
│   ├── test_telemetry_parser.py   # Telemetry schema tests
│   └── test_end_to_end.py         # Full Physical AI loop integration tests
├── requirements.txt               # Python package dependencies
└── README.md                      # System documentation & quickstart
```

---

## ⚡ Quick Start Guide

### 1. Installation
Install the required Python dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Run the Integrated End-to-End Demo (Zero Hardware Required)
Test the entire "See → Decide → Act" pipeline immediately with the virtual ESP32 simulator:
```powershell
python simulator/run_system_demo.py
```
*This launches both the virtual ESP32 simulator and the PipeGen computer vision HUD. Use keys `1` to `5` on the video window to instantly trigger gesture actuations!*

### 3. Run PipeGen Computer Vision Engine Separately
```powershell
# Run with physical webcam:
python pipegen/main.py

# Run in virtual/mock camera mode:
python pipegen/main.py --mock-camera

# Run in headless mode:
python pipegen/main.py --headless --iterations 100
```

### 4. Run the Virtual ESP32 Hardware Simulator
```powershell
python simulator/esp32_simulator.py
```

### 5. Run the Automated Test Suite
```powershell
python -m pytest tests -v
```
*(All 15 unit and integration tests execute and pass in ~1.3 seconds)*

---

## 🔌 ESP32 Hardware Wiring Guide

| Component | ESP32 GPIO | Electrical Connection |
| :--- | :---: | :--- |
| **Green LED Anode (+)** | **GPIO 27** | Through 220Ω resistor to GPIO 27; Cathode to GND |
| **Red LED Anode (+)** | **GPIO 26** | Through 220Ω resistor to GPIO 26; Cathode to GND |
| **Active Buzzer (+)** | **GPIO 25** | Positive pin to GPIO 25; Negative pin to GND |
| **Servo Motor (Signal)** | **GPIO 13** | Orange PWM line to GPIO 13 |
| **Servo Motor (Power)** | **VIN / 5V** | Red line to 5V rail |
| **Servo Motor (Ground)**| **GND** | Brown line to Common GND |

---

## 📡 MQTT Message Protocol

### Command Topic: `aircontrol/commands/gesture`
```json
{
  "gesture": "THUMBS_UP",
  "timestamp": "2026-10-16T18:00:00Z"
}
```

### Telemetry Topic: `aircontrol/device/telemetry`
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

---

## 📋 Deliverables Summary Checklist

- [x] **1. Requirements Specification:** [`docs/01_REQUIREMENTS_SPECIFICATION.md`](docs/01_REQUIREMENTS_SPECIFICATION.md)
- [x] **2. Functional Requirements (FR1 - FR12):** [`docs/02_FUNCTIONAL_REQUIREMENTS.md`](docs/02_FUNCTIONAL_REQUIREMENTS.md)
- [x] **3. Acceptance Criteria:** [`docs/03_ACCEPTANCE_CRITERIA.md`](docs/03_ACCEPTANCE_CRITERIA.md)
- [x] **4. Design Document:** [`docs/04_SYSTEM_DESIGN_DOCUMENT.md`](docs/04_SYSTEM_DESIGN_DOCUMENT.md)
- [x] **5. Implementation Tasks (WBS):** [`docs/05_IMPLEMENTATION_TASKS.md`](docs/05_IMPLEMENTATION_TASKS.md)
- [x] **6. Unit Tests Specification & Results:** [`docs/06_UNIT_TESTS_SPECIFICATION.md`](docs/06_UNIT_TESTS_SPECIFICATION.md)
- [x] **7. Firmware Structure:** [`docs/07_FIRMWARE_STRUCTURE.md`](docs/07_FIRMWARE_STRUCTURE.md)
- [x] **8. Traceability Report:** [`docs/08_TRACEABILITY_REPORT.md`](docs/08_TRACEABILITY_REPORT.md)
- [x] **9. Telemetry Design:** [`docs/09_TELEMETRY_DESIGN.md`](docs/09_TELEMETRY_DESIGN.md)
- [x] **10. ESP32 Firmware Generation:** [`firmware/`](firmware/) & [`docs/10_ESP32_FIRMWARE_GUIDE.md`](docs/10_ESP32_FIRMWARE_GUIDE.md)
