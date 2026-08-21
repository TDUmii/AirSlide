"""Cooldown and deliberate rearm state for one-action-per-swipe safety."""

from __future__ import annotations

from enum import Enum


class GestureState(str, Enum):
    NO_HAND = "NO HAND"
    READY = "READY"
    TRACKING = "TRACKING"
    COOLDOWN = "COOLDOWN"
    WAIT_FOR_REARM = "WAIT FOR REARM"


class GestureStateMachine:
    """Gate swipe detection until cooldown and a physical reset both occur."""

    def __init__(self, cooldown_ms: int = 800) -> None:
        self.cooldown_s = cooldown_ms / 1000.0
        self.state = GestureState.NO_HAND
        self.triggered_at = -1e9
        self._reset_started: float | None = None
        self._reset_seen_during_cooldown = False

    @property
    def can_detect(self) -> bool:
        return self.state in {GestureState.READY, GestureState.TRACKING}

    def mark_tracking(self) -> None:
        if self.can_detect:
            self.state = GestureState.TRACKING

    def trigger(self, timestamp: float) -> None:
        self.triggered_at = timestamp
        self._reset_started = None
        self._reset_seen_during_cooldown = False
        self.state = GestureState.COOLDOWN

    def update(
        self,
        timestamp: float,
        *,
        hand_present: bool,
        open_palm: bool,
        motion_speed: float = 0.0,
        near_center: bool = False,
    ) -> GestureState:
        if self.state == GestureState.COOLDOWN:
            # Returning through the center during cooldown is the most natural
            # preparation for the next swipe. Remember it instead of discarding
            # that physical reset with the rest of the cooldown frames.
            if (not hand_present) or (not open_palm) or near_center:
                self._reset_seen_during_cooldown = True
            if timestamp - self.triggered_at >= self.cooldown_s:
                if self._reset_seen_during_cooldown:
                    self.state = (
                        GestureState.READY
                        if hand_present and open_palm
                        else GestureState.NO_HAND
                    )
                    self._reset_seen_during_cooldown = False
                    return self.state
                self.state = GestureState.WAIT_FOR_REARM
            else:
                return self.state

        if self.state == GestureState.WAIT_FOR_REARM:
            if not hand_present or not open_palm:
                reset_condition, required = True, 0.12
            elif near_center:
                reset_condition, required = True, 0.06
            else:
                reset_condition, required = motion_speed < 0.12, 0.24
            if reset_condition:
                self._reset_started = self._reset_started or timestamp
                if timestamp - self._reset_started >= required:
                    self.state = GestureState.READY if hand_present and open_palm else GestureState.NO_HAND
                    self._reset_started = None
            else:
                self._reset_started = None
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
        self._reset_started = None
        self._reset_seen_during_cooldown = False
