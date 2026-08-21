from __future__ import annotations

import pytest

from src.core.gesture_detector import GestureDetector, GestureEvent
from src.utils.config_manager import DEFAULT_SETTINGS


def detector(**overrides: object) -> GestureDetector:
    settings = DEFAULT_SETTINGS.copy()
    settings.update(overrides)
    return GestureDetector(settings)


def feed(
    engine: GestureDetector,
    xs: list[float],
    ys: list[float] | None = None,
    *,
    start: float = 0.0,
    step: float = 0.08,
    open_palm: bool = True,
) -> list[GestureEvent]:
    ys = ys or [0.5] * len(xs)
    return [
        engine.update(start + index * step, x, y, open_palm, 0.9 if open_palm else 0.1)
        for index, (x, y) in enumerate(zip(xs, ys))
    ]


def test_fast_right_swipe_is_detected_once() -> None:
    events = feed(detector(), [0.30, 0.34, 0.40, 0.48, 0.57, 0.66])
    assert events.count(GestureEvent.SWIPE_RIGHT) == 1


def test_fast_left_swipe_is_detected_once() -> None:
    events = feed(detector(), [0.70, 0.66, 0.60, 0.52, 0.43, 0.34])
    assert events.count(GestureEvent.SWIPE_LEFT) == 1


def test_short_deliberate_swipe_is_detected_with_sensitive_defaults() -> None:
    events = feed(detector(), [0.30, 0.34, 0.38, 0.42])
    assert events.count(GestureEvent.SWIPE_RIGHT) == 1


@pytest.mark.parametrize(
    ("xs", "ys", "step"),
    [
        ([0.50, 0.51, 0.49, 0.52, 0.50, 0.51, 0.49], None, 0.06),
        ([0.30, 0.34, 0.38, 0.42, 0.46, 0.50, 0.54, 0.58], None, 0.65),
        ([0.30, 0.32, 0.34, 0.36, 0.37, 0.38], None, 0.07),
        ([0.50, 0.52, 0.54, 0.56, 0.58, 0.60], [0.20, 0.28, 0.38, 0.50, 0.63, 0.76], 0.07),
        ([0.35, 0.43, 0.38, 0.48, 0.40, 0.53, 0.45, 0.58], None, 0.06),
    ],
)
def test_invalid_motion_does_not_trigger(xs: list[float], ys: list[float] | None, step: float) -> None:
    assert all(event is GestureEvent.NONE for event in feed(detector(), xs, ys, step=step))


def test_closed_palm_swipe_does_not_trigger() -> None:
    assert all(
        event is GestureEvent.NONE
        for event in feed(detector(), [0.30, 0.36, 0.44, 0.53, 0.63, 0.72], open_palm=False)
    )


def test_no_hand_never_triggers() -> None:
    engine = detector()
    assert [engine.update(i * 0.1, None, None, False) for i in range(10)] == [GestureEvent.NONE] * 10


def test_cooldown_blocks_immediate_repeat_then_automatically_recovers() -> None:
    engine = detector(cooldown_ms=500)
    first = feed(engine, [0.30, 0.35, 0.42, 0.50, 0.59, 0.68], start=0.0)
    immediate = feed(engine, [0.30, 0.36, 0.44, 0.53, 0.63, 0.72], start=0.48, step=0.06)
    assert first.count(GestureEvent.SWIPE_RIGHT) == 1
    assert all(event is GestureEvent.NONE for event in immediate)

    after_cooldown = feed(engine, [0.70, 0.65, 0.58, 0.50, 0.41, 0.32], start=1.05)
    assert after_cooldown.count(GestureEvent.SWIPE_LEFT) == 1


def test_open_palm_can_swipe_again_without_a_rearm_pose() -> None:
    engine = detector(cooldown_ms=500)
    swipe = [0.30, 0.35, 0.42, 0.50, 0.59, 0.68]
    first = feed(engine, swipe, start=0.0)
    second = feed(engine, swipe, start=1.05)

    assert first.count(GestureEvent.SWIPE_RIGHT) == 1
    assert second.count(GestureEvent.SWIPE_RIGHT) == 1


def test_diagnostics_are_bounded() -> None:
    engine = detector()
    feed(engine, [0.3, 0.35, 0.42, 0.50, 0.60, 0.69])
    assert 0.0 <= engine.diagnostics.progress <= 1.0
    assert 0.0 <= engine.diagnostics.consistency <= 1.0
