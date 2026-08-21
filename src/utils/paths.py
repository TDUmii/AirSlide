"""Runtime paths that work from source and from a PyInstaller bundle."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the read-only resource root."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def writable_root() -> Path:
    """Return the directory where settings and logs can persist."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return project_root()


def resource_path(*parts: str) -> Path:
    return project_root().joinpath(*parts)


def writable_path(*parts: str) -> Path:
    path = writable_root().joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
