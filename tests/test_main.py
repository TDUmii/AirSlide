from __future__ import annotations

import main
from src.ui.main_window import gesture_moves_to_next_slide


def test_venv_has_all_runtime_dependencies() -> None:
    assert main.missing_runtime_dependencies() == []


def test_missing_dependency_uses_friendly_package_name(monkeypatch) -> None:
    monkeypatch.setattr(
        main.importlib.util,
        "find_spec",
        lambda module_name: None if module_name == "cv2" else object(),
    )
    assert main.missing_runtime_dependencies() == ["opencv-contrib-python (cv2)"]


def test_canva_page_motion_follows_swipe_direction() -> None:
    assert gesture_moves_to_next_slide("SWIPE_LEFT") is True
    assert gesture_moves_to_next_slide("SWIPE_RIGHT") is False
