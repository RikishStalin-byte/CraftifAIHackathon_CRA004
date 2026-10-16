"""
AirControl AI - PipeGen Computer Vision Main Application
Coordinates the "See -> Decide -> Act" workflow:
  1. SEE: Live video capture via camera or synthetic stream.
  2. DECIDE: Real-time hand gesture classification and debounce.
  3. ACT: MQTT command dispatch to ESP32 firmware.
"""

import os
import sys
import time
import argparse
import cv2
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipegen.config import load_config
from pipegen.camera_stream import CameraStream
from pipegen.gesture_classifier import GestureClassifier
from pipegen.mqtt_publisher import MqttPublisher
from pipegen.visualizer import VisualizerHUD


def run_pipegen(config_path: Optional[str] = None,
                headless: bool = False,
                mock_camera: bool = False,
                max_iterations: Optional[int] = None,
                test_gesture: Optional[str] = None):
    """
    Main execution loop for PipeGen.
    """
    cfg = load_config(config_path)

    print("=" * 65)
    print("           AIRCONTROL AI - PIPEGEN SYSTEM STARTING           ")
    print("=" * 65)
    print(f"MQTT Broker : {cfg['mqtt']['broker']}:{cfg['mqtt']['port']}")
    print(f"Command Topic: {cfg['mqtt']['topics']['command']}")
    print(f"Telemetry Topic: {cfg['mqtt']['topics']['telemetry']}")
    print(f"Headless Mode: {headless}")
    print("=" * 65)

    # 1. Initialize MQTT
    mqtt_mgr = MqttPublisher(
        broker=cfg["mqtt"]["broker"],
        port=cfg["mqtt"]["port"],
        keepalive=cfg["mqtt"]["keepalive"],
        command_topic=cfg["mqtt"]["topics"]["command"],
        status_topic=cfg["mqtt"]["topics"]["status"],
        telemetry_topic=cfg["mqtt"]["topics"]["telemetry"]
    )
    mqtt_mgr.start()

    # 2. Initialize Camera Stream
    stream = CameraStream(
        device_index=cfg["camera"]["device_index"],
        width=cfg["camera"]["frame_width"],
        height=cfg["camera"]["frame_height"],
        fps=cfg["camera"]["fps"],
        mock_mode=mock_camera or cfg["camera"]["mock_mode"]
    )

    # 3. Initialize Classifier
    classifier = GestureClassifier(
        confidence_threshold=cfg["gesture"]["confidence_threshold"],
        consecutive_frames_required=cfg["gesture"]["consecutive_frames_required"],
        cooldown_seconds=cfg["gesture"]["cooldown_seconds"]
    )

    # 4. Initialize Visualizer HUD
    hud = VisualizerHUD()

    iteration = 0
    last_sent_gesture = None
    window_name = "AirControl AI - PipeGen Gesture Interface"

    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        while True:
            iteration += 1
            if max_iterations is not None and iteration > max_iterations:
                print(f"[PIPEGEN] Reached maximum requested iterations ({max_iterations}). Exiting loop.")
                break

            # --- SEE ---
            ret, frame = stream.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # --- DECIDE ---
            if test_gesture:
                # Direct test injection
                result = classifier.classify_synthetic(test_gesture)
                annotated = frame
            else:
                result, annotated = classifier.process_frame(frame)

            # Check if this frame triggered a new confirmed debounced gesture
            if result.gesture in classifier.SUPPORTED_GESTURES:
                # Check debounced trigger flag
                is_debounced_trigger = result.details.get("debounced", False) or result.details.get("synthetic", False)
                if is_debounced_trigger and (result.gesture != last_sent_gesture):
                    # --- ACT TRIGGER (MQTT) ---
                    print(f"\n[DECIDE -> ACT] Confirmed Gesture: '{result.gesture}' -> Dispatching to ESP32...")
                    mqtt_mgr.publish_gesture(result.gesture)
                    last_sent_gesture = result.gesture

            # Render HUD
            fps = stream.get_fps()
            display_frame = hud.render(
                frame=annotated,
                result=result,
                fps=fps,
                mqtt_connected=mqtt_mgr.connected,
                last_published_gesture=mqtt_mgr.last_published_gesture,
                last_published_time=mqtt_mgr.last_published_time,
                telemetry=mqtt_mgr.latest_telemetry
            )

            # Interactive Display (if not headless)
            if not headless:
                cv2.imshow(window_name, display_frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("[PIPEGEN] User exit requested.")
                    break
                # Manual keypad overrides for rapid testing:
                elif key == ord('1'):
                    print("[MANUAL TEST] Triggering OPEN_HAND")
                    mqtt_mgr.publish_gesture("OPEN_HAND")
                    last_sent_gesture = "OPEN_HAND"
                elif key == ord('2'):
                    print("[MANUAL TEST] Triggering FIST")
                    mqtt_mgr.publish_gesture("FIST")
                    last_sent_gesture = "FIST"
                elif key == ord('3'):
                    print("[MANUAL TEST] Triggering THUMBS_UP")
                    mqtt_mgr.publish_gesture("THUMBS_UP")
                    last_sent_gesture = "THUMBS_UP"
                elif key == ord('4'):
                    print("[MANUAL TEST] Triggering THUMBS_DOWN")
                    mqtt_mgr.publish_gesture("THUMBS_DOWN")
                    last_sent_gesture = "THUMBS_DOWN"
                elif key == ord('5'):
                    print("[MANUAL TEST] Triggering VICTORY")
                    mqtt_mgr.publish_gesture("VICTORY")
                    last_sent_gesture = "VICTORY"
            else:
                # Small sleep to regulate loop in headless mode
                time.sleep(0.03)

    except KeyboardInterrupt:
        print("\n[PIPEGEN] Interrupted by user.")
    finally:
        stream.release()
        mqtt_mgr.stop()
        if not headless:
            cv2.destroyAllWindows()
        print("[PIPEGEN] System shutdown complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AirControl AI - PipeGen Gesture Recognition Engine")
    parser.add_argument("--config", type=str, default=None, help="Path to custom config JSON")
    parser.add_argument("--headless", action="store_true", help="Run without OpenCV GUI window")
    parser.add_argument("--mock-camera", action="store_true", help="Force synthetic virtual camera mode")
    parser.add_argument("--iterations", type=int, default=None, help="Run for N frames then exit")
    parser.add_argument("--gesture", type=str, default=None, help="Force a specific gesture test")

    args = parser.parse_args()
    run_pipegen(
        config_path=args.config,
        headless=args.headless,
        mock_camera=args.mock_camera,
        max_iterations=args.iterations,
        test_gesture=args.gesture
    )
