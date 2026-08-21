"""Settings dialog with simple sensitivity plus optional advanced tuning."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)


class SettingsDialog(QDialog):
    settings_saved = Signal(dict)

    def __init__(self, settings: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.values = settings.copy()
        self.setWindowTitle("AirSlide Settings")
        self.setMinimumSize(560, 540)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._camera_tab(), "Camera")
        tabs.addTab(self._gesture_tab(), "Gesture")
        tabs.addTab(self._control_tab(), "Control")
        tabs.addTab(self._interface_tab(), "Interface")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _combo(items: list[tuple[str, Any]], current: Any) -> QComboBox:
        combo = QComboBox()
        for label, value in items:
            combo.addItem(label, value)
        index = combo.findData(current)
        combo.setCurrentIndex(max(0, index))
        return combo

    def _camera_tab(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page)
        self.camera = QSpinBox(); self.camera.setRange(0, 10); self.camera.setValue(int(self.values["camera_index"]))
        self.resolution = self._combo([("640 × 480", "640x480"), ("1280 × 720", "1280x720")], self.values["resolution"])
        self.mirror = QCheckBox("Mirror preview and gesture direction"); self.mirror.setChecked(bool(self.values["mirror"]))
        form.addRow("Camera device", self.camera); form.addRow("Resolution", self.resolution); form.addRow("", self.mirror)
        return page

    def _gesture_tab(self) -> QWidget:
        page = QWidget(); outer = QVBoxLayout(page)
        basic = QGroupBox("Sensitivity"); basic_form = QFormLayout(basic)
        self.sensitivity = self._combo([("Low (fewer triggers)", "low"), ("Medium", "medium"), ("High (easier triggers)", "high"), ("Custom", "custom")], self.values.get("sensitivity", "medium"))
        basic_form.addRow("Preset", self.sensitivity); outer.addWidget(basic)
        advanced = QGroupBox("Advanced settings"); form = QFormLayout(advanced)
        self.distance = self._double(0.05, 0.40, float(self.values["swipe_threshold"]), 0.01)
        self.velocity = self._double(0.10, 2.5, float(self.values["velocity_threshold"]), 0.05)
        self.window = QSpinBox(); self.window.setRange(250, 900); self.window.setSuffix(" ms"); self.window.setValue(int(self.values["gesture_window_ms"]))
        self.cooldown = QSpinBox(); self.cooldown.setRange(300, 2000); self.cooldown.setSuffix(" ms"); self.cooldown.setValue(int(self.values["cooldown_ms"]))
        self.horizontal = self._double(1.0, 3.0, float(self.values["horizontal_ratio"]), 0.05)
        form.addRow("Swipe distance", self.distance); form.addRow("Minimum velocity", self.velocity)
        form.addRow("Gesture window", self.window); form.addRow("Cooldown", self.cooldown); form.addRow("Horizontal tolerance", self.horizontal)
        outer.addWidget(advanced); outer.addStretch()
        self.sensitivity.currentIndexChanged.connect(self._apply_preset)
        return page

    def _control_tab(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page)
        self.next_key = self._combo([("Right Arrow", "right")], self.values["next_key"])
        self.previous_key = self._combo([("Left Arrow", "left")], self.values["previous_key"])
        self.hand = self._combo([("Auto", "auto"), ("Left Hand", "left"), ("Right Hand", "right")], self.values["control_hand"])
        form.addRow("Next slide key", self.next_key); form.addRow("Previous slide key", self.previous_key); form.addRow("Control hand", self.hand)
        return page

    def _interface_tab(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page)
        self.theme = self._combo([("Follow system", "system"), ("Light", "light"), ("Dark", "dark")], self.values["theme"])
        self.landmarks = QCheckBox("Show hand landmarks"); self.landmarks.setChecked(bool(self.values["show_landmarks"]))
        self.fps = QCheckBox("Show FPS"); self.fps.setChecked(bool(self.values["show_fps"]))
        self.debug = QCheckBox("Debug mode and trajectory"); self.debug.setChecked(bool(self.values["debug_mode"]))
        form.addRow("Theme", self.theme); form.addRow("", self.landmarks); form.addRow("", self.fps); form.addRow("", self.debug)
        return page

    @staticmethod
    def _double(low: float, high: float, value: float, step: float) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(); widget.setRange(low, high); widget.setDecimals(3); widget.setSingleStep(step); widget.setValue(value)
        return widget

    def _apply_preset(self) -> None:
        preset = self.sensitivity.currentData()
        mappings = {
            "low": (0.16, 0.45, 600),
            "medium": (0.10, 0.25, 700),
            "high": (0.07, 0.15, 800),
        }
        if preset in mappings:
            distance, velocity, window = mappings[preset]
            self.distance.setValue(distance); self.velocity.setValue(velocity); self.window.setValue(window)

    def _save(self) -> None:
        self.values.update({
            "camera_index": self.camera.value(), "resolution": self.resolution.currentData(), "mirror": self.mirror.isChecked(),
            "sensitivity": self.sensitivity.currentData(), "swipe_threshold": self.distance.value(), "velocity_threshold": self.velocity.value(),
            "gesture_window_ms": self.window.value(), "cooldown_ms": self.cooldown.value(), "horizontal_ratio": self.horizontal.value(),
            "next_key": self.next_key.currentData(), "previous_key": self.previous_key.currentData(), "control_hand": self.hand.currentData(),
            "theme": self.theme.currentData(), "show_landmarks": self.landmarks.isChecked(), "show_fps": self.fps.isChecked(), "debug_mode": self.debug.isChecked(),
        })
        self.settings_saved.emit(self.values.copy()); self.accept()
