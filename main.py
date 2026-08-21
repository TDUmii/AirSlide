"""AirSlide application entry point."""

from __future__ import annotations

import importlib.util
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.logger import configure_logging

RUNTIME_DEPENDENCIES = {
    "cv2": "opencv-contrib-python (cv2)",
    "mediapipe": "mediapipe",
    "numpy": "numpy",
    "pyautogui": "PyAutoGUI",
}


def missing_runtime_dependencies() -> list[str]:
    """Return friendly package names missing from the active interpreter."""
    return [
        package_name
        for module_name, package_name in RUNTIME_DEPENDENCIES.items()
        if importlib.util.find_spec(module_name) is None
    ]


def main() -> int:
    logger = configure_logging()
    logger.info("AirSlide started")
    app = QApplication(sys.argv)
    app.setApplicationName("AirSlide")
    app.setOrganizationName("AirSlide")
    app.setQuitOnLastWindowClosed(True)
    missing = missing_runtime_dependencies()
    if missing:
        message = (
            "AirSlide is running with a Python environment that is missing:\n\n"
            + "\n".join(f"• {name}" for name in missing)
            + "\n\nRun AirSlide with:\n"
            + r".\.venv\Scripts\python.exe main.py"
            + "\n\nOr install dependencies with:\n"
            + r"python -m pip install -r requirements.txt"
        )
        logger.error("Missing runtime dependencies: %s", ", ".join(missing))
        QMessageBox.critical(None, "AirSlide dependencies missing", message)
        return 2
    window = MainWindow(ConfigManager())
    window.show()
    try:
        return app.exec()
    finally:
        logger.info("AirSlide stopped")


if __name__ == "__main__":
    raise SystemExit(main())
