@echo off
REM ============================================
REM OpenClaw Gateway Tray Tool - Build Script
REM Using PyInstaller
REM ============================================

echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller --onefile ^
    --windowed ^
    --name "OpenClawGateway" ^
    --icon=NONE ^
    --add-data "openclaw_tray.py;." ^
    --uac-admin ^
    --clean ^
    openclaw_tray.py

echo.
echo [3/3] Build complete!
echo Executable location: dist\OpenClawGateway.exe
echo.
echo You can now distribute: dist\OpenClawGateway.exe
pause
