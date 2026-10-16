"""
AirControl AI - ESP32 Hardware Simulator
Simulates the physical ESP32 device running FirmGen firmware.
Subscribes to MQTT commands, updates simulated GPIO/PWM/Buzzer hardware states,
and publishes runtime telemetry.
"""

import json
import time
import datetime
import threading
from typing import Dict, Any
import paho.mqtt.client as mqtt

from pipegen.config import load_config


class ESP32HardwareSimulator:
    """
    Virtual ESP32 Dev Board simulator.
    Accurately mirrors firmware state machine and telemetry reporting.
    """

    def __init__(self, broker: str = "broker.emqx.io", port: int = 1883,
                 device_id: str = "ESP32_AIRCONTROL_VIRTUAL"):
        self.broker = broker
        self.port = port
        self.device_id = device_id

        self.command_topic = "aircontrol/commands/gesture"
        self.status_topic = "aircontrol/device/status"
        self.telemetry_topic = "aircontrol/device/telemetry"

        # Hardware Actuator States
        self.green_led: bool = False
        self.red_led: bool = False
        self.servo_angle: int = 0          # 0 degrees = closed, 90 degrees = open
        self.buzzer_active: bool = False

        # Telemetry & Runtime Stats
        self.start_time: float = time.time()
        self.commands_received: int = 0
        self.commands_executed: int = 0
        self.last_gesture: str = "NONE"
        self.last_command_time: float = 0.0
        self.last_latency_ms: int = 0

        self.running: bool = False
        self._telemetry_thread: threading.Thread = None

        # Paho MQTT 2.0
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"{self.device_id}_{int(time.time())}")
        except AttributeError:
            self.client = mqtt.Client(f"{self.device_id}_{int(time.time())}")

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Set MQTT Last Will and Testament (LWT)
        lwt_payload = json.dumps({"device_id": self.device_id, "status": "OFFLINE"})
        self.client.will_set(self.status_topic, lwt_payload, qos=1, retain=True)

    def start(self):
        """Starts the simulated ESP32 device."""
        print("=" * 60)
        print(f"[{self.device_id}] Starting Virtual ESP32 Hardware Simulator...")
        print(f"[{self.device_id}] Connecting to MQTT broker {self.broker}:{self.port}...")
        self.running = True
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

        # Start periodic telemetry publisher thread (every 3 seconds)
        self._telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self._telemetry_thread.start()

    def stop(self):
        """Stops the simulator cleanly."""
        print(f"[{self.device_id}] Stopping simulator...")
        self.running = False
        # Send offline status
        offline_payload = json.dumps({"device_id": self.device_id, "status": "OFFLINE"})
        self.client.publish(self.status_topic, offline_payload, qos=1, retain=True)
        self.client.loop_stop()
        self.client.disconnect()
        print(f"[{self.device_id}] Simulator stopped.")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            print(f"[{self.device_id}] Connected to MQTT broker.")
            # Publish ONLINE status
            online_payload = json.dumps({
                "device_id": self.device_id,
                "status": "ONLINE",
                "firmware_version": "1.0.0-firmgen",
                "simulated": True,
                "ip_address": "192.168.1.105"
            })
            self.client.publish(self.status_topic, online_payload, qos=1, retain=True)

            # Subscribe to gesture command topic
            self.client.subscribe(self.command_topic, qos=1)
            print(f"[{self.device_id}] Subscribed to commands: '{self.command_topic}'")
        else:
            print(f"[{self.device_id} ERROR] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags_or_rc, properties=None):
        print(f"[{self.device_id} WARNING] MQTT connection lost.")

    def _on_message(self, client, userdata, msg):
        """Processes incoming gesture commands from PipeGen."""
        t_recv = time.time()
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            gesture = data.get("gesture", "").upper()
            self.commands_received += 1

            print(f"\n[{self.device_id}] --> COMMAND RECEIVED: '{gesture}'")
            self._execute_gesture_action(gesture)

            # Calculate actuation latency
            self.last_latency_ms = int((time.time() - t_recv) * 1000)
            self.last_gesture = gesture
            self.last_command_time = time.time()
            self.commands_executed += 1

            # Immediately publish updated state
            self.publish_telemetry()

        except Exception as e:
            print(f"[{self.device_id} ERROR] Failed to process command: {e}")

    def _execute_gesture_action(self, gesture: str):
        """Executes hardware actuation according to FR6 - FR10."""
        if gesture == "OPEN_HAND":
            # FR6: Turn ON Green LED
            self.green_led = True
            print(f"[{self.device_id} ACTUATION] GPIO27 (GREEN LED) -> HIGH [ON] (Open Hand detected)")

        elif gesture == "FIST":
            # FR7: Turn OFF Green LED
            self.green_led = False
            print(f"[{self.device_id} ACTUATION] GPIO27 (GREEN LED) -> LOW [OFF] (Fist detected)")

        elif gesture == "THUMBS_UP":
            # FR8: Rotate servo to 90 degrees (Open position)
            self.servo_angle = 90
            print(f"[{self.device_id} ACTUATION] GPIO13 (SERVO PWM) -> 90 DEGREES [OPEN] (Thumbs Up detected)")

        elif gesture == "THUMBS_DOWN":
            # FR9: Rotate servo to 0 degrees (Closed position)
            self.servo_angle = 0
            print(f"[{self.device_id} ACTUATION] GPIO13 (SERVO PWM) -> 0 DEGREES [CLOSED] (Thumbs Down detected)")

        elif gesture == "VICTORY":
            # FR10: Activate Red LED and Buzzer
            print(f"[{self.device_id} ACTUATION] GPIO26 (RED LED) & GPIO25 (BUZZER) -> ACTIVATED! (Victory detected)")
            self._trigger_alarm_alert()

        else:
            print(f"[{self.device_id} WARNING] Unknown gesture command '{gesture}'. No action taken.")

    def _trigger_alarm_alert(self):
        """Non-blocking simulated alarm alert pulse (Red LED + Active Buzzer)."""
        def _pulse():
            self.red_led = True
            self.buzzer_active = True
            print(f"[{self.device_id} HARDWARE] Buzzer BEEPING & Red LED ON (Alert Mode)")
            time.sleep(1.2)  # Active alert pulse duration
            self.red_led = False
            self.buzzer_active = False
            print(f"[{self.device_id} HARDWARE] Alert pulse complete -> Red LED OFF, Buzzer OFF")
            self.publish_telemetry()

        threading.Thread(target=_pulse, daemon=True).start()

    def get_telemetry_dict(self) -> Dict[str, Any]:
        """Assembles telemetry data payload (FR11, FR12)."""
        uptime_ms = int((time.time() - self.start_time) * 1000)
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "device_id": self.device_id,
            "uptime_ms": uptime_ms,
            "wifi_rssi": -55,
            "free_heap_bytes": 172400,
            "actuators": {
                "green_led": self.green_led,
                "red_led": self.red_led,
                "servo_angle": self.servo_angle,
                "buzzer_active": self.buzzer_active
            },
            "metrics": {
                "commands_received": self.commands_received,
                "commands_executed": self.commands_executed,
                "last_gesture": self.last_gesture,
                "last_command_time_ms": int(self.last_command_time * 1000) if self.last_command_time else 0,
                "execution_latency_ms": self.last_latency_ms
            },
            "timestamp": now_iso
        }

    def publish_telemetry(self):
        """Transmits telemetry JSON to MQTT."""
        data = self.get_telemetry_dict()
        payload = json.dumps(data)
        self.client.publish(self.telemetry_topic, payload, qos=0)

    def _telemetry_loop(self):
        """Background heartbeat telemetry publisher."""
        while self.running:
            try:
                self.publish_telemetry()
            except Exception:
                pass
            time.sleep(3.0)


if __name__ == "__main__":
    cfg = load_config()
    sim = ESP32HardwareSimulator(
        broker=cfg["mqtt"]["broker"],
        port=cfg["mqtt"]["port"]
    )
    sim.start()
    try:
        print("[SIMULATOR] ESP32 Simulator running. Waiting for PipeGen gesture commands. Press Ctrl+C to terminate.")
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        sim.stop()
