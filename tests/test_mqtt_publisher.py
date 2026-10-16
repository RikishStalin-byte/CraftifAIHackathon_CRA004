"""
AirControl AI - Unit Tests: MQTT Publisher
Verifies FR4 and Payload Schema compliance.
"""

import json
import re
from unittest.mock import MagicMock
from pipegen.mqtt_publisher import MqttPublisher


class TestMqttPublisher:

    def setup_method(self):
        self.publisher = MqttPublisher(broker="localhost", port=1883)
        self.publisher.client = MagicMock()

    def test_publish_payload_structure(self):
        # Intercept client.publish calls
        published_payloads = []

        def mock_publish(topic, payload, qos):
            published_payloads.append((topic, payload))
            mock_info = MagicMock()
            return mock_info

        self.publisher.client.publish = mock_publish

        gestures_to_test = ["OPEN_HAND", "FIST", "THUMBS_UP", "THUMBS_DOWN", "VICTORY"]
        for g in gestures_to_test:
            success = self.publisher.publish_gesture(g)
            assert success is True

        assert len(published_payloads) == 5

        # Check ISO-8601 timestamp and key matching
        iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        for topic, payload_bytes in published_payloads:
            assert topic == "aircontrol/commands/gesture"
            data = json.loads(payload_bytes)
            assert "gesture" in data
            assert "timestamp" in data
            assert data["gesture"] in gestures_to_test
            assert re.match(iso_regex, data["timestamp"])

    def test_telemetry_callback_invoked(self):
        received_data = []

        def callback(telemetry):
            received_data.append(telemetry)

        self.publisher.on_telemetry_received = callback

        # Simulate incoming telemetry message
        mock_msg = MagicMock()
        mock_msg.topic = "aircontrol/device/telemetry"
        sample_telemetry = {
            "device_id": "TEST_DEVICE",
            "uptime_ms": 1000,
            "wifi_rssi": -60
        }
        mock_msg.payload = json.dumps(sample_telemetry).encode("utf-8")

        self.publisher._on_message(None, None, mock_msg)

        assert len(received_data) == 1
        assert received_data[0]["device_id"] == "TEST_DEVICE"
