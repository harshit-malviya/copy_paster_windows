@echo off
title Build Standalone Executable
echo ========================================================
echo       Building Click-to-Paste Standalone EXE
echo ========================================================
echo.

if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo [*] Ensuring PyInstaller and dependencies are installed...
pip install -r requirements.txt

echo [*] Running PyInstaller build using ClickToPaste.spec...
pyinstaller --noconfirm ClickToPaste.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  BUILD SUCCESSFUL!
    echo  Executable is ready at: dist\ClickToPaste.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed. Check the output above.
)

pause
