"""
AirControl AI - PipeGen Configuration Module
Manages configuration parameters for camera, gesture detection, and MQTT broker.
"""

import json
import os
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "mqtt": {
        "broker": "broker.emqx.io",
        "port": 1883,
        "keepalive": 60,
        "client_id_prefix": "AirControl_PipeGen_",
        "topics": {
            "command": "aircontrol/commands/gesture",
            "status": "aircontrol/device/status",
            "telemetry": "aircontrol/device/telemetry"
        }
    },
    "camera": {
        "device_index": 0,
        "frame_width": 640,
        "frame_height": 480,
        "fps": 30,
        "mock_mode": False
    },
    "gesture": {
        "confidence_threshold": 0.70,
        "consecutive_frames_required": 5,
        "cooldown_seconds": 1.0,
        "supported_gestures": [
            "OPEN_HAND",
            "FIST",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "VICTORY"
        ]
    },
    "actuator_mappings": {
        "OPEN_HAND": "GREEN_LED_ON",
        "FIST": "GREEN_LED_OFF",
        "THUMBS_UP": "SERVO_90",
        "THUMBS_DOWN": "SERVO_0",
        "VICTORY": "ALARM_RED_BUZZER"
    }
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Loads configuration from JSON file or returns defaults."""
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "default_config.json")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                for k, v in user_cfg.items():
                    if isinstance(v, dict) and k in merged:
                        merged[k].update(v)
                    else:
                        merged[k] = v
                return merged
        except Exception as e:
            print(f"[CONFIG WARNING] Could not parse {config_path}: {e}. Using defaults.")

    return DEFAULT_CONFIG
