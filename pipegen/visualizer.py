"""
AirControl AI - PipeGen Real-Time Visualizer
Renders an interactive Heads-Up Display (HUD) overlay depicting the
Physical AI "See -> Decide -> Act" pipeline and live ESP32 telemetry.
"""

import time
import cv2
import numpy as np
from typing import Dict, Any, Optional
from pipegen.gesture_classifier import GestureResult


class VisualizerHUD:
    """
    Renders high-contrast telemetry and status overlays on OpenCV display frames.
    """

    ACTION_MAP = {
        "OPEN_HAND": "Turn ON Green LED",
        "FIST": "Turn OFF Green LED",
        "THUMBS_UP": "Rotate Servo to Open (90°)",
        "THUMBS_DOWN": "Rotate Servo to Closed (0°)",
        "VICTORY": "Activate Red LED & Buzzer Alarm",
        "NONE": "Idle / Waiting for Gesture"
    }

    ACTION_COLORS = {
        "OPEN_HAND": (0, 255, 0),        # Green
        "FIST": (180, 180, 180),         # Gray
        "THUMBS_UP": (255, 180, 0),       # Cyan/Blue
        "THUMBS_DOWN": (255, 120, 0),     # Deep Sky
        "VICTORY": (0, 0, 255),          # Red
        "NONE": (120, 120, 120)          # Dim Gray
    }

    def render(self, frame: np.ndarray, result: GestureResult,
               fps: float, mqtt_connected: bool,
               last_published_gesture: Optional[str],
               last_published_time: Optional[float],
               telemetry: Dict[str, Any]) -> np.ndarray:

        h, w = frame.shape[:2]
        canvas = frame.copy()

        # Top Banner
        cv2.rectangle(canvas, (0, 0), (w, 50), (20, 24, 30), -1)
        cv2.putText(canvas, "AirControl AI  |  Physical AI Gesture System", (15, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        # Connection status pill
        conn_text = "MQTT: CONNECTED" if mqtt_connected else "MQTT: DISCONNECTED"
        conn_color = (0, 220, 0) if mqtt_connected else (0, 0, 220)
        cv2.putText(canvas, conn_text, (w - 210, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, conn_color, 2, cv2.LINE_AA)

        # Left Panel: See -> Decide -> Act Pipeline Flow
        panel_w = 320
        panel_h = 390
        px, py = 15, 65

        overlay = canvas.copy()
        cv2.rectangle(overlay, (px, py), (px + panel_w, py + panel_h), (15, 18, 24), -1)
        cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
        cv2.rectangle(canvas, (px, py), (px + panel_w, py + panel_h), (60, 70, 85), 1)

        # Pipeline Stage 1: SEE
        cv2.putText(canvas, "[1] SEE: Video Feed", (px + 12, py + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"Frame Rate: {fps:.1f} FPS  |  {w}x{h}", (px + 18, py + 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        # Pipeline Stage 2: DECIDE
        cv2.putText(canvas, "[2] DECIDE: PipeGen Classifier", (px + 12, py + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2, cv2.LINE_AA)

        gesture_color = self.ACTION_COLORS.get(result.gesture, (255, 255, 255))
        cv2.putText(canvas, f"Gesture: {result.gesture}", (px + 18, py + 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, gesture_color, 2, cv2.LINE_AA)

        # Confidence Bar
        bar_x, bar_y = px + 18, py + 125
        bar_w, bar_h = 180, 10
        cv2.rectangle(canvas, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        fill_w = int(bar_w * max(0.0, min(1.0, result.confidence)))
        cv2.rectangle(canvas, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), gesture_color, -1)
        cv2.putText(canvas, f"{int(result.confidence * 100)}%", (bar_x + bar_w + 8, bar_y + 9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Pipeline Stage 3: ACT
        cv2.putText(canvas, "[3] ACT: ESP32 Hardware Action", (px + 12, py + 165),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2, cv2.LINE_AA)
        action_desc = self.ACTION_MAP.get(result.gesture, "Idle")
        cv2.putText(canvas, action_desc, (px + 18, py + 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        # Last Command Sent
        cv2.line(canvas, (px + 10, py + 210), (px + panel_w - 10, py + 210), (50, 60, 75), 1)
        cv2.putText(canvas, "LAST MQTT COMMAND DISPATCHED:", (px + 12, py + 230),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1)

        if last_published_gesture:
            age = time.time() - (last_published_time or time.time())
            cv2.putText(canvas, f">> {last_published_gesture} ({age:.1f}s ago)", (px + 18, py + 252),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1, cv2.LINE_AA)
        else:
            cv2.putText(canvas, ">> No commands published yet", (px + 18, py + 252),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

        # ESP32 Telemetry Box
        cv2.line(canvas, (px + 10, py + 270), (px + panel_w - 10, py + 270), (50, 60, 75), 1)
        cv2.putText(canvas, "ESP32 RUNTIME TELEMETRY:", (px + 12, py + 290),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1)

        if telemetry:
            act = telemetry.get("actuators", {})
            metrics = telemetry.get("metrics", {})
            g_led = "ON" if act.get("green_led") else "OFF"
            r_led = "ON" if act.get("red_led") else "OFF"
            servo = act.get("servo_angle", 0)
            buzz = "ACTIVE" if act.get("buzzer_active") else "OFF"
            rssi = telemetry.get("wifi_rssi", -60)
            heap = telemetry.get("free_heap_bytes", 0) // 1024

            cv2.putText(canvas, f"Green LED: {g_led}  |  Red LED: {r_led}", (px + 18, py + 310),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
            cv2.putText(canvas, f"Servo: {servo} deg  |  Buzzer: {buzz}", (px + 18, py + 330),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
            cv2.putText(canvas, f"WiFi RSSI: {rssi} dBm | Heap: {heap} KB", (px + 18, py + 350),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
            cv2.putText(canvas, f"Executed Count: {metrics.get('commands_executed', 0)}", (px + 18, py + 370),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 180), 1)
        else:
            cv2.putText(canvas, "Awaiting ESP32 Telemetry Ping...", (px + 18, py + 325),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140, 140, 140), 1)

        # Footer Instruction Bar
        cv2.rectangle(canvas, (0, h - 25), (w, h), (20, 24, 30), -1)
        cv2.putText(canvas, "Press 'Q' to Exit  |  '1': Open Hand  '2': Fist  '3': Thumbs Up  '4': Thumbs Down  '5': Victory",
                    (15, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

        return canvas
