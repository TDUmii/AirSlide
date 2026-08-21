"""MediaPipe Tasks hand tracking and orientation-independent open-palm logic."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass
class HandObservation:
    landmarks: list[tuple[float, float, float]]
    handedness: str
    confidence: float
    palm_x: float
    palm_y: float
    is_open_palm: bool
    open_palm_confidence: float


class HandTracker:
    """Small adapter around the current MediaPipe Hand Landmarker Tasks API."""

    PALM_INDICES = (0, 5, 9, 13, 17)
    FINGERS = ((5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20))

    def __init__(
        self,
        model_path: Path,
        control_hand: str = "auto",
        mirrored_input: bool = True,
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"MediaPipe model not found: {model_path}. Run scripts/download_model.py first."
            )
        import mediapipe as mp

        self.mp = mp
        self.control_hand = control_hand.lower()
        self.mirrored_input = mirrored_input
        self._result_lock = Lock()
        self._latest_timestamp_ms = -1
        self._latest_observation: HandObservation | None = None
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=2,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.55,
            min_tracking_confidence=0.55,
            result_callback=self._on_result,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self._last_label: str | None = None

    def submit(self, rgb_frame: Any, timestamp_ms: int) -> None:
        """Queue a frame without blocking capture; MediaPipe may drop stale frames."""
        image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_frame)
        self.landmarker.detect_async(image, timestamp_ms)

    def latest(self, after_timestamp_ms: int) -> tuple[int, HandObservation | None] | None:
        """Return a new inference result once, including explicit no-hand results."""
        with self._result_lock:
            if self._latest_timestamp_ms <= after_timestamp_ms:
                return None
            return self._latest_timestamp_ms, self._latest_observation

    def _on_result(self, result: Any, _image: Any, timestamp_ms: int) -> None:
        observation = self._observation_from_result(result)
        with self._result_lock:
            self._latest_timestamp_ms = timestamp_ms
            self._latest_observation = observation

    def _observation_from_result(self, result: Any) -> HandObservation | None:
        if not result.hand_landmarks:
            return None

        candidates: list[HandObservation] = []
        for index, raw_landmarks in enumerate(result.hand_landmarks):
            category = result.handedness[index][0]
            label = self.normalize_handedness(
                str(category.category_name or "Unknown"),
                self.mirrored_input,
            )
            score = float(category.score or 0.0)
            landmarks = [(float(point.x), float(point.y), float(point.z)) for point in raw_landmarks]
            palm_x = sum(landmarks[i][0] for i in self.PALM_INDICES) / len(self.PALM_INDICES)
            palm_y = sum(landmarks[i][1] for i in self.PALM_INDICES) / len(self.PALM_INDICES)
            open_score = self.open_palm_score(landmarks)
            candidates.append(
                HandObservation(
                    landmarks=landmarks,
                    handedness=label,
                    confidence=score,
                    palm_x=palm_x,
                    palm_y=palm_y,
                    is_open_palm=open_score >= 0.72,
                    open_palm_confidence=open_score,
                )
            )

        filtered = [
            item for item in candidates if self.control_hand == "auto" or item.handedness.lower() == self.control_hand
        ]
        if not filtered:
            return None
        # Prefer continuity before confidence so two visible hands do not alternate.
        chosen = max(
            filtered,
            key=lambda item: (item.handedness == self._last_label, item.confidence),
        )
        self._last_label = chosen.handedness
        return chosen

    @staticmethod
    def normalize_handedness(label: str, mirrored_input: bool) -> str:
        """Map MediaPipe's camera-space label to the presenter's mirrored view."""
        normalized = label.title()
        if mirrored_input:
            return {"Left": "Right", "Right": "Left"}.get(normalized, normalized)
        return normalized

    @classmethod
    def open_palm_score(cls, landmarks: list[tuple[float, float, float]]) -> float:
        """Return a 0..1 extension score for index through pinky.

        Distance ratios relative to the wrist work for upright, tilted, and sideways
        palms. Requiring three strongly extended fingers keeps the pose forgiving
        without accepting a fist.
        """
        if len(landmarks) != 21:
            return 0.0
        wrist = landmarks[0]

        def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
            return hypot(a[0] - b[0], a[1] - b[1])

        finger_scores: list[float] = []
        for _mcp, pip, tip in cls.FINGERS:
            base_distance = max(0.001, distance(landmarks[pip], wrist))
            ratio = distance(landmarks[tip], wrist) / base_distance
            finger_scores.append(max(0.0, min(1.0, (ratio - 1.0) / 0.32)))
        strong = sum(score >= 0.58 for score in finger_scores)
        if strong < 3:
            return sum(finger_scores) / len(finger_scores) * 0.65
        return min(1.0, sum(finger_scores) / len(finger_scores) * 0.85 + strong * 0.04)

    def close(self) -> None:
        self.landmarker.close()
