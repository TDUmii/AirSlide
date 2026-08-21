from __future__ import annotations

import json

from src.utils.config_manager import ConfigManager, DEFAULT_SETTINGS


def test_missing_settings_are_created(tmp_path) -> None:
    path = tmp_path / "config" / "settings.json"
    manager = ConfigManager(path)
    assert path.exists()
    assert manager.settings["swipe_threshold"] == DEFAULT_SETTINGS["swipe_threshold"]


def test_invalid_json_restores_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    manager = ConfigManager(path)
    assert manager.settings == DEFAULT_SETTINGS
    assert json.loads(path.read_text(encoding="utf-8"))["mirror"] is True


def test_out_of_range_values_are_clamped(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"cooldown_ms": 9000, "swipe_threshold": -2}), encoding="utf-8")
    settings = ConfigManager(path).settings
    assert settings["cooldown_ms"] == 2000
    assert settings["swipe_threshold"] == 0.05
