"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import writable_path


def configure_logging() -> logging.Logger:
    """Configure a bounded file log without duplicating handlers."""
    logger = logging.getLogger("airslide")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        writable_path("logs", "airslide.log"),
        maxBytes=1_500_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
