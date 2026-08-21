from src.core.hand_tracker import HandTracker


def test_mirrored_handedness_matches_presenters_body_side() -> None:
    assert HandTracker.normalize_handedness("Right", mirrored_input=True) == "Left"
    assert HandTracker.normalize_handedness("Left", mirrored_input=True) == "Right"


def test_unmirrored_handedness_keeps_mediapipe_label() -> None:
    assert HandTracker.normalize_handedness("Right", mirrored_input=False) == "Right"
    assert HandTracker.normalize_handedness("Left", mirrored_input=False) == "Left"
