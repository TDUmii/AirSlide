"""AirSlide application entry point."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.logger import configure_logging


def main() -> int:
    logger = configure_logging()
    logger.info("AirSlide started")
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setApplicationName("AirSlide")
    app.setOrganizationName("AirSlide")
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow(ConfigManager())
    window.show()
    try:
        return app.exec()
    finally:
        logger.info("AirSlide stopped")


if __name__ == "__main__":
    raise SystemExit(main())
