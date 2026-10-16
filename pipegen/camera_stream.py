"""
AirControl AI - PipeGen Camera Stream Manager
Manages webcam frame acquisition, format normalization, mirror inversion,
and automatic fallback to synthetic simulation frames when physical camera is absent.
"""

import time
import numpy as np
import cv2
from typing import Tuple, Optional


class CameraStream:
    """
    Acquires video frames from USB camera or synthesizes interactive demo frames.
    """

    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480,
                 fps: int = 30, mock_mode: bool = False):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.target_fps = fps
        self.mock_mode = mock_mode

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_synthetic: bool = False
        self._frame_count: int = 0
        self._start_time: float = time.time()
        self._last_frame_time: float = time.time()

        self._initialize_stream()

    def _initialize_stream(self):
        """Attempts to open physical webcam; falls back to synthetic generator if unavailable."""
        if not self.mock_mode:
            try:
                # Use DirectShow on Windows for fast opening
                self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.device_index)

                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None:
                        self.is_synthetic = False
                        print(f"[CAMERA] Initialized physical camera device {self.device_index} ({self.width}x{self.height} @ {self.target_fps}fps)")
                        return
            except Exception as e:
                print(f"[CAMERA WARNING] Hardware camera initialization failed: {e}")

        # Fallback to synthetic mode
        self.is_synthetic = True
        print(f"[CAMERA INFO] Operating in SYNTHETIC/MOCK video stream mode.")

    def read(self) -> Tuple[bool, np.ndarray]:
        """
        Reads the next frame. Returns (success_bool, frame_bgr).
        Always returns a valid (H, W, 3) image even in headless or mock mode.
        """
        now = time.time()
        self._last_frame_time = now
        self._frame_count += 1

        if not self.is_synthetic and self.cap is not None:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Mirror flip for intuitive user interaction
                frame = cv2.flip(frame, 1)
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                return True, frame

        # Synthetic frame generator
        frame = self._generate_synthetic_frame()
        return True, frame

    def _generate_synthetic_frame(self) -> np.ndarray:
        """
        Generates an animated test background with dynamic hand simulator.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Gradient dark sci-fi background
        for y in range(self.height):
            v = int(25 + 30 * (y / self.height))
            frame[y, :] = [v, v + 10, v + 20]

        # Draw tech grid
        grid_size = 40
        for x in range(0, self.width, grid_size):
            cv2.line(frame, (x, 0), (x, self.height), (45, 55, 65), 1)
        for y in range(0, self.height, grid_size):
            cv2.line(frame, (0, y), (self.width, y), (45, 55, 65), 1)

        # Draw Simulated Hand ROI zone
        rx = int(self.width * 0.45)
        ry = int(self.height * 0.15)
        rw = int(self.width * 0.45)
        rh = int(self.height * 0.70)

        # Draw animated hand silhouette in ROI
        t = time.time()
        cx = rx + rw // 2
        cy = ry + rh // 2

        # Cycle through gestures over time for demonstration:
        cycle_period = 4.0
        phase = int((t % (cycle_period * 5)) // cycle_period)
        gesture_names = ["OPEN_HAND", "FIST", "THUMBS_UP", "THUMBS_DOWN", "VICTORY"]
        active_demo_gesture = gesture_names[phase]

        # Draw synthetic hand shape with skin color
        skin_color = (130, 170, 220)  # BGR skin-like
        palm_radius = 45

        cv2.circle(frame, (cx, cy), palm_radius, skin_color, -1)

        if active_demo_gesture == "OPEN_HAND":
            # 5 fingers
            for angle_deg in [-50, -25, 0, 25, 50]:
                rad = math_rad = np.radians(angle_deg - 90)
                fx = int(cx + 85 * np.cos(rad))
                fy = int(cy + 85 * np.sin(rad))
                cv2.line(frame, (cx, cy), (fx, fy), skin_color, 20)
                cv2.circle(frame, (fx, fy), 10, skin_color, -1)

        elif active_demo_gesture == "FIST":
            # Closed circular fist with knuckles
            cv2.circle(frame, (cx, cy), 52, skin_color, -1)
            cv2.circle(frame, (cx, cy), 48, (110, 150, 200), 2)

        elif active_demo_gesture == "THUMBS_UP":
            # Thumb pointing up
            cv2.circle(frame, (cx, cy), 45, skin_color, -1)
            cv2.line(frame, (cx, cy), (cx, cy - 80), skin_color, 24)
            cv2.circle(frame, (cx, cy - 80), 12, skin_color, -1)

        elif active_demo_gesture == "THUMBS_DOWN":
            # Thumb pointing down
            cv2.circle(frame, (cx, cy), 45, skin_color, -1)
            cv2.line(frame, (cx, cy), (cx, cy + 80), skin_color, 24)
            cv2.circle(frame, (cx, cy + 80), 12, skin_color, -1)

        elif active_demo_gesture == "VICTORY":
            # Index and Middle finger in V
            cv2.circle(frame, (cx, cy), 45, skin_color, -1)
            f1_x, f1_y = int(cx - 25), int(cy - 85)
            f2_x, f2_y = int(cx + 25), int(cy - 85)
            cv2.line(frame, (cx - 10, cy), (f1_x, f1_y), skin_color, 20)
            cv2.line(frame, (cx + 10, cy), (f2_x, f2_y), skin_color, 20)
            cv2.circle(frame, (f1_x, f1_y), 10, skin_color, -1)
            cv2.circle(frame, (f2_x, f2_y), 10, skin_color, -1)

        # Header watermark
        cv2.putText(frame, "AIRCONTROL AI - VIRTUAL CAMERA STREAM", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Demo Gesture: {active_demo_gesture}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        return frame

    def get_fps(self) -> float:
        """Calculates current runtime FPS."""
        elapsed = time.time() - self._start_time
        return self._frame_count / elapsed if elapsed > 0 else 0.0

    def release(self):
        """Releases camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("[CAMERA] Stream released.")
