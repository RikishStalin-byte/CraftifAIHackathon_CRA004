"""
AirControl AI - PipeGen MQTT Publisher & Telemetry Monitor
Handles MQTT communication between computer vision pipeline and ESP32 hardware.
Publishes gesture commands and receives ESP32 telemetry.
"""

import json
import time
import datetime
import uuid
from typing import Optional, Dict, Any, Callable
import paho.mqtt.client as mqtt


class MqttPublisher:
    """
    Manages robust MQTT connection, payload serialization, and telemetry monitoring.
    """

    def __init__(self, broker: str = "broker.emqx.io", port: int = 1883,
                 keepalive: int = 60,
                 client_id_prefix: str = "AirControl_PipeGen_",
                 command_topic: str = "aircontrol/commands/gesture",
                 status_topic: str = "aircontrol/device/status",
                 telemetry_topic: str = "aircontrol/device/telemetry"):

        self.broker = broker
        self.port = port
        self.keepalive = keepalive
        self.client_id = f"{client_id_prefix}{uuid.uuid4().hex[:6]}"
        self.command_topic = command_topic
        self.status_topic = status_topic
        self.telemetry_topic = telemetry_topic

        self.connected = False
        self.last_published_time: Optional[float] = None
        self.last_published_gesture: Optional[str] = None
        self.total_published: int = 0
        self.latest_telemetry: Dict[str, Any] = {}
        self.latest_status: Dict[str, Any] = {}

        # Callbacks
        self.on_telemetry_received: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_status_received: Optional[Callable[[Dict[str, Any]], None]] = None

        # Paho MQTT 2.0 compatibility
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.client_id)
        except AttributeError:
            self.client = mqtt.Client(self.client_id)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

    def start(self, async_connect: bool = True):
        """Connects to MQTT broker and starts background loop."""
        try:
            print(f"[MQTT] Connecting to broker {self.broker}:{self.port} as {self.client_id}...")
            self.client.connect_async(self.broker, self.port, self.keepalive)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTT ERROR] Connection initiation failed: {e}")

    def stop(self):
        """Disconnects and stops background loop."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            print("[MQTT] Disconnected cleanly.")
        except Exception as e:
            print(f"[MQTT ERROR] Disconnect failed: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when broker acknowledges connection."""
        # Handle both integer rc and ReasonCode objects
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            self.connected = True
            print(f"[MQTT] Connected successfully to {self.broker}")
            # Subscribe to hardware status & telemetry topics
            client.subscribe([(self.status_topic, 1), (self.telemetry_topic, 0)])
            print(f"[MQTT] Subscribed to {self.status_topic} & {self.telemetry_topic}")
        else:
            self.connected = False
            print(f"[MQTT ERROR] Connection refused with code: {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags_or_rc, properties=None):
        self.connected = False
        print("[MQTT WARNING] Disconnected from broker. Auto-reconnecting in background...")

    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        pass

    def _on_message(self, client, userdata, msg):
        """Handles incoming messages from ESP32."""
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            if msg.topic == self.telemetry_topic:
                self.latest_telemetry = data
                if self.on_telemetry_received:
                    self.on_telemetry_received(data)
            elif msg.topic == self.status_topic:
                self.latest_status = data
                if self.on_status_received:
                    self.on_status_received(data)
        except Exception as e:
            print(f"[MQTT WARNING] Error parsing incoming message from {msg.topic}: {e}")

    def publish_gesture(self, gesture: str) -> bool:
        """
        Serializes and transmits gesture command.
        Follows required payload structure:
        {
          "gesture": "THUMBS_UP",
          "timestamp": "2026-10-16T18:00:00Z"
        }
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "gesture": gesture,
            "timestamp": now_iso
        }
        payload_bytes = json.dumps(payload)

        try:
            info = self.client.publish(self.command_topic, payload_bytes, qos=1)
            self.last_published_time = time.time()
            self.last_published_gesture = gesture
            self.total_published += 1
            print(f"[MQTT COMMAND SENT] Topic: {self.command_topic} -> {payload_bytes}")
            return True
        except Exception as e:
            print(f"[MQTT ERROR] Failed to publish gesture command: {e}")
            return False
