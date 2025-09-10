@echo off
REM LangPlug Backend - Main Entry Point
REM Always use this file to start the backend

echo.
echo ================================
echo   LangPlug Backend Startup
echo ================================
echo.

REM Change to backend directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "api_venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please create the virtual environment first:
    echo   python -m venv api_venv
    echo   api_venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [INFO] Virtual environment found
echo [INFO] Starting LangPlug Backend...
echo.

REM Run the backend using the comprehensive startup script
api_venv\Scripts\python.exe run_backend.py

echo.
echo Backend stopped. Press any key to exit...
pause >nul
