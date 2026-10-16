"""
AirControl AI - End-to-End Integration Tests
Validates the complete "See -> Decide -> Act" Physical AI flow:
FR6 (Open Hand -> Green LED ON)
FR7 (Fist -> Green LED OFF)
FR8 (Thumbs Up -> Servo 90)
FR9 (Thumbs Down -> Servo 0)
FR10 (Victory -> Red LED + Buzzer)
"""

import time
from simulator.esp32_simulator import ESP32HardwareSimulator
from pipegen.gesture_classifier import GestureClassifier


class TestEndToEndPhysicalAI:

    def setup_method(self):
        self.sim = ESP32HardwareSimulator()
        self.classifier = GestureClassifier()

    def test_open_hand_actuation(self):
        # 1. Decide: Classifier recognizes OPEN_HAND
        res = self.classifier.classify_synthetic("OPEN_HAND")
        assert res.gesture == "OPEN_HAND"

        # 2. Act: Hardware executes command
        self.sim._execute_gesture_action(res.gesture)

        # 3. Verify hardware state
        assert self.sim.green_led is True

    def test_fist_actuation(self):
        # First turn on green led
        self.sim.green_led = True

        # Decide: Classifier recognizes FIST
        res = self.classifier.classify_synthetic("FIST")
        assert res.gesture == "FIST"

        # Act: Execute
        self.sim._execute_gesture_action(res.gesture)

        # Verify state
        assert self.sim.green_led is False

    def test_thumbs_up_actuation(self):
        res = self.classifier.classify_synthetic("THUMBS_UP")
        assert res.gesture == "THUMBS_UP"

        self.sim._execute_gesture_action(res.gesture)
        assert self.sim.servo_angle == 90

    def test_thumbs_down_actuation(self):
        self.sim.servo_angle = 90

        res = self.classifier.classify_synthetic("THUMBS_DOWN")
        assert res.gesture == "THUMBS_DOWN"

        self.sim._execute_gesture_action(res.gesture)
        assert self.sim.servo_angle == 0

    def test_victory_actuation(self):
        res = self.classifier.classify_synthetic("VICTORY")
        assert res.gesture == "VICTORY"

        self.sim._execute_gesture_action(res.gesture)
        # Give thread a few ms to start
        time.sleep(0.1)
        assert self.sim.red_led is True
        assert self.sim.buzzer_active is True

    def test_full_sequence_lifecycle(self):
        sequence = ["OPEN_HAND", "THUMBS_UP", "VICTORY", "THUMBS_DOWN", "FIST"]

        for gesture in sequence:
            res = self.classifier.classify_synthetic(gesture)
            self.sim._execute_gesture_action(res.gesture)

        # In final state:
        assert self.sim.green_led is False
        assert self.sim.servo_angle == 0
