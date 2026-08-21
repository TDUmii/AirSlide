"""Validated JSON settings with safe fallback behavior."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import writable_path

DEFAULT_SETTINGS: dict[str, Any] = {
    "camera_index": 0,
    "resolution": "640x480",
    "mirror": True,
    "show_landmarks": True,
    "show_fps": True,
    "debug_mode": False,
    "control_hand": "auto",
    "swipe_threshold": 0.15,
    "velocity_threshold": 0.42,
    "gesture_window_ms": 550,
    "cooldown_ms": 500,
    "horizontal_ratio": 1.30,
    "direction_consistency": 0.68,
    "dead_zone": 0.010,
    "smoothing_alpha": 0.68,
    "next_key": "right",
    "previous_key": "left",
    "theme": "system",
    "sensitivity": "medium",
    "presentation_mode": False,
    "show_onboarding": True,
}

RANGES: dict[str, tuple[float, float]] = {
    "swipe_threshold": (0.08, 0.40),
    "velocity_threshold": (0.15, 2.5),
    "gesture_window_ms": (250, 900),
    "cooldown_ms": (300, 2000),
    "horizontal_ratio": (1.0, 3.0),
    "direction_consistency": (0.55, 1.0),
    "dead_zone": (0.0, 0.05),
    "smoothing_alpha": (0.2, 1.0),
}


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or writable_path("config", "settings.json")
        self.logger = logging.getLogger("airslide")
        self._settings = deepcopy(DEFAULT_SETTINGS)
        self.load()

    @property
    def settings(self) -> dict[str, Any]:
        return deepcopy(self._settings)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            self.save(DEFAULT_SETTINGS)
            self.logger.info("Default settings created")
            return self.settings
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("settings root must be an object")
            merged = deepcopy(DEFAULT_SETTINGS)
            merged.update(raw)
            self._settings = self._validate(merged)
            self.logger.info("Settings loaded")
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            self.logger.warning("Invalid settings; defaults restored: %s", exc)
            self._settings = deepcopy(DEFAULT_SETTINGS)
            self.save()
        return self.settings

    def save(self, values: dict[str, Any] | None = None) -> None:
        if values is not None:
            merged = deepcopy(DEFAULT_SETTINGS)
            merged.update(values)
            self._settings = self._validate(merged)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._settings, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def update(self, **values: Any) -> dict[str, Any]:
        merged = self.settings
        merged.update(values)
        self.save(merged)
        return self.settings

    @staticmethod
    def _validate(values: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(values)
        for name, (minimum, maximum) in RANGES.items():
            try:
                numeric = float(result[name])
            except (TypeError, ValueError, KeyError):
                numeric = float(DEFAULT_SETTINGS[name])
            result[name] = max(minimum, min(maximum, numeric))
            if name in {"gesture_window_ms", "cooldown_ms"}:
                result[name] = int(result[name])
        result["camera_index"] = max(0, int(result.get("camera_index", 0)))
        if result.get("resolution") not in {"640x480", "1280x720"}:
            result["resolution"] = "640x480"
        if result.get("control_hand") not in {"auto", "left", "right"}:
            result["control_hand"] = "auto"
        if result.get("theme") not in {"system", "light", "dark"}:
            result["theme"] = "system"
        for name in ("mirror", "show_landmarks", "show_fps", "debug_mode", "presentation_mode", "show_onboarding"):
            result[name] = bool(result.get(name, DEFAULT_SETTINGS[name]))
        return result
