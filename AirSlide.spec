# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

mediapipe_data = collect_data_files("mediapipe")
mediapipe_bins = collect_dynamic_libs("mediapipe")
mediapipe_hidden = [
    "mediapipe.tasks.python",
    "mediapipe.tasks.python.core.base_options",
    "mediapipe.tasks.python.vision",
    "mediapipe.tasks.python.vision.hand_landmarker",
    "mediapipe.tasks.python.vision.core.vision_task_running_mode",
]

a = Analysis(
    ["main.py"],
    pathex=[SPECPATH],
    binaries=mediapipe_bins,
    datas=[
        ("assets", "assets"),
        ("models/hand_landmarker.task", "models"),
    ] + mediapipe_data,
    hiddenimports=mediapipe_hidden + ["pyautogui", "cv2", "numpy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AirSlide",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AirSlide",
)
