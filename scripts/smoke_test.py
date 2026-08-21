"""Headless UI startup/shutdown check used before packaging."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["AIRSLIDE_SKIP_CAMERA"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.utils.config_manager import ConfigManager


def main() -> int:
    app = QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        config = ConfigManager(Path(directory) / "settings.json")
        settings = config.settings
        settings["show_onboarding"] = False
        config.save(settings)
        window = MainWindow(config)
        window.show()
        QTimer.singleShot(150, window.close)
        result = app.exec()
    print("UI_STARTUP_SHUTDOWN=PASS")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
