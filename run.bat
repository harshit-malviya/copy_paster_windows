@echo off
title Click-to-Paste Automation Launcher
echo ========================================================
echo         Click-to-Paste Automation Tool
echo ========================================================
echo.

:: Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: Check / create virtual environment
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install / verify dependencies
echo [*] Checking dependencies...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pip install had issues, retrying...
    pip install -r requirements.txt
)

echo [*] Launching Click-to-Paste GUI...
python main.py

echo.
echo Application closed.
pause
