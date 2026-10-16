# AirControl AI - ESP32 Firmware Structure Document

**Document Version:** 1.0.0  
**Target Microcontroller:** Espressif ESP32 (Xtensa Dual-Core 32-bit LX6, 240 MHz)  
**Framework:** Arduino / ESP-IDF Core via PlatformIO  
**Design Paradigm:** FirmGen Layered Edge Architecture  

---

## 1. Firmware File Tree & Directory Layout

```
firmware/
├── platformio.ini               # Build system configuration & library dependencies
├── include/
│   ├── config.h                 # Centralized pin assignments, network parameters & timing
│   ├── actuators.h              # Actuator hardware driver interface (LED, Servo, Buzzer)
│   ├── state_machine.h          # Gesture command parsing and discrete actuation mapping
│   ├── mqtt_manager.h           # WiFi connectivity, MQTT subscription/publication & LWT
│   └── telemetry.h              # System health monitoring and telemetry reporting
└── src/
    ├── main.cpp                 # Application entrypoint (setup and non-blocking loop)
    ├── actuators.cpp            # Low-level GPIO, PWM timer allocation, and pulse timers
    ├── state_machine.cpp        # State transitions, metrics tracking, and command execution
    ├── mqtt_manager.cpp         # Network client loop, auto-reconnect, and JSON dispatch
    └── telemetry.cpp            # System metrics aggregation and JSON serialization
```

---

## 2. Layered Architectural Decomposition

The firmware follows FirmGen's strict separation of concerns into four decoupled layers:

```
┌────────────────────────────────────────────────────────┐
│             Application Coordination Layer             │
│                      (main.cpp)                        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│               Service Orchestration Layer              │
│       (state_machine.h / .cpp, telemetry.h / .cpp)     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│               Network & Protocol Layer                 │
│                 (mqtt_manager.h / .cpp)                │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│            Hardware Abstraction Layer (HAL)            │
│                 (actuators.h / .cpp)                   │
└────────────────────────────────────────────────────────┘
```

### 2.1 Hardware Abstraction Layer (HAL) - `actuators.h` / `actuators.cpp`
* **Encapsulation:** Isolates raw ESP32 registers, GPIO manipulation, and PWM timers.
* **Servo Integration:** Utilizes `ESP32Servo` which dynamically allocates hardware LEDC PWM timers (Timer 0 - 3) without conflicting with analog inputs or tone generators.
* **Non-Blocking Timer Model:** The buzzer and red LED alert pulse (FR10) operates via delta-timestamp checks (`millis() - _alarmStartTime >= _alarmDurationMs`), completely eliminating blocking calls (`delay()`).

### 2.2 Network & Protocol Layer - `mqtt_manager.h` / `mqtt_manager.cpp`
* **Buffer Allocation:** Sets internal PubSubClient packet buffer to 768 bytes to accommodate JSON payloads with nested actuator and telemetry trees.
* **Resilience:** Implements auto-reconnect logic with exponential backoff timers.
* **LWT (Last Will & Testament):** Automatically registers a retained offline payload with the broker upon connection.

### 2.3 Service Layer - `state_machine.h` / `telemetry.h`
* **Deterministic Parsing:** Safe string-to-enum token matching (`parseGestureString`) with automatic whitespace trimming and uppercase conversion.
* **Instrumentation:** Computes real-time execution latency per command and increments operational counters.
* **Static Memory Safety:** All JSON serialization and deserialization uses `StaticJsonDocument` with compile-time sized pools, preventing heap fragmentation.

---

## 3. Peripheral & Resource Allocation

| Peripheral | Resource Allocated | Pin | Configuration Parameters |
| :--- | :--- | :---: | :--- |
| **Serial Debug** | UART 0 | TX (GPIO 1), RX (GPIO 3) | 115200 Baud, 8N1 |
| **WiFi Radio** | 2.4 GHz 802.11 b/g/n | Internal RF | STA mode, Auto-reconnect enabled |
| **Servo PWM** | LEDC Timer 0 | **GPIO 13** | 50 Hz carrier, 500µs - 2400µs pulse bounds |
| **Green LED** | Digital Output | **GPIO 27** | Push-Pull, 3.3V Logic |
| **Red LED** | Digital Output | **GPIO 26** | Push-Pull, 3.3V Logic |
| **Active Buzzer** | Digital Output | **GPIO 25** | Push-Pull, 3.3V Logic |
| **Telemetry Timer** | Software RTC | Internal `millis()` | 3000 ms cadence |
