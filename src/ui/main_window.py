"""AirSlide dashboard, tray integration, settings, and safe shutdown."""

from __future__ import annotations

import logging
import os
from typing import Any

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)

from src.core.camera_worker import CameraWorker
from src.core.slide_controller import SlideController
from src.ui.calibration_dialog import CalibrationDialog
from src.ui.settings_dialog import SettingsDialog
from src.ui.styles import stylesheet
from src.utils.config_manager import ConfigManager
from src.utils.paths import resource_path


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.settings = config.settings
        self.logger = logging.getLogger("airslide")
        self.worker: CameraWorker | None = None
        self.control_enabled = False
        self.last_frame: QPixmap | None = None
        self.calibration: CalibrationDialog | None = None
        self._error_shown = False
        self.setWindowTitle("AirSlide — Gesture Presentation Controller")
        self.setMinimumSize(960, 650)
        self.resize(1120, 720)
        icon_path = resource_path("assets", "icon.svg")
        if icon_path.exists(): self.setWindowIcon(QIcon(str(icon_path)))
        self._build_ui()
        self._apply_theme()
        self._build_tray()
        self._build_shortcuts()
        if os.environ.get("AIRSLIDE_SKIP_CAMERA") != "1":
            self.start_camera()
        QTimer.singleShot(450, self._show_onboarding)

    def _build_ui(self) -> None:
        root = QWidget(); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(28, 24, 28, 24); outer.setSpacing(18)
        header = QHBoxLayout()
        brand = QVBoxLayout(); title = QLabel("AirSlide"); title.setObjectName("title")
        subtitle = QLabel("AI Gesture Presentation Controller · fully local"); subtitle.setObjectName("subtitle")
        brand.addWidget(title); brand.addWidget(subtitle); header.addLayout(brand); header.addStretch()
        calibration = QPushButton("Calibrate"); calibration.clicked.connect(self.open_calibration); header.addWidget(calibration)
        settings = QPushButton("Settings"); settings.clicked.connect(self.open_settings); header.addWidget(settings)
        outer.addLayout(header)

        content = QHBoxLayout(); content.setSpacing(18)
        camera_card = QFrame(); camera_card.setObjectName("card"); camera_layout = QVBoxLayout(camera_card); camera_layout.setContentsMargins(10, 10, 10, 10)
        self.camera_label = QLabel("Camera initializing…"); self.camera_label.setObjectName("camera"); self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(560, 410); self.camera_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        camera_layout.addWidget(self.camera_label)
        self.debug_label = QLabel(); self.debug_label.setObjectName("muted"); self.debug_label.setWordWrap(True); self.debug_label.hide(); camera_layout.addWidget(self.debug_label)
        content.addWidget(camera_card, 7)

        side = QFrame(); side.setObjectName("card"); side.setMinimumWidth(290); side.setMaximumWidth(350)
        side_layout = QVBoxLayout(side); side_layout.setContentsMargins(22, 22, 22, 22); side_layout.setSpacing(13)
        section = QLabel("SYSTEM STATUS"); section.setObjectName("section"); side_layout.addWidget(section)
        self.state_badge = QLabel("●  INITIALIZING"); self.state_badge.setStyleSheet("font-size: 12pt; font-weight: 700; color: #70808A;"); side_layout.addWidget(self.state_badge)
        self.status_labels: dict[str, QLabel] = {}
        grid = QGridLayout(); grid.setVerticalSpacing(12)
        rows = (("Camera", "camera"), ("Hand", "hand"), ("Gesture", "gesture"), ("Control", "control"), ("Last action", "action"), ("FPS", "fps"))
        for row, (caption, key) in enumerate(rows):
            label = QLabel(caption); label.setObjectName("muted"); value = QLabel("—"); value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(label, row, 0); grid.addWidget(value, row, 1); self.status_labels[key] = value
        self.status_labels["control"].setText("Off"); side_layout.addLayout(grid)
        side_layout.addStretch()
        self.action_feedback = QLabel(); self.action_feedback.setObjectName("action"); self.action_feedback.setAlignment(Qt.AlignmentFlag.AlignCenter); self.action_feedback.hide(); side_layout.addWidget(self.action_feedback)
        self.retry_button = QPushButton("Retry Camera"); self.retry_button.clicked.connect(self.restart_camera); self.retry_button.hide(); side_layout.addWidget(self.retry_button)
        content.addWidget(side, 3); outer.addLayout(content, 1)

        controls = QHBoxLayout(); controls.addStretch()
        self.presentation = QCheckBox("Presentation Mode (minimize after start)"); self.presentation.setChecked(bool(self.settings["presentation_mode"])); controls.addWidget(self.presentation)
        self.control_button = QPushButton("START CONTROL"); self.control_button.setObjectName("primary"); self.control_button.setMinimumWidth(230); self.control_button.clicked.connect(self.toggle_control); controls.addWidget(self.control_button); controls.addStretch()
        outer.addLayout(controls)
        hint = QLabel("Open palm + fast horizontal swipe  ·  F8 toggles control while AirSlide has focus")
        hint.setObjectName("muted"); hint.setAlignment(Qt.AlignmentFlag.AlignCenter); outer.addWidget(hint)

    def _build_shortcuts(self) -> None:
        self.toggle_shortcut = QShortcut(QKeySequence("F8"), self)
        self.toggle_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.toggle_shortcut.activated.connect(self.toggle_control)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu(); self.tray_toggle = QAction("Enable Control", self); self.tray_toggle.triggered.connect(self.toggle_control)
        show = QAction("Show AirSlide", self); show.triggered.connect(self.show_from_tray)
        exit_action = QAction("Exit", self); exit_action.triggered.connect(self.shutdown)
        menu.addAction(self.tray_toggle); menu.addSeparator(); menu.addAction(show); menu.addAction(exit_action)
        self.tray.setContextMenu(menu); self.tray.setToolTip("AirSlide · Control Off")
        self.tray.activated.connect(lambda reason: self.show_from_tray() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable(): self.tray.show()

    def start_camera(self) -> None:
        if self.worker and self.worker.isRunning(): return
        self.camera_label.setText("Camera initializing…"); self.retry_button.hide(); self._error_shown = False
        self.worker = CameraWorker(self.settings, resource_path("models", "hand_landmarker.task"))
        self.worker.frame_ready.connect(self.update_frame); self.worker.status_ready.connect(self.update_status)
        self.worker.gesture_detected.connect(self.handle_gesture); self.worker.camera_error.connect(self.handle_camera_error)
        self.worker.start()

    def restart_camera(self) -> None:
        self.stop_camera(); self.start_camera()

    def stop_camera(self) -> None:
        if self.worker:
            self.worker.stop()
            if not self.worker.wait(4000):
                self.logger.error("Camera worker did not stop within four seconds")
            self.worker = None

    def update_frame(self, image: Any) -> None:
        self.last_frame = QPixmap.fromImage(image); self._render_frame()

    def _render_frame(self) -> None:
        if not self.last_frame: return
        size = self.camera_label.size()
        pixmap = self.last_frame.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.camera_label.setPixmap(pixmap)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event); self._render_frame()

    def update_status(self, status: dict[str, Any]) -> None:
        state = str(status["system"])
        colors = {"READY": "#4E9870", "TRACKING": "#B28A3B", "COOLDOWN": "#C07A42", "WAIT FOR REARM": "#C07A42", "NO HAND": "#7A8790"}
        self.state_badge.setText(f"●  {state}"); self.state_badge.setStyleSheet(f"font-size: 12pt; font-weight: 700; color: {colors.get(state, '#7A8790')};")
        for key in ("camera", "hand", "gesture", "fps"): self.status_labels[key].setText(str(status[key]))
        debug = status["debug"]
        self.debug_label.setVisible(bool(self.settings["debug_mode"]))
        self.debug_label.setText(f"Palm ({debug['palm_x']:.3f}, {debug['palm_y']:.3f})   ΔX {debug['delta_x']:+.3f}   ΔY {debug['delta_y']:+.3f}   Velocity {debug['velocity']:+.2f}/s   Consistency {debug['consistency']:.0%}   Progress {debug['progress']:.0%}   Open {debug['open_palm_confidence']:.0%}")

    def handle_gesture(self, event: str, diagnostics: dict[str, Any]) -> None:
        if self.calibration and self.calibration.isVisible(): self.calibration.record_event(event, diagnostics)
        next_slide = event == "SWIPE_RIGHT"
        label = "→  NEXT SLIDE" if next_slide else "←  PREVIOUS SLIDE"
        self.status_labels["action"].setText("Next Slide" if next_slide else "Previous Slide")
        self._show_action(label)
        if not self.control_enabled: return
        controller = SlideController(str(self.settings["next_key"]), str(self.settings["previous_key"]))
        success = controller.next_slide() if next_slide else controller.previous_slide()
        if not success: self.status_labels["action"].setText("Keyboard error")

    def _show_action(self, text: str) -> None:
        self.action_feedback.setText(text); self.action_feedback.setWindowOpacity(1.0); self.action_feedback.show()
        animation = QPropertyAnimation(self.action_feedback, b"windowOpacity", self); animation.setDuration(650); animation.setStartValue(1.0); animation.setEndValue(0.0); animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.finished.connect(self.action_feedback.hide); self._action_animation = animation; animation.start()

    def toggle_control(self) -> None:
        self.control_enabled = not self.control_enabled
        self.control_button.setText("STOP CONTROL" if self.control_enabled else "START CONTROL")
        self.status_labels["control"].setText("Enabled" if self.control_enabled else "Off")
        self.tray_toggle.setText("Disable Control" if self.control_enabled else "Enable Control")
        self.tray.setToolTip(f"AirSlide · Control {'On' if self.control_enabled else 'Off'}")
        self.logger.info("Gesture control %s", "enabled" if self.control_enabled else "disabled")
        if self.control_enabled and self.presentation.isChecked():
            self.settings["presentation_mode"] = True; self.config.save(self.settings); self.restart_camera(); QTimer.singleShot(250, self.hide)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self); dialog.settings_saved.connect(self.apply_settings); dialog.exec()

    def apply_settings(self, values: dict[str, Any]) -> None:
        self.settings = values.copy(); self.config.save(self.settings); self._apply_theme(); self.restart_camera()

    def open_calibration(self) -> None:
        was_enabled = self.control_enabled
        if was_enabled: self.toggle_control()
        self.calibration = CalibrationDialog(self); self.calibration.apply_recommendation.connect(self.apply_calibration)
        self.calibration.exec(); self.calibration = None

    def apply_calibration(self, recommendation: dict[str, Any]) -> None:
        self.settings.update(recommendation); self.config.save(self.settings); self.restart_camera()
        QMessageBox.information(self, "Calibration applied", "Recommended gesture settings have been saved.")

    def handle_camera_error(self, message: str) -> None:
        self.camera_label.clear(); self.camera_label.setText("Unable to access camera"); self.retry_button.show()
        self.state_badge.setText("●  ERROR"); self.state_badge.setStyleSheet("font-size: 12pt; font-weight: 700; color: #B85F5F;")
        if not self._error_shown:
            self._error_shown = True; QMessageBox.warning(self, "AirSlide camera error", message)

    def _apply_theme(self) -> None:
        theme = self.settings.get("theme", "system")
        dark = theme == "dark" or (theme == "system" and QApplication.palette().window().color().lightness() < 128)
        QApplication.instance().setStyleSheet(stylesheet(dark))  # type: ignore[union-attr]

    def _show_onboarding(self) -> None:
        if not bool(self.settings.get("show_onboarding", True)): return
        box = QMessageBox(self); box.setWindowTitle("Welcome to AirSlide"); box.setIcon(QMessageBox.Icon.Information)
        box.setText("Present without touching the keyboard")
        box.setInformativeText("1. Face the webcam.\n2. Hold an open palm.\n3. Swipe right or left quickly.\n4. Press Start Control before presenting.")
        checkbox = QCheckBox("Don't show again"); box.setCheckBox(checkbox); box.exec()
        if checkbox.isChecked(): self.settings["show_onboarding"] = False; self.config.save(self.settings)

    def show_from_tray(self) -> None:
        self.showNormal(); self.raise_(); self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept(); self.shutdown()

    def shutdown(self) -> None:
        self.control_enabled = False; self.stop_camera(); self.tray.hide(); QApplication.quit()
