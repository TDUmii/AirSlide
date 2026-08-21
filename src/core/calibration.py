"""Statistical calibration from deliberate swipe samples."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class CalibrationSample:
    direction: str
    distance: float
    velocity: float
    duration: float


class CalibrationSession:
    REQUIRED_PER_DIRECTION = 3

    def __init__(self) -> None:
        self.samples: list[CalibrationSample] = []

    def add(self, direction: str, distance: float, velocity: float, duration: float) -> bool:
        direction = direction.lower()
        if direction not in {"left", "right"} or self.count(direction) >= self.REQUIRED_PER_DIRECTION:
            return False
        self.samples.append(CalibrationSample(direction, abs(distance), abs(velocity), duration))
        return True

    def count(self, direction: str) -> int:
        return sum(sample.direction == direction for sample in self.samples)

    @property
    def complete(self) -> bool:
        return all(self.count(direction) >= self.REQUIRED_PER_DIRECTION for direction in ("right", "left"))

    def recommendation(self) -> dict[str, float | int | str]:
        if not self.complete:
            raise ValueError("Calibration requires three swipes in each direction")
        distance = mean(sample.distance for sample in self.samples)
        velocity = mean(sample.velocity for sample in self.samples)
        duration = mean(sample.duration for sample in self.samples)
        return {
            "swipe_threshold": round(max(0.10, min(0.30, distance * 0.72)), 3),
            "velocity_threshold": round(max(0.25, min(1.5, velocity * 0.58)), 3),
            "gesture_window_ms": int(max(300, min(750, duration * 1400))),
            "sensitivity": "custom",
        }
