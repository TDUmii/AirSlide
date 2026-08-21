import pytest

from src.core.calibration import CalibrationSession


def test_calibration_requires_three_each_and_recommends_safe_ranges() -> None:
    session = CalibrationSession()
    with pytest.raises(ValueError):
        session.recommendation()
    for direction in ("right", "left"):
        for index in range(3):
            assert session.add(direction, 0.24 + index * 0.01, 0.9 + index * 0.05, 0.35)
    assert session.complete
    recommendation = session.recommendation()
    assert 0.10 <= recommendation["swipe_threshold"] <= 0.30
    assert 0.25 <= recommendation["velocity_threshold"] <= 1.5
    assert 300 <= recommendation["gesture_window_ms"] <= 750


def test_calibration_rejects_extra_or_unknown_samples() -> None:
    session = CalibrationSession()
    assert not session.add("up", 0.2, 0.8, 0.3)
    for _ in range(3): session.add("right", 0.2, 0.8, 0.3)
    assert not session.add("right", 0.2, 0.8, 0.3)
