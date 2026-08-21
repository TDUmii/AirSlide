"""Time-based cooldown state for one-action-per-swipe safety."""

from __future__ import annotations

from enum import Enum


class GestureState(str, Enum):
    NO_HAND = "NO HAND"
    READY = "READY"
    TRACKING = "TRACKING"
    COOLDOWN = "COOLDOWN"


class GestureStateMachine:
    """Gate swipe detection for a fixed interval after every trigger."""

    def __init__(self, cooldown_ms: int = 1000) -> None:
        self.cooldown_s = cooldown_ms / 1000.0
        self.state = GestureState.NO_HAND
        self.triggered_at = -1e9

    @property
    def can_detect(self) -> bool:
        return self.state in {GestureState.READY, GestureState.TRACKING}

    def mark_tracking(self) -> None:
        if self.can_detect:
            self.state = GestureState.TRACKING

    def trigger(self, timestamp: float) -> None:
        self.triggered_at = timestamp
        self.state = GestureState.COOLDOWN

    def update(
        self,
        timestamp: float,
        *,
        hand_present: bool,
        open_palm: bool,
    ) -> GestureState:
        if self.state == GestureState.COOLDOWN:
            if timestamp - self.triggered_at < self.cooldown_s:
                return self.state

        if not hand_present:
            self.state = GestureState.NO_HAND
        elif open_palm:
            self.state = GestureState.READY
        else:
            self.state = GestureState.NO_HAND
        return self.state

    def reset(self) -> None:
        self.state = GestureState.NO_HAND
        self.triggered_at = -1e9
