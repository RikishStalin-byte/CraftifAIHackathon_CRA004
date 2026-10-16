# AirControl AI - Requirements Specification

**Document Version:** 1.0.0  
**Status:** Approved / Baseline  
**Project:** AirControl AI (Physical AI Touchless Device Control System)  
**Standard:** Aligned with IEEE 830 / ISO/IEC/IEEE 29148  

---

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive Requirements Specification for **AirControl AI**, an edge-to-cloud Physical AI system. It defines the operational domain, user characteristics, external interface definitions, functional boundaries, and non-functional constraints governing the automated detection of hand gestures and their translation into hardware actuation via an ESP32 microcontroller.

### 1.2 Problem Statement
In environments such as surgical suites, microbiological laboratories, semiconductor cleanrooms, food preparation facilities, and heavy industrial plants, physical contact with electrical switches, manual dials, mechanical levers, and control panels introduces severe operational hazards:
- **Biological Contamination:** Cross-contamination via pathogen transfer on shared physical surfaces.
- **Sterility Breaches:** Requirement for personnel to de-glove or re-sterilize after touching equipment.
- **Chemical / Electrical Hazards:** Physical interaction with controls while handling corrosive chemicals or wearing bulky PPE.
- **Mechanical Friction:** Wear and tear on physical contact buttons in high-cycle industrial automation.

### 1.3 Proposed Solution
**AirControl AI** addresses these problems through the **"See → Decide → Act"** Physical AI paradigm:
1. **SEE (Perception):** An optical sensor (USB camera) captures high-resolution video streams of human hand movements in real time.
2. **DECIDE (Cognition & Intelligence):** A Computer Vision pipeline (**PipeGen**) processes the video feed, segments the hand region, extracts geometric and topological landmarks, classifies discrete hand gestures, debounces transient states, and maps valid gestures to deterministic machine commands.
3. **ACT (Physical Embodiment):** An edge microcontroller (**ESP32**) running deterministic firmware generated using **FirmGen** best practices receives commands over a low-latency MQTT message bus, driving physical actuators (Green LED indicator, Red LED warning strobe, high-torque PWM servo motor, and active acoustic buzzer), while streaming real-time hardware telemetry back to the network.

---

## 2. Overall Description

### 2.1 System Architecture Overview

```
 [ HUMAN USER ]
        │
   (Hand Gesture)
        ▼
   ┌─────────┐
   │ CAMERA  │ ──── Optical Capture (30 FPS)
   └────┬────┘
        │ (Video Stream)
        ▼
┌────────────────────────────────────────────────────────┐
│                   SEE -> DECIDE                        │
│                 PipeGen Subsystem                      │
│                                                        │
│  - Video Ingestion & Frame Normalization               │
│  - Hand Detection & Morphological Segmentation         │
│  - Convexity Defects & Geometric Feature Extraction    │
│  - Temporal Debouncing & Cooldown Filter               │
│  - Command Mapping & JSON Message Packaging           │
└───────────────────────┬────────────────────────────────┘
                        │
                  (MQTT over TCP)
               Topic: aircontrol/commands/gesture
                        ▼
┌────────────────────────────────────────────────────────┐
│                   DECIDE -> ACT                        │
│                 MQTT Message Broker                    │
│            (Low-Latency Transport Layer)               │
└───────────────────────┬────────────────────────────────┘
                        │
                  (WiFi 802.11 b/g/n)
                        ▼
┌────────────────────────────────────────────────────────┐
│                        ACT                             │
│               ESP32 Firmware Subsystem                 │
│                                                        │
│  - Non-blocking MQTT Subscriber & JSON Parser          │
│  - Actuator State Machine & Command Router             │
│  - Multi-Actuator Hardware Driver Layer                │
│  - Telemetry Engine (Health, Uptime, Heap, RSSI)       │
└───────┬────────────────┬───────────────┬───────────────┘
        │                │               │               │
        ▼                ▼               ▼               ▼
 ┌─────────────┐  ┌─────────────┐  ┌───────────┐  ┌─────────────┐
 │  GREEN LED  │  │   RED LED   │  │   SERVO   │  │   BUZZER    │
 │  (GPIO 27)  │  │  (GPIO 26)  │  │ (GPIO 13) │  │  (GPIO 25)  │
 └─────────────┘  └─────────────┘  └───────────┘  └─────────────┘
```

### 2.2 Operational Environment
- **Host Processing Unit (PipeGen):** Workstation, edge PC, or single-board computer running Python 3.9+ with OpenCV, NumPy, and Paho-MQTT.
- **Embedded Edge Unit (FirmGen):** Espressif ESP32 dual-core Xtensa LX6 microcontroller operating at 240 MHz with 520 KB SRAM and 4 MB Flash.
- **Network Infrastructure:** IEEE 802.11b/g/n 2.4 GHz WiFi network; MQTT v3.1.1 / v5.0 compliant broker.

---

## 3. Gesture-to-Actuation Functional Matrix

| Gesture Token | Human Gesture Description | Target Hardware Actuator | Pin / Channel | Physical Action |
| :--- | :--- | :--- | :--- | :--- |
| **`OPEN_HAND`** | 5 fingers extended, palm facing camera | Green LED | GPIO 27 | Turn **ON** Green LED |
| **`FIST`** | All fingers closed into a compact fist | Green LED | GPIO 27 | Turn **OFF** Green LED |
| **`THUMBS_UP`** | Thumb pointing vertically upwards | Micro Servo Motor | GPIO 13 (PWM) | Rotate arm to **90° (Open)** |
| **`THUMBS_DOWN`** | Thumb pointing vertically downwards | Micro Servo Motor | GPIO 13 (PWM) | Rotate arm to **0° (Closed)** |
| **`VICTORY`** | Index & middle fingers extended (V sign) | Red LED & Buzzer | GPIO 26 & 25 | Trigger **Red LED & Buzzer Alert** |

---

## 4. User Classes and Characteristics
1. **Clinical / Laboratory Operators:** Require touchless, zero-contamination activation of doors, illumination, and sample storage compartments.
2. **Industrial Technicians:** Require rapid hands-free signaling in noisy, machinery-heavy environments where gloved hands preclude touchscreens.
3. **Embedded Systems Engineers:** Monitor runtime telemetry (free heap, command latencies, packet delivery rate, actuator states) for predictive maintenance.

---

## 5. Assumptions and Dependencies
- Camera delivers uncompressed or MJPEG video stream at minimum 640x480 resolution @ 20 FPS.
- Sufficient ambient light is present to permit skin chrominance segmentation.
- MQTT broker is reachable over TCP port 1883 with round-trip latency < 150 ms.
- ESP32 power rail provides clean 5V DC capable of sourcing up to 1.5A peak during simultaneous servo movement and buzzer activation.
