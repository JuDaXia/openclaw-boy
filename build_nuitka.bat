@echo off
REM ============================================
REM OpenClaw Gateway Tray Tool - Build Script
REM Using Nuitka (Smaller size, faster startup)
REM ============================================

echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install nuitka ordered-set zstandard

echo.
echo [2/3] Building executable with Nuitka...
echo This may take 5-10 minutes on first build...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --enable-plugin=tk-inter ^
    --windows-icon-from-ico=NONE ^
    --output-dir=dist ^
    --output-filename=OpenClawGateway.exe ^
    --assume-yes-for-downloads ^
    openclaw_tray.py

echo.
echo [3/3] Build complete!
echo Executable location: dist\OpenClawGateway.exe
echo.
echo Nuitka produces smaller and faster executables than PyInstaller
echo You can now distribute: dist\OpenClawGateway.exe
pause
