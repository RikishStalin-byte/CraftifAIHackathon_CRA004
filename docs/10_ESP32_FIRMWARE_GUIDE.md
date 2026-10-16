# AirControl AI - ESP32 Firmware Build & Flashing Guide

**Document Version:** 1.0.0  
**Target Hardware:** ESP32-WROOM-32 / ESP32-DevKitC  
**Authoring Methodology:** FirmGen Best Practices  

---

## 1. Hardware Bill of Materials (BOM)

| Item | Component Specification | Quantity | Recommended Role |
| :---: | :--- | :---: | :--- |
| **1** | ESP32 Development Board (ESP-WROOM-32) | 1 | Microcontroller Core |
| **2** | Green 5mm LED | 1 | Power / Status Indicator (FR6, FR7) |
| **3** | Red 5mm LED | 1 | Alarm / Strobe Indicator (FR10) |
| **4** | Active 5V / 3.3V Buzzer | 1 | Audible Warning Chime (FR10) |
| **5** | SG90 or MG90S Micro Servo Motor | 1 | Mechanical Barrier / Latch (FR8, FR9) |
| **6** | 220 Ohm Carbon Film Resistors (1/4W) | 2 | Current Limiting for LEDs |
| **7** | Breadboard & Jumper Wires | 1 Set | Circuit Interconnects |
| **8** | Micro-USB Cable (Data Capable) | 1 | Power & Firmware Flashing |

---

## 2. Pin Connection Diagram

Connect the components to the ESP32 development board according to this layout:

```
ESP32 Pin      Component Pin             Wiring Notes
──────────────────────────────────────────────────────────────────
GPIO 27 ──────> [220Ω Resistor] ─> Green LED Anode (+)  (Cathode to GND)
GPIO 26 ──────> [220Ω Resistor] ─> Red LED Anode (+)    (Cathode to GND)
GPIO 25 ──────> Buzzer (+) Terminal                    (Buzzer (-) to GND)
GPIO 13 ──────> SG90 Orange (PWM Signal Wire)
VIN / 5V ─────> SG90 Red (Power Wire)
GND     ──────> SG90 Brown (Ground) & Common Rail
```

---

## 3. Building & Flashing with PlatformIO (Recommended)

PlatformIO is the recommended development environment for reproducible embedded builds.

### 3.1 Prerequisites
- [VS Code](https://code.visualstudio.com/) with the **PlatformIO IDE** extension installed, or the PlatformIO Core CLI (`pip install platformio`).

### 3.2 Compilation & Upload Commands

1. Open a terminal in the `firmware/` directory:
   ```powershell
   cd "C:\Users\RIKISH STALIN\OneDrive\Documents\Desktop\AirControl AI\firmware"
   ```

2. Configure WiFi Credentials in `include/config.h`:
   ```cpp
   #define WIFI_SSID       "Your_WiFi_Network"
   #define WIFI_PASSWORD   "Your_WiFi_Password"
   ```

3. Build the firmware binary:
   ```powershell
   pio run
   ```

4. Connect your ESP32 via USB and flash the board:
   ```powershell
   pio run --target upload
   ```

5. Open the Serial Monitor (115200 baud):
   ```powershell
   pio device monitor --speed 115200
   ```

---

## 4. Building with Arduino IDE (Alternative)

If using the Arduino IDE:
1. Open Arduino IDE and install the **esp32** board package via the Boards Manager.
2. Install the following libraries via the Library Manager:
   - `PubSubClient` by Nick O'Leary (v2.8+)
   - `ArduinoJson` by Benoit Blanchon (v6.21+)
   - `ESP32Servo` by Kevin Harrington (v1.1+)
3. Create a sketch named `firmware.ino` containing the code from `src/main.cpp`.
4. Copy the headers from `include/` and source files from `src/` into the sketch folder.
5. Select **ESP32 Dev Module**, choose your COM port, and click **Upload**.

---

## 5. Serial Console Output Example

Upon successful boot, the ESP32 outputs clean diagnostic telemetry:

```
=====================================================
         AIRCONTROL AI - ESP32 FIRMGEN FIRMWARE      
=====================================================
Firmware Version : 1.0.0-firmgen
Hardware ID      : ESP32_AIRCONTROL_DEV01
Actuator Pins    : Green=27, Red=26, Buzz=25, Servo=13
=====================================================
[ACTUATORS] Hardware subsystem initialized successfully.
[ACTUATORS] Green LED (GPIO27), Red LED (GPIO26), Buzzer (GPIO25), Servo (GPIO13)
[WIFI] Connecting to SSID: 'Office_Guest_WiFi'....
[WIFI] Connected! IP Address: 192.168.1.105 (RSSI: -54 dBm)
[MQTT] Connecting to broker broker.emqx.io:1883 as 'ESP32_AirControl_FirmGen'...
[MQTT] Connected successfully!
[MQTT] Subscribed to command topic: 'aircontrol/commands/gesture'
[TELEMETRY] Subsystem initialized.
[SETUP] ESP32 Ready to receive gesture commands.

[MQTT RECV] Topic: aircontrol/commands/gesture | Payload: {"gesture":"THUMBS_UP","timestamp":"2026-10-16T18:00:00Z"}
[ACTUATION] Servo (GPIO13) -> 90 degrees
[STATE_MACHINE] Executed 'THUMBS_UP' in 2 ms (Total Executed: 1)
```
