@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo AirSlide virtual environment was not found.
    echo.
    echo Create it with:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo   .venv\Scripts\python.exe scripts\download_model.py
    echo.
    pause
    exit /b 1
)

endlocal
