"""Open the configured camera/model briefly and prove clean worker shutdown."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.core.camera_worker import CameraWorker
from src.utils.config_manager import ConfigManager


def main() -> int:
    app = QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        settings = ConfigManager(Path(directory) / "settings.json").settings
        settings["show_landmarks"] = False
        worker = CameraWorker(settings, ROOT / "models" / "hand_landmarker.task")
        result = {"initialized": False, "frames": 0, "error": "", "first": 0.0, "last": 0.0}
        worker.initialized.connect(lambda: result.update(initialized=True))
        def frame_received(_image: object) -> None:
            now = time.perf_counter()
            result.update(frames=result["frames"] + 1, first=result["first"] or now, last=now)
        worker.frame_ready.connect(frame_received)
        worker.camera_error.connect(lambda message: result.update(error=message))

        def finish() -> None:
            worker.stop()
            stopped = worker.wait(4000)
            print(f"CAMERA_INITIALIZED={result['initialized']}")
            print(f"CAMERA_FRAMES={result['frames']}")
            elapsed = max(0.001, result["last"] - result["first"])
            print(f"CAMERA_MEASURED_FPS={(result['frames'] - 1) / elapsed:.1f}")
            print(f"CAMERA_ERROR={result['error'] or 'NONE'}")
            print(f"CAMERA_THREAD_STOPPED={stopped}")
            app.quit()

        worker.start()
        QTimer.singleShot(4500, finish)
        return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
