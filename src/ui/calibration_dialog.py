"""Guided six-swipe calibration dialog."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from src.core.calibration import CalibrationSession


class CalibrationDialog(QDialog):
    apply_recommendation = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = CalibrationSession()
        self.setWindowTitle("Gesture Calibration")
        self.setMinimumSize(460, 330)
        layout = QVBoxLayout(self); layout.setSpacing(16)
        title = QLabel("Calibrate your natural swipe"); title.setObjectName("section"); layout.addWidget(title)
        intro = QLabel("Keep an open palm in the center, then make three natural swipes right and three left.\nControl stays off during calibration—no presentation keys are sent.")
        intro.setWordWrap(True); intro.setObjectName("muted"); layout.addWidget(intro)
        self.instruction = QLabel(); self.instruction.setStyleSheet("font-size: 15pt; font-weight: 700; padding: 18px;"); layout.addWidget(self.instruction)
        self.progress = QProgressBar(); self.progress.setRange(0, 6); layout.addWidget(self.progress)
        self.summary = QLabel("Waiting for an open-palm swipe…"); self.summary.setObjectName("muted"); layout.addWidget(self.summary)
        self.apply_button = QPushButton("Apply Recommended Settings"); self.apply_button.setObjectName("primary"); self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self._apply); layout.addWidget(self.apply_button); layout.addStretch()
        self._refresh()

    def record_event(self, event: str, diagnostics: dict[str, Any]) -> None:
        direction = "right" if event == "SWIPE_RIGHT" else "left"
        if direction == "left" and self.session.count("right") < 3:
            self.summary.setText("Please complete the right swipes first."); return
        accepted = self.session.add(direction, float(diagnostics["delta_x"]), float(diagnostics["velocity"]), float(diagnostics["duration"]))
        if accepted: self._refresh()

    def _refresh(self) -> None:
        right, left = self.session.count("right"), self.session.count("left")
        self.progress.setValue(right + left)
        self.instruction.setText(f"Step 2 — Swipe right  →   ({right}/3)" if right < 3 else f"Step 3 — Swipe left  ←   ({left}/3)")
        self.summary.setText(f"Captured {right + left} of 6 swipes")
        if self.session.complete:
            recommendation = self.session.recommendation()
            self.instruction.setText("Calibration complete")
            self.summary.setText(f"Recommended distance {recommendation['swipe_threshold']:.3f} · velocity {recommendation['velocity_threshold']:.3f} · window {recommendation['gesture_window_ms']} ms")
            self.apply_button.setEnabled(True)

    def _apply(self) -> None:
        self.apply_recommendation.emit(self.session.recommendation()); self.accept()
