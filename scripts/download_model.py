"""Download the official MediaPipe Hand Landmarker model bundle once."""

from __future__ import annotations

import argparse
import shutil
import urllib.request
from pathlib import Path

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
DESTINATION = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"


def download(force: bool = False) -> Path:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists() and DESTINATION.stat().st_size > 1_000_000 and not force:
        print(f"Model already available: {DESTINATION}")
        return DESTINATION
    temporary = DESTINATION.with_suffix(".download")
    request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "AirSlide/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if temporary.stat().st_size < 1_000_000:
            raise RuntimeError("Downloaded model is unexpectedly small")
        temporary.replace(DESTINATION)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Downloaded {DESTINATION.name} ({DESTINATION.stat().st_size:,} bytes)")
    return DESTINATION


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace an existing model")
    download(parser.parse_args().force)
