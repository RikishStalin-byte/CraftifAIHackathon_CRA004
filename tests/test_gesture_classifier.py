"""
AirControl AI - Unit Tests: Gesture Classifier
Verifies FR1, FR2, FR3: Gesture detection, discrete classification, and debouncing.
"""

import pytest
import numpy as np
from pipegen.gesture_classifier import GestureClassifier, GestureResult


class TestGestureClassifier:

    def setup_method(self):
        self.classifier = GestureClassifier(
            confidence_threshold=0.70,
            consecutive_frames_required=3,
            cooldown_seconds=0.5
        )

    def test_initialization(self):
        assert self.classifier.confidence_threshold == 0.70
        assert self.classifier.consecutive_frames_required == 3
        assert len(self.classifier.SUPPORTED_GESTURES) == 5

    def test_synthetic_classification_all_gestures(self):
        for gesture in ["OPEN_HAND", "FIST", "THUMBS_UP", "THUMBS_DOWN", "VICTORY"]:
            res = self.classifier.classify_synthetic(gesture, confidence=0.92)
            assert isinstance(res, GestureResult)
            assert res.gesture == gesture
            assert res.confidence == 0.92
            assert res.details.get("synthetic") is True

    def test_invalid_gesture_raises_error(self):
        with pytest.raises(ValueError):
            self.classifier.classify_synthetic("INVALID_GESTURE")

    def test_process_empty_frame(self):
        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result, annotated = self.classifier.process_frame(empty_frame)
        assert isinstance(result, GestureResult)
        assert annotated.shape == (480, 640, 3)

    def test_debouncing_logic(self):
        # 1st raw frame with OPEN_HAND: not confirmed yet (requires 3 consecutive frames)
        r1 = self.classifier._debounce(GestureResult("OPEN_HAND", 0.85))
        assert r1.details.get("debounced") is False

        # 2nd frame
        r2 = self.classifier._debounce(GestureResult("OPEN_HAND", 0.85))
        assert r2.details.get("debounced") is False

        # 3rd frame -> should confirm and debounce
        r3 = self.classifier._debounce(GestureResult("OPEN_HAND", 0.85))
        assert r3.gesture == "OPEN_HAND"
        assert r3.details.get("debounced") is True

    def test_reset_functionality(self):
        self.classifier.classify_synthetic("THUMBS_UP")
        assert self.classifier._last_confirmed_gesture == "THUMBS_UP"
        self.classifier.reset()
        assert self.classifier._last_confirmed_gesture == "NONE"
        assert self.classifier._candidate_count == 0
