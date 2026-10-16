"""
AirControl AI - Integrated System Demo Runner
Launches the ESP32 simulator in a background thread and runs PipeGen to verify
the complete "See -> Decide -> Act" Physical AI pipeline in real time.
"""

import time
import threading
from simulator.esp32_simulator import ESP32HardwareSimulator
from pipegen.main import run_pipegen


def main():
    print("=" * 70)
    print("    AIRCONTROL AI - INTEGRATED END-TO-END PHYSICAL AI DEMO")
    print("=" * 70)
    print("This runner initializes:")
    print("  1. Virtual ESP32 Hardware Simulator (Subscribed to MQTT)")
    print("  2. PipeGen Computer Vision Engine (Captures -> Classifies -> Publishes)")
    print("\nSupported Gestures & Actuations:")
    print("  * OPEN_HAND   -> Green LED ON (GPIO 27)")
    print("  * FIST        -> Green LED OFF (GPIO 27)")
    print("  * THUMBS_UP   -> Servo 90 deg Open (GPIO 13)")
    print("  * THUMBS_DOWN -> Servo 0 deg Closed (GPIO 13)")
    print("  * VICTORY     -> Red LED (GPIO 26) + Buzzer Alert (GPIO 25)")
    print("=" * 70)

    # 1. Start ESP32 Simulator in daemon thread
    sim = ESP32HardwareSimulator()
    sim.start()

    time.sleep(1.5)  # Let simulator connect and establish subscriptions

    try:
        # 2. Run PipeGen (opens GUI window, or fallback stream)
        run_pipegen(mock_camera=True)
    finally:
        print("\n[DEMO] Cleaning up simulator...")
        sim.stop()
        print("[DEMO] Demo ended.")


if __name__ == "__main__":
    main()
