# AirSlide

**AI Gesture Presentation Controller** is a local Windows desktop application that uses a webcam and MediaPipe's pretrained Hand Landmarker to move through presentation slides with deliberate open-palm swipes.

AirSlide sends only the configured `Right Arrow` and `Left Arrow` keys. It does not open, modify, or connect directly to presentation files. It uses no cloud AI service, account, database, telemetry, or paid API.

## Features

- Open Palm + Swipe Right → Next Slide
- Open Palm + Swipe Left → Previous Slide
- Distance, speed, horizontal-dominance, direction-consistency, and dead-zone checks
- Separate cooldown and physical rearm gates for one action per swipe
- Stable palm center computed from wrist and four MCP joints
- MediaPipe Tasks Hand Landmarker with a local pretrained model
- Mirrored, aspect-ratio-preserving preview with optional landmarks, trajectory, and FPS
- PySide6 camera worker thread plus non-blocking MediaPipe live-stream inference; widgets are updated only through Qt signals
- Start/Stop control, F8 in-app shortcut, presentation mode, and system tray menu
- Light, dark, and system themes
- Guided statistical calibration using three right and three left swipes
- JSON settings with validation and safe recovery from malformed files
- Rotating local logs and explicit camera/model/keyboard error handling
- Deterministic gesture tests that do not need a webcam

## Screenshot

The application opens directly to a dashboard with a large camera preview, real-time status card, action feedback, and a single prominent **Start Control** button. A repository screenshot is intentionally not fabricated; run the app to capture the dashboard on the target webcam and Windows theme.

## Architecture

```text
Webcam → OpenCV → MediaPipe Hand Landmarker → HandObservation
                                                ↓
                                    Palm center + open-palm score
                                                ↓
                  GestureDetector → GestureStateMachine → GestureEvent
                                                              ↓
PySide6 UI ← QThread signals                         SlideController
                                                              ↓
                                                  PyAutoGUI Left/Right
```

The gesture detector accepts only `timestamp`, normalized palm coordinates, open-palm state, and confidence. It does not import OpenCV, MediaPipe, PySide6, or PyAutoGUI, so motion behavior can be tested with synthetic trajectories.

### Swipe acceptance

A gesture must satisfy all of the following:

1. A hand is present and at least three of the four non-thumb fingers are strongly extended.
2. Smoothed palm displacement reaches the configured distance within the rolling gesture window.
3. Absolute horizontal velocity reaches the minimum velocity.
4. Horizontal displacement dominates vertical displacement.
5. At least 74% of meaningful frame-to-frame movement agrees with the final direction.
6. The state machine is armed.

After a trigger, AirSlide enters cooldown and then **Wait for Rearm**. It rearms only after a short, observable reset: hand disappearance, closing the palm, returning near center, or holding the hand still. This is intentionally conservative.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 recommended (the validated environment is Python 3.11.3)
- A webcam
- Approximately 500 MB for the virtual environment and build dependencies

The pinned runtime set was resolver-checked together on Windows/Python 3.11:

- PySide6 6.11.2
- OpenCV Contrib Python 5.0.0.93 (MediaPipe's required OpenCV distribution)
- MediaPipe 0.10.35 (Tasks API)
- NumPy 2.4.6
- PyAutoGUI 0.9.54

MediaPipe 0.10.35 is pinned because AirSlide uses its verified Tasks API surface (`mp.tasks.vision.HandLandmarker`) and that release carries a correct Windows wheel tag. This is the non-legacy Hand Landmarker API, not the deprecated `mp.solutions.hands` interface. MediaPipe requires `opencv-contrib-python`; AirSlide therefore installs that distribution only and avoids the unsupported state caused by installing multiple OpenCV wheel variants together.

## Installation

From the `AirSlide` directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\download_model.py
```

The model downloader retrieves Google's official `hand_landmarker.task` float16 bundle and writes it to `models/hand_landmarker.task`. The main application never downloads anything. Once installed, AirSlide runs completely offline.

## Run

```powershell
python main.py
```

To avoid accidentally using a different global Python installation on Windows,
you can run the included launcher instead:

```powershell
.\run_airslide.cmd
```

The launcher always uses `.venv\Scripts\python.exe`. AirSlide also performs a
startup dependency check and shows a clear installation message instead of
allowing a missing OpenCV/MediaPipe module to fail inside the camera thread.

On first launch:

1. Allow Windows camera access if prompted.
2. Keep an open palm visible around the middle of the preview.
3. Try swiping while control is off; the dashboard still shows detections without sending keys.
4. Open **Calibrate** if the defaults do not match your camera distance or natural speed.
5. Press **Start Control**.
6. Focus the PowerPoint, Google Slides, Canva, Prezi, or PDF presentation window.
7. Swipe right or left. AirSlide sends the key to whichever application is active.

AirSlide never foregrounds PowerPoint and never sends Enter, Escape, Alt+F4, or mouse clicks.

## Gesture guide

- Face the palm toward the webcam; the thumb may remain relaxed.
- Start near the center third of the frame.
- Move in one clear horizontal direction for roughly 20–45 cm in the real world.
- Pause, return to center, close the palm, or briefly leave the frame before the next swipe.
- Avoid letting a bright window sit directly behind the hand.

The mirrored preview matches selfie-camera expectations: moving your visible hand to your right produces **Swipe Right**.

## Settings

Settings persist in `config/settings.json` beside the source tree or beside `AirSlide.exe` in the packaged app.

### Camera

- Camera device index
- 640 × 480 or 1280 × 720
- Mirror camera

### Gesture

- Low, Medium, High, or Custom sensitivity
- Swipe distance threshold
- Minimum normalized velocity
- Gesture history window
- Cooldown duration (300–2000 ms)
- Horizontal tolerance

Low sensitivity requires a larger, faster movement. High sensitivity accepts a smaller, slower movement.

### Control and interface

- Right/Left arrow mapping
- Auto, Left Hand, or Right Hand selection
- System, Light, or Dark theme
- Landmarks, FPS, and debug telemetry

If JSON is malformed or out of range, AirSlide logs a warning, restores safe defaults, and continues instead of crashing.

## Calibration

Calibration temporarily keeps presentation control off. It asks for three right swipes and then three left swipes. From accepted samples it calculates average distance, velocity, and duration, then proposes conservative thresholds:

- distance threshold ≈ 72% of average observed distance
- velocity threshold ≈ 58% of average observed velocity
- history window derived from average duration and clamped to a safe range

No training or machine learning occurs during calibration.

## Debug mode

Enable **Settings → Interface → Debug mode** to see:

- 21 landmarks and hand connections
- stable palm center and recent trajectory
- normalized palm X/Y and ΔX/ΔY
- velocity, direction consistency, progress, open-palm score, state, and moving-average FPS

History is bounded by both a short time window and fixed trajectory deque; it cannot grow without limit.

## Tests

Install development dependencies and run:

```powershell
pip install -r requirements-dev.txt
pytest -q
python -m compileall -q main.py src tests scripts
python scripts\smoke_test.py
```

The suite covers right and left swipes, jitter, small movement, slow movement, vertical movement, direction reversals, closed palm, no hand, cooldown, rearm, calibration, settings recovery, and the keyboard controller boundary.

Real camera quality depends on hardware and lighting, so complete final acceptance on the target laptop:

```text
Open palm still           → no action
Open palm jitter          → no action
Slow horizontal movement  → no action
Fast right swipe          → exactly one next action
Fast left swipe           → exactly one previous action
Closed-palm movement      → no action
Rapid repeat              → blocked until cooldown + rearm
```

## Build the Windows EXE

The project intentionally uses an **onedir** build. Native Qt, OpenCV, MediaPipe, and model files are more reliable and easier to diagnose in a folder than in a self-extracting one-file executable.

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts\download_model.py
pyinstaller --noconfirm --clean AirSlide.spec
```

Output:

```text
dist/
└── AirSlide/
    ├── AirSlide.exe
    └── _internal/
```

Copy the entire `dist/AirSlide` folder. Do not copy only the executable. On first packaged launch, writable `config/settings.json` and `logs/airslide.log` are created beside the executable.

## Troubleshooting

### Camera is unavailable

- Close Teams, Zoom, OBS, browser camera tabs, and other camera users.
- Check **Windows Settings → Privacy & security → Camera**.
- Choose another device index in AirSlide Settings.
- Press **Retry Camera**.

### Model not found or cannot load

Run:

```powershell
python scripts\download_model.py --force
```

Confirm `models/hand_landmarker.task` is larger than 1 MB. For a packaged build, rebuild after the model exists; the spec bundles it.

### Swipe appears backward

Keep **Mirror Camera** enabled for natural selfie behavior. If it is disabled, gesture coordinates follow the unmirrored camera image.

### False positives

- Select **Low** sensitivity.
- Increase Swipe Distance or Minimum Velocity.
- Increase Horizontal Tolerance.
- Keep the palm open only when intending to control slides.

### Swipe is not detected

- Use Calibration.
- Select **High** sensitivity.
- Improve lighting and keep the entire palm in frame.
- Verify the correct control hand setting.

### Log location

See `logs/airslide.log`. Logs rotate at 1.5 MB with three backups and do not write per frame.

## Project structure

```text
AirSlide/
├── main.py
├── AirSlide.spec
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── LICENSE
├── assets/
│   └── icon.svg
├── config/
│   └── settings.json
├── models/
│   └── hand_landmarker.task     # downloaded official model
├── scripts/
│   ├── download_model.py
│   └── smoke_test.py
├── src/
│   ├── core/
│   │   ├── calibration.py
│   │   ├── camera_worker.py
│   │   ├── gesture_detector.py
│   │   ├── gesture_state_machine.py
│   │   ├── hand_tracker.py
│   │   └── slide_controller.py
│   ├── ui/
│   │   ├── calibration_dialog.py
│   │   ├── main_window.py
│   │   ├── settings_dialog.py
│   │   └── styles.py
│   └── utils/
│       ├── config_manager.py
│       ├── logger.py
│       └── paths.py
└── tests/
```

## Known limitations

- F8 is an application shortcut, not a system-wide hotkey. It works while an AirSlide window is focused; the tray menu remains available otherwise. A global hook was intentionally avoided in V1 to reduce permission and stability issues.
- Gesture thresholds are normalized image-space values. Camera field of view and user distance vary, so calibration on the presentation laptop is recommended.
- MediaPipe handedness is inferred from the mirrored input. Extreme occlusion or two overlapping hands can still cause a temporary tracking loss; AirSlide favors the previously tracked handedness to avoid rapid switching.
- Synthetic tests validate decision logic, but a real webcam acceptance pass is still required for each room, camera, and lighting setup.

## Roadmap

- V1 — Swipe slide control
- V2 — Finger pointer
- V3 — Virtual laser pointer
- V4 — Pinch click
- V5 — Custom gesture mapping
- V6 — Presenter analytics

V2–V6 are not implemented in this release, keeping V1 focused on reliable slide navigation.
