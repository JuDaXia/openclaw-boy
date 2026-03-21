@echo off
REM ============================================
REM Quick test script - Run before building
REM ============================================

echo Testing OpenClaw Gateway Tray Tool...
echo.
echo [1/2] Checking Python dependencies...
pip show pystray >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pystray not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

pip show Pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Pillow not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo OK - Dependencies installed
echo.
echo [2/2] Starting program...
echo Close the tray icon window to stop
echo.
python openclaw_tray.py
