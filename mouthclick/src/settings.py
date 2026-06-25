import json
import os
import sys
from copy import deepcopy
from pathlib import Path

from .config import (
    DEFAULT_CURSOR_SENSITIVITY,
    DEFAULT_EYE_CLOSED_THRESHOLD,
    PROJECT_ROOT,
    TONGUE_COLOR_RATIO_THRESHOLD,
    TONGUE_MOUTH_OPEN_THRESHOLD,
)


def default_settings_path():
    if getattr(sys, "frozen", False):
        app_data = os.getenv("APPDATA")
        if app_data:
            return Path(app_data) / "MouthClick" / "settings.json"

    return PROJECT_ROOT / "mouthclick_settings.json"


SETTINGS_PATH = default_settings_path()

DEFAULT_SETTINGS = {
    "sensitivity": DEFAULT_CURSOR_SENSITIVITY,
    "blink_threshold": DEFAULT_EYE_CLOSED_THRESHOLD,
    "diagnostic_enabled": False,
    "start_unlocked": True,
    "tongue": {
        "mouth_open_threshold": TONGUE_MOUTH_OPEN_THRESHOLD,
        "color_ratio_threshold": TONGUE_COLOR_RATIO_THRESHOLD,
    },
    "nose_calibration": None,
}


class AppSettings:
    def __init__(self, path=SETTINGS_PATH, data=None):
        self.path = path
        self.data = deepcopy(DEFAULT_SETTINGS)

        if data:
            self.merge(data)

    @classmethod
    def load(cls, path=SETTINGS_PATH):
        if not path.exists():
            return cls(path=path)

        try:
            with path.open("r", encoding="utf-8") as settings_file:
                loaded_data = json.load(settings_file)
        except (OSError, json.JSONDecodeError):
            return cls(path=path)

        return cls(path=path, data=loaded_data)

    def merge(self, data):
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(self.data.get(key), dict):
                self.data[key].update(value)
            else:
                self.data[key] = value

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as settings_file:
                json.dump(self.data, settings_file, indent=2, ensure_ascii=False)
        except OSError:
            return False

        return True

    def get_float(self, key, default):
        try:
            return float(self.data.get(key, default))
        except (TypeError, ValueError):
            return default

    def get_bool(self, key, default=False):
        return bool(self.data.get(key, default))

    def set_value(self, key, value):
        self.data[key] = value

    def tongue_thresholds(self):
        tongue_settings = self.data.get("tongue", {})
        return (
            float(tongue_settings.get("mouth_open_threshold", TONGUE_MOUTH_OPEN_THRESHOLD)),
            float(tongue_settings.get("color_ratio_threshold", TONGUE_COLOR_RATIO_THRESHOLD)),
        )

    def set_tongue_thresholds(self, mouth_open_threshold, color_ratio_threshold):
        self.data["tongue"] = {
            "mouth_open_threshold": round(float(mouth_open_threshold), 4),
            "color_ratio_threshold": round(float(color_ratio_threshold), 4),
        }

    def set_nose_calibration(self, calibration_data):
        self.data["nose_calibration"] = calibration_data
