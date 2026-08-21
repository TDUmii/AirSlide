"""Keyboard-only presentation control boundary."""

from __future__ import annotations

import logging
from collections.abc import Callable


class SlideController:
    def __init__(
        self,
        next_key: str = "right",
        previous_key: str = "left",
        press_function: Callable[[str], None] | None = None,
    ) -> None:
        self.next_key = next_key
        self.previous_key = previous_key
        self._press = press_function
        self.logger = logging.getLogger("airslide")

    def _press_key(self, key: str) -> bool:
        try:
            if self._press is None:
                import pyautogui

                pyautogui.PAUSE = 0
                pyautogui.FAILSAFE = False
                self._press = pyautogui.press
            self._press(key)
            return True
        except Exception:
            self.logger.exception("Unable to send presentation key: %s", key)
            return False

    def next_slide(self) -> bool:
        success = self._press_key(self.next_key)
        if success:
            self.logger.info("Next Slide triggered")
        return success

    def previous_slide(self) -> bool:
        success = self._press_key(self.previous_key)
        if success:
            self.logger.info("Previous Slide triggered")
        return success
