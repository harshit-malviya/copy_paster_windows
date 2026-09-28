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

echo [*] Running PyInstaller build...
pyinstaller --noconfirm --onedir --windowed ^
    --name "ClickToPaste" ^
    --icon "assets/icon.ico" ^
    --add-data "assets;assets" ^
    --collect-all "customtkinter" ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  BUILD SUCCESSFUL!
    echo  Executable is ready at: dist\ClickToPaste\ClickToPaste.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed. Check the output above.
)

pause
