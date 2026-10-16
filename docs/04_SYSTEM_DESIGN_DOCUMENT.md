# AirControl AI - System Design Document (SDD)

**Document Version:** 1.0.0  
**Status:** Approved  
**Classification:** Technical Architecture & Design Document  

---

## 1. System Architecture

AirControl AI demonstrates the complete **Physical AI** loop: **See → Decide → Act**.

```mermaid
flowchart TD
    subgraph SEE["1. SEE (Perception)"]
        A["Human User Hand"] -->|"Photons / Visible Spectrum"| B["USB Optical Camera"]
        B -->|"Video Stream (640x480 @ 30FPS)"| C["Frame Buffer Ingestion"]
    end

    subgraph DECIDE["2. DECIDE (Cognition & Intelligence)"]
        C --> D["Color Space Transformation (HSV + YCrCb)"]
        D --> E["Morphological Segmentation & Contour Analysis"]
        E --> F["Convexity Defects & Aspect Ratio Classification"]
        F --> G["Temporal Debouncing & Cooldown Filter"]
        G --> H["Action Command Mapping & JSON Packaging"]
    end

    subgraph TRANSPORT["Message Broker (Transport)"]
        H -->|"MQTT QoS 1 (TCP Port 1883)"| I["MQTT Broker (broker.emqx.io)"]
    end

    subgraph ACT["3. ACT (Physical Embodiment)"]
        I -->|"Subscribed Topic: aircontrol/commands/gesture"| J["ESP32 MQTT Client"]
        J --> K["ArduinoJson Parser"]
        K --> L["Actuator State Machine"]
        
        L -->|"GPIO 27 HIGH/LOW"| M["Green LED (Illumination)"]
        L -->|"GPIO 13 50Hz PWM"| N["Servo Motor (Mechanical Gate/Latch)"]
        L -->|"GPIO 26 HIGH"| O["Red LED (Alert Strobe)"]
        L -->|"GPIO 25 HIGH"| P["Active Buzzer (Audible Alarm)"]

        L --> Q["Telemetry Engine"]
        Q -->|"Publish: aircontrol/device/telemetry"| I
    end
```

---

## 2. Sequence Diagram (End-to-End Gesture Actuation)

```mermaid
sequenceDiagram
    autonumber
    actor User as Human Operator
    participant Cam as USB Camera
    participant Pipe as PipeGen Vision Engine
    participant Broker as MQTT Broker
    participant ESP as ESP32 Firmware
    participant Act as Physical Actuators (LED/Servo/Buzzer)

    User->>Cam: Presents Hand Gesture (e.g. Thumbs Up)
    Cam->>Pipe: Transmits Raw BGR Frame (30 FPS)
    Note over Pipe: SEE: Hand segmentation & contouring<br/>DECIDE: Feature extraction -> THUMBS_UP
    Pipe->>Pipe: Debounce (5 frames) & Cooldown check
    Pipe->>Broker: PUBLISH aircontrol/commands/gesture {"gesture":"THUMBS_UP", ...}
    Broker->>ESP: DISPATCH MQTT message to subscriber
    Note over ESP: ACT: Parse JSON -> StateMachine.handleGestureCommand()
    ESP->>Act: Write PWM to GPIO 13 (90 degrees)
    Act-->>User: Physical Action: Barrier Opens (90 deg)
    ESP->>Broker: PUBLISH aircontrol/device/telemetry (Status, Heap, Angle: 90)
    Broker-->>Pipe: Telemetry Update displayed on HUD
```

---

## 3. Hardware Schematic & Pin Mapping

### 3.1 Actuator Pinout Table
| Actuator Component | Function / Role | ESP32 GPIO | Drive Interface | Electrical Characteristics |
| :--- | :--- | :---: | :--- | :--- |
| **Green LED** | Power / Status Indicator | **GPIO 27** | Direct Digital Out | 3.3V Logic through 220Ω current-limiting resistor (~10 mA) |
| **Red LED** | Warning / Alarm Strobe | **GPIO 26** | Direct Digital Out | 3.3V Logic through 220Ω current-limiting resistor (~10 mA) |
| **Active Buzzer** | Audible Warning Beep | **GPIO 25** | Direct Digital Out / NPN Transistor | 3.3V Logic or 5V rail switched via 2N2222 / S8050 NPN driver |
| **Micro Servo (SG90/MG90S)** | Physical Mechanical Actuator | **GPIO 13** | Hardware PWM (ESP32PWM) | 50 Hz PWM carrier, 500µs (0°) to 2400µs (180°), powered via 5V rail |

### 3.2 Electrical Wiring Diagram
```
    ┌──────────────────────────────────────────────┐
    │             ESP32 DEVELOPMENT BOARD          │
    │                                              │
    │   [GPIO 27] ──────[ 220Ω ]──────( Green LED )─┐
    │                                              │
    │   [GPIO 26] ──────[ 220Ω ]──────(  Red LED  )─┤
    │                                              │
    │   [GPIO 25] ───────────────────( Active Buzz )┤
    │                                              │
    │   [GPIO 13] ────────[ PWM Signal ]──────────┐│
    │                                             ││
    │   [  GND  ] ────────────────────────────────┼┴──── (COMMON GROUND)
    │   [  VIN  ] ───────( +5V DC Rail )──────────┼───── (SERVO +5V VCC)
    │                                             │
    │                     ┌───────────────────────┘
    │                     ▼
    │            ┌─────────────────┐
    │            │ SG90 SERVO MOTOR│
    │            │ Orange : PWM    │
    │            │ Red    : +5V    │
    │            │ Brown  : GND    │
    │            └─────────────────┘
    └──────────────────────────────────────────────┘
```

---

## 4. MQTT Protocol Architecture

### 4.1 Topic Hierarchy
```
aircontrol/
├── commands/
│   └── gesture         [QoS 1] Direction: PipeGen -> ESP32
└── device/
    ├── status          [QoS 1, Retained] Direction: ESP32 -> Broker / Clients (LWT)
    └── telemetry       [QoS 0] Direction: ESP32 -> Broker / PipeGen HUD
```

### 4.2 Message Schemas

#### Command Topic (`aircontrol/commands/gesture`)
```json
{
  "gesture": "THUMBS_UP",
  "timestamp": "2026-10-16T18:00:00Z"
}
```

#### Device Status Topic (`aircontrol/device/status`)
*Online Notification (Retained):*
```json
{
  "device_id": "ESP32_AIRCONTROL_DEV01",
  "status": "ONLINE",
  "firmware_version": "1.0.0-firmgen",
  "ip_address": "192.168.1.105",
  "mac_address": "24:6F:28:XX:YY:ZZ"
}
```
*Offline Notification (Last Will & Testament - Retained):*
```json
{
  "device_id": "ESP32_AIRCONTROL_DEV01",
  "status": "OFFLINE"
}
```

#### Telemetry Topic (`aircontrol/device/telemetry`)
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

## 5. Actuator State Machine Design

The firmware maintains an explicit deterministic finite-state machine (FSM).

```mermaid
stateDiagram-v2
    [*] --> SYSTEM_INIT : Boot & Hardware Config
    SYSTEM_INIT --> CONNECTING_NETWORK : Init WiFi & MQTT
    CONNECTING_NETWORK --> READY_IDLE : MQTT Connected & Subscribed
    
    READY_IDLE --> ACTUATING_GREEN_ON : RECV "OPEN_HAND"
    ACTUATING_GREEN_ON --> READY_IDLE : GPIO 27 -> HIGH
    
    READY_IDLE --> ACTUATING_GREEN_OFF : RECV "FIST"
    ACTUATING_GREEN_OFF --> READY_IDLE : GPIO 27 -> LOW
    
    READY_IDLE --> ACTUATING_SERVO_OPEN : RECV "THUMBS_UP"
    ACTUATING_SERVO_OPEN --> READY_IDLE : PWM -> 90 deg
    
    READY_IDLE --> ACTUATING_SERVO_CLOSED : RECV "THUMBS_DOWN"
    ACTUATING_SERVO_CLOSED --> READY_IDLE : PWM -> 0 deg
    
    READY_IDLE --> ALARM_PULSE_ACTIVE : RECV "VICTORY"
    state ALARM_PULSE_ACTIVE {
        [*] --> ALARM_ON : Red LED HIGH, Buzzer HIGH
        ALARM_ON --> ALARM_TIMER : Start 1200ms non-blocking timer
        ALARM_TIMER --> ALARM_EXPIRED : millis() >= 1200ms
        ALARM_EXPIRED --> [*] : Red LED LOW, Buzzer LOW
    }
    ALARM_PULSE_ACTIVE --> READY_IDLE : Alarm Expired
```

---

## 6. Fail-Safe & Watchdog Mechanisms
1. **MQTT LWT (Last Will & Testament):** Guarantees that any abrupt loss of connectivity (power failure or WiFi drop) immediately informs supervisory dashboards.
2. **Non-Blocking Execution:** No `delay()` operations exist in the main loop; all timers rely on `millis()` timestamps.
3. **Out-of-Range Clamping:** Servo angles outside [0, 180] are clamped to safe structural bounds.
4. **Buffer Overrun Protection:** `ArduinoJson` static memory allocations prevent heap fragmentation on the microcontroller.
