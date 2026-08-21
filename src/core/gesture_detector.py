"""Webcam-independent swipe detector operating on normalized palm centers."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from enum import Enum

from .gesture_state_machine import GestureStateMachine


class GestureEvent(str, Enum):
    NONE = "NONE"
    SWIPE_LEFT = "SWIPE_LEFT"
    SWIPE_RIGHT = "SWIPE_RIGHT"


@dataclass(frozen=True)
class PalmSample:
    timestamp: float
    x: float
    y: float


@dataclass
class GestureDiagnostics:
    palm_x: float = 0.0
    palm_y: float = 0.0
    delta_x: float = 0.0
    delta_y: float = 0.0
    velocity: float = 0.0
    consistency: float = 0.0
    progress: float = 0.0
    state: str = "NO HAND"
    open_palm_confidence: float = 0.0
    duration: float = 0.0

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


class GestureDetector:
    """Detect fast, consistent horizontal swipes with a timed cooldown."""

    def __init__(self, settings: dict[str, object]) -> None:
        self.settings = settings.copy()
        self.history: deque[PalmSample] = deque()
        self.state_machine = GestureStateMachine(int(self.settings["cooldown_ms"]))
        self.diagnostics = GestureDiagnostics()
        self._smoothed: tuple[float, float] | None = None

    def update(
        self,
        timestamp: float,
        palm_x: float | None,
        palm_y: float | None,
        is_open_palm: bool,
        open_palm_confidence: float = 0.0,
    ) -> GestureEvent:
        present = palm_x is not None and palm_y is not None
        self.state_machine.update(
            timestamp,
            hand_present=present,
            open_palm=is_open_palm,
        )
        self.diagnostics.open_palm_confidence = open_palm_confidence
        self.diagnostics.state = self.state_machine.state.value

        if not present or not is_open_palm:
            self.history.clear()
            self._smoothed = None
            return GestureEvent.NONE

        x, y = self._smooth(float(palm_x), float(palm_y))
        self.diagnostics.palm_x, self.diagnostics.palm_y = x, y
        if not self.state_machine.can_detect:
            self.history.clear()
            return GestureEvent.NONE

        self.history.append(PalmSample(timestamp, x, y))
        window_s = float(self.settings["gesture_window_ms"]) / 1000.0
        while self.history and timestamp - self.history[0].timestamp > window_s:
            self.history.popleft()
        self.state_machine.mark_tracking()

        event = self._classify()
        if event is not GestureEvent.NONE:
            self.state_machine.trigger(timestamp)
            self.diagnostics.state = self.state_machine.state.value
            self.history.clear()
        return event

    def _classify(self) -> GestureEvent:
        if len(self.history) < 4:
            return GestureEvent.NONE
        first, last = self.history[0], self.history[-1]
        elapsed = last.timestamp - first.timestamp
        if elapsed < 0.06:
            return GestureEvent.NONE
        dx, dy = last.x - first.x, last.y - first.y
        velocity = dx / elapsed
        threshold = float(self.settings["swipe_threshold"])
        self.diagnostics.delta_x = dx
        self.diagnostics.delta_y = dy
        self.diagnostics.velocity = velocity
        self.diagnostics.duration = elapsed
        self.diagnostics.progress = min(1.0, abs(dx) / threshold)
        if abs(dx) < threshold or abs(velocity) < float(self.settings["velocity_threshold"]):
            return GestureEvent.NONE
        if abs(dx) < abs(dy) * float(self.settings["horizontal_ratio"]):
            return GestureEvent.NONE

        direction = 1 if dx > 0 else -1
        meaningful = 0
        aligned = 0
        step_dead_zone = max(0.0015, float(self.settings["dead_zone"]) * 0.20)
        samples = list(self.history)
        for previous, current in zip(samples, samples[1:]):
            step = current.x - previous.x
            if abs(step) >= step_dead_zone:
                meaningful += 1
                aligned += int(step * direction > 0)
        consistency = aligned / meaningful if meaningful else 0.0
        self.diagnostics.consistency = consistency
        if meaningful < 2 or consistency < float(self.settings["direction_consistency"]):
            return GestureEvent.NONE
        return GestureEvent.SWIPE_RIGHT if direction > 0 else GestureEvent.SWIPE_LEFT

    def _smooth(self, x: float, y: float) -> tuple[float, float]:
        alpha = float(self.settings["smoothing_alpha"])
        if self._smoothed is None:
            self._smoothed = (x, y)
        else:
            self._smoothed = (
                alpha * x + (1.0 - alpha) * self._smoothed[0],
                alpha * y + (1.0 - alpha) * self._smoothed[1],
            )
        return self._smoothed

    def reset(self) -> None:
        self.history.clear()
        self._smoothed = None
        self.state_machine.reset()
