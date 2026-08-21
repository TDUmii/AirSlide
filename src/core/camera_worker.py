"""Non-blocking camera, MediaPipe inference, overlays, and gesture signals."""

from __future__ import annotations

import logging
import time
from collections import deque
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .gesture_detector import GestureDetector, GestureEvent
from .hand_tracker import HandObservation, HandTracker


class CameraWorker(QThread):
    frame_ready = Signal(QImage)
    status_ready = Signal(dict)
    gesture_detected = Signal(str, dict)
    camera_error = Signal(str)
    initialized = Signal()

    CONNECTIONS = (
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
    )

    def __init__(self, settings: dict[str, Any], model_path: Path) -> None:
        super().__init__()
        self.settings = settings.copy()
        self.model_path = model_path
        self._running = True
        self.logger = logging.getLogger("airslide")
        self.detector = GestureDetector(self.settings)
        self.trajectory: deque[tuple[int, int]] = deque(maxlen=24)

    def stop(self) -> None:
        self._running = False
        self.requestInterruption()

    def run(self) -> None:
        import cv2

        camera = None
        tracker = None
        try:
            camera = cv2.VideoCapture(int(self.settings["camera_index"]), cv2.CAP_DSHOW)
            width, height = (1280, 720) if self.settings["resolution"] == "1280x720" else (640, 480)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            camera.set(cv2.CAP_PROP_FPS, 30)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not camera.isOpened():
                self.camera_error.emit(
                    "Camera is unavailable. It may be used by another application."
                )
                return
            self.logger.info("Camera %s initialized", self.settings["camera_index"])
            try:
                tracker = HandTracker(self.model_path, str(self.settings["control_hand"]))
                self.logger.info("MediaPipe Hand Landmarker model loaded")
            except Exception as exc:
                self.logger.exception("MediaPipe model load failure")
                self.camera_error.emit(str(exc))
            self.initialized.emit()

            fps_times: deque[float] = deque(maxlen=30)
            start_time = time.perf_counter()
            last_render = 0.0
            last_result_ms = -1
            last_inference_submit = -1.0
            observation: HandObservation | None = None
            failures = 0
            while self._running and not self.isInterruptionRequested():
                success, frame = camera.read()
                now = time.perf_counter()
                if not success:
                    failures += 1
                    if failures >= 8:
                        self.camera_error.emit("Unable to read camera frames.")
                        return
                    self.msleep(20)
                    continue
                failures = 0
                if bool(self.settings["mirror"]):
                    frame = cv2.flip(frame, 1)
                if tracker is not None and now - last_inference_submit >= 0.05:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    timestamp_ms = int((now - start_time) * 1000)
                    tracker.submit(rgb, timestamp_ms)
                    last_inference_submit = now
                if tracker is not None:
                    latest = tracker.latest(last_result_ms)
                    if latest is not None:
                        last_result_ms, observation = latest
                        self._process_observation(start_time + last_result_ms / 1000.0, observation)
                elif last_result_ms < 0:
                    self._process_observation(now, None)
                    last_result_ms = 0

                fps_times.append(now)
                fps = 0.0
                if len(fps_times) > 1:
                    fps = (len(fps_times) - 1) / max(0.001, fps_times[-1] - fps_times[0])
                status = self._status(observation, fps)
                self.status_ready.emit(status)

                render_interval = 0.18 if bool(self.settings.get("presentation_mode")) else 0.0
                if now - last_render >= render_interval:
                    self._draw_overlay(frame, observation, fps)
                    preview = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, channels = preview.shape
                    image = QImage(preview.data, w, h, channels * w, QImage.Format.Format_RGB888).copy()
                    self.frame_ready.emit(image)
                    last_render = now
        except Exception as exc:
            self.logger.exception("Camera worker failed")
            self.camera_error.emit(f"Camera worker error: {exc}")
        finally:
            if tracker is not None:
                try:
                    tracker.close()
                except Exception:
                    self.logger.exception("Failed to close MediaPipe tracker")
            if camera is not None:
                camera.release()
            self.logger.info("Camera worker stopped")

    def _process_observation(self, now: float, observation: HandObservation | None) -> None:
        if observation is None:
            event = self.detector.update(now, None, None, False, 0.0)
            self.trajectory.clear()
        else:
            event = self.detector.update(
                now,
                observation.palm_x,
                observation.palm_y,
                observation.is_open_palm,
                observation.open_palm_confidence,
            )
        if event is not GestureEvent.NONE:
            self.logger.info("%s detected", event.value.replace("_", " ").title())
            self.gesture_detected.emit(event.value, self.detector.diagnostics.to_dict())

    def _status(self, observation: HandObservation | None, fps: float) -> dict[str, Any]:
        diag = self.detector.diagnostics
        return {
            "system": diag.state,
            "camera": f"Camera {self.settings['camera_index']}",
            "hand": observation.handedness if observation else "No Hand",
            "gesture": "Open Palm" if observation and observation.is_open_palm else "—",
            "fps": round(fps, 1),
            "debug": diag.to_dict(),
        }

    def _draw_overlay(self, frame: Any, observation: HandObservation | None, fps: float) -> None:
        import cv2

        h, w = frame.shape[:2]
        if observation and bool(self.settings["show_landmarks"]):
            points = [(int(x * w), int(y * h)) for x, y, _ in observation.landmarks]
            for first, second in self.CONNECTIONS:
                cv2.line(frame, points[first], points[second], (194, 176, 125), 2, cv2.LINE_AA)
            for point in points:
                cv2.circle(frame, point, 3, (235, 244, 239), -1, cv2.LINE_AA)
            center = (int(observation.palm_x * w), int(observation.palm_y * h))
            self.trajectory.append(center)
            cv2.circle(frame, center, 7, (78, 164, 120), -1, cv2.LINE_AA)
            if bool(self.settings["debug_mode"]) and len(self.trajectory) > 1:
                cv2.polylines(frame, [__import__("numpy").array(self.trajectory)], False, (78, 164, 120), 3, cv2.LINE_AA)
        if bool(self.settings["show_fps"]):
            cv2.putText(frame, f"{fps:.0f} FPS", (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (240, 240, 240), 2, cv2.LINE_AA)
