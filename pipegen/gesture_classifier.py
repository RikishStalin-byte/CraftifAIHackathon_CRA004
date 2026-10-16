"""
AirControl AI - PipeGen Gesture Classifier
Implements computer vision hand detection, feature extraction, and discrete gesture classification.
Aligned with the Physical AI "Decide" stage.
"""

import time
import math
import numpy as np
import cv2
from typing import Tuple, Optional, Dict, Any, List


class GestureResult:
    """Encapsulates the classification outcome of a single frame."""
    def __init__(self, gesture: str, confidence: float, details: Optional[Dict[str, Any]] = None):
        self.gesture = gesture          # OPEN_HAND, FIST, THUMBS_UP, THUMBS_DOWN, VICTORY, NONE
        self.confidence = confidence    # 0.0 to 1.0
        self.details = details or {}
        self.timestamp = time.time()

    def __repr__(self) -> str:
        return f"<GestureResult {self.gesture} (conf: {self.confidence:.2f})>"


class GestureClassifier:
    """
    Robust real-time hand gesture classifier.
    Combines skin-color chrominance thresholding, convex hull defect analysis,
    and geometric feature vectors to classify hand gestures.
    """

    SUPPORTED_GESTURES = [
        "OPEN_HAND",
        "FIST",
        "THUMBS_UP",
        "THUMBS_DOWN",
        "VICTORY"
    ]

    def __init__(self, confidence_threshold: float = 0.70,
                 consecutive_frames_required: int = 5,
                 cooldown_seconds: float = 1.0):
        self.confidence_threshold = confidence_threshold
        self.consecutive_frames_required = consecutive_frames_required
        self.cooldown_seconds = cooldown_seconds

        # Debounce tracking
        self._current_candidate: Optional[str] = None
        self._candidate_count: int = 0
        self._last_confirmed_gesture: str = "NONE"
        self._last_emission_time: float = 0.0

    def reset(self):
        """Resets debouncing and classification state."""
        self._current_candidate = None
        self._candidate_count = 0
        self._last_confirmed_gesture = "NONE"
        self._last_emission_time = 0.0

    def process_frame(self, frame: np.ndarray, roi_box: Optional[Tuple[int, int, int, int]] = None) -> Tuple[GestureResult, np.ndarray]:
        """
        Processes a BGR camera frame and returns (GestureResult, annotated_frame).
        roi_box: Optional (x, y, w, h) bounding box for hand interaction zone.
        """
        h, w = frame.shape[:2]
        if roi_box is None:
            # Default to center-right region (typical user interaction zone)
            rw, rh = int(w * 0.5), int(h * 0.7)
            rx = int(w * 0.45)
            ry = int(h * 0.15)
            roi_box = (rx, ry, rw, rh)

        rx, ry, rw, rh = roi_box
        roi = frame[ry:ry+rh, rx:rx+rw]

        raw_result, mask, contour = self._classify_roi(roi)

        # Draw ROI box and hand contours on the frame
        annotated = frame.copy()
        cv2.rectangle(annotated, (rx, ry), (rx + rw, ry + rh), (255, 200, 0), 2)
        cv2.putText(annotated, "HAND INTERACTION ZONE", (rx, ry - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1, cv2.LINE_AA)

        if contour is not None:
            # Shift contour back to full frame coordinates
            shifted_contour = contour + np.array([rx, ry])
            cv2.drawContours(annotated, [shifted_contour], -1, (0, 255, 0), 2)

        # Apply temporal debouncing and cooldown
        debounced_result = self._debounce(raw_result)
        return debounced_result, annotated

    def _classify_roi(self, roi: np.ndarray) -> Tuple[GestureResult, np.ndarray, Optional[np.ndarray]]:
        """Analyzes ROI pixels to extract geometric features and determine gesture."""
        if roi is None or roi.size == 0:
            return GestureResult("NONE", 0.0), np.zeros((10, 10), dtype=np.uint8), None

        # Convert to HSV and YCrCb for robust illumination-resilient skin extraction
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)

        # HSV Skin range
        lower_hsv = np.array([0, 20, 70], dtype=np.uint8)
        upper_hsv = np.array([25, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        # YCrCb Skin range
        lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
        upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        # Combined skin mask
        combined_mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)

        # Morphological operations to suppress noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_clean = cv2.GaussianBlur(mask_clean, (5, 5), 0)

        # Find largest contour
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return GestureResult("NONE", 0.0), mask_clean, None

        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)

        # Minimum area threshold (filter out minor skin noise)
        roi_area = roi.shape[0] * roi.shape[1]
        if area < 0.04 * roi_area:
            return GestureResult("NONE", 0.0), mask_clean, None

        # Extract geometric features
        hull = cv2.convexHull(max_contour, returnPoints=False)
        hull_points = cv2.convexHull(max_contour, returnPoints=True)

        solidity = float(area) / cv2.contourArea(hull_points) if cv2.contourArea(hull_points) > 0 else 0.0
        x, y, bw, bh = cv2.boundingRect(max_contour)
        aspect_ratio = float(bw) / bh if bh > 0 else 1.0

        # Convexity defects (fingers create valleys)
        defects_count = 0
        extended_fingers = 0
        defect_depths = []

        # Find centroid of hand
        M = cv2.moments(max_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + bw // 2, y + bh // 2

        if hull is not None and len(hull) > 3:
            try:
                defects = cv2.convexityDefects(max_contour, hull)
                if defects is not None:
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        start = tuple(max_contour[s][0])
                        end = tuple(max_contour[e][0])
                        far = tuple(max_contour[f][0])
                        depth = d / 256.0  # depth in pixels
                        defect_depths.append(depth)

                        # Check angle between start-far and end-far
                        a = math.dist(start, end)
                        b = math.dist(far, start)
                        c = math.dist(far, end)
                        if b > 0 and c > 0:
                            angle = math.acos(max(-1.0, min(1.0, (b**2 + c**2 - a**2) / (2 * b * c))))
                            # Acute angles with sufficient depth indicate finger separations
                            if angle < math.pi / 2.0 and depth > 15:
                                defects_count += 1
                                if start[1] < cy:  # Points above centroid
                                    extended_fingers += 1
            except Exception:
                pass

        details = {
            "area": area,
            "solidity": solidity,
            "aspect_ratio": aspect_ratio,
            "defects_count": defects_count,
            "centroid": (cx, cy),
            "bounding_box": (x, y, bw, bh)
        }

        # Classification decision rules
        # 1. FIST: high solidity, low defects, compact bounding box
        if solidity > 0.85 and defects_count <= 1:
            confidence = min(0.98, solidity)
            return GestureResult("FIST", confidence, details), mask_clean, max_contour

        # 2. OPEN HAND: 3-5 defects, lower solidity, broad aspect ratio
        if defects_count >= 3 and solidity < 0.75:
            confidence = min(0.95, 0.70 + (defects_count * 0.05))
            return GestureResult("OPEN_HAND", confidence, details), mask_clean, max_contour

        # 3. VICTORY SIGN: exactly 2 extended fingers, V-shape
        if defects_count == 1 or defects_count == 2:
            # Check aspect ratio & height dominance
            if 0.60 <= solidity <= 0.82 and bh > bw:
                confidence = 0.88
                return GestureResult("VICTORY", confidence, details), mask_clean, max_contour

        # 4. THUMBS UP / THUMBS DOWN: 1 prominent protrusion
        if defects_count <= 2 and solidity < 0.88:
            # Evaluate top vs bottom protrusion relative to centroid
            extreme_top = tuple(max_contour[max_contour[:, :, 1].argmin()][0])
            extreme_bottom = tuple(max_contour[max_contour[:, :, 1].argmax()][0])

            top_dist = cy - extreme_top[1]
            bot_dist = extreme_bottom[1] - cy

            if top_dist > bot_dist * 1.35 and top_dist > bh * 0.45:
                confidence = 0.85
                return GestureResult("THUMBS_UP", confidence, details), mask_clean, max_contour
            elif bot_dist > top_dist * 1.35 and bot_dist > bh * 0.45:
                confidence = 0.85
                return GestureResult("THUMBS_DOWN", confidence, details), mask_clean, max_contour

        # Default fallback
        return GestureResult("NONE", 0.0, details), mask_clean, max_contour

    def _debounce(self, raw: GestureResult) -> GestureResult:
        """
        Applies temporal hysteresis and cooldown to avoid false transitions.
        """
        now = time.time()

        if raw.confidence < self.confidence_threshold or raw.gesture == "NONE":
            # Decrement candidate counter gradually
            self._candidate_count = max(0, self._candidate_count - 1)
            return GestureResult(self._last_confirmed_gesture, 0.5, {"debounced": False, "raw": raw.gesture})

        if raw.gesture == self._current_candidate:
            self._candidate_count += 1
        else:
            self._current_candidate = raw.gesture
            self._candidate_count = 1

        if self._candidate_count >= self.consecutive_frames_required:
            if (raw.gesture != self._last_confirmed_gesture) or (now - self._last_emission_time > self.cooldown_seconds):
                self._last_confirmed_gesture = raw.gesture
                self._last_emission_time = now
                return GestureResult(raw.gesture, raw.confidence, {"debounced": True, "raw": raw.gesture})

        return GestureResult(self._last_confirmed_gesture, raw.confidence, {"debounced": False, "raw": raw.gesture})

    def classify_synthetic(self, gesture_name: str, confidence: float = 0.95) -> GestureResult:
        """
        Provides direct synthetic gesture classification for testing and simulation.
        """
        if gesture_name not in self.SUPPORTED_GESTURES:
            raise ValueError(f"Unsupported gesture: {gesture_name}. Must be one of {self.SUPPORTED_GESTURES}")
        raw = GestureResult(gesture_name, confidence, {"synthetic": True})
        self._last_confirmed_gesture = gesture_name
        self._last_emission_time = time.time()
        return raw
