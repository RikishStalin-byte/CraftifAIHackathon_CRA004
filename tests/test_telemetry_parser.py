"""
AirControl AI - Unit Tests: Telemetry Schema & Parser
Verifies FR11, FR12: Telemetry structure and device status schema validation.
"""

from simulator.esp32_simulator import ESP32HardwareSimulator


class TestTelemetryParser:

    def setup_method(self):
        self.sim = ESP32HardwareSimulator()

    def test_telemetry_dictionary_structure(self):
        telemetry = self.sim.get_telemetry_dict()

        # Check root fields
        required_root_keys = [
            "device_id", "uptime_ms", "wifi_rssi", "free_heap_bytes",
            "actuators", "metrics", "timestamp"
        ]
        for key in required_root_keys:
            assert key in telemetry, f"Missing key: {key}"

        # Check actuator schema
        actuators = telemetry["actuators"]
        assert "green_led" in actuators
        assert "red_led" in actuators
        assert "servo_angle" in actuators
        assert "buzzer_active" in actuators
        assert isinstance(actuators["green_led"], bool)
        assert isinstance(actuators["red_led"], bool)
        assert isinstance(actuators["servo_angle"], int)
        assert isinstance(actuators["buzzer_active"], bool)

        # Check metrics schema
        metrics = telemetry["metrics"]
        assert "commands_received" in metrics
        assert "commands_executed" in metrics
        assert "last_gesture" in metrics
        assert "execution_latency_ms" in metrics
