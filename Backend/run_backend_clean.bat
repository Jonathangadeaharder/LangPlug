@echo off
echo ============================================================
echo           LangPlug Backend - Clean Startup
echo ============================================================
echo.

REM First clean up any existing processes on our ports
echo [CLEANUP] Killing processes on Backend ports...
powershell -Command "Get-NetTCPConnection -LocalPort 8000,8001,8002,8003 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
echo [CLEANUP] Ports cleaned

REM Activate virtual environment
echo [INFO] Activating Python virtual environment...
call api_venv\Scripts\activate

REM Ask user which mode to run
echo.
echo Select startup mode:
echo 1) Fast mode (no AI models) - Port 8003
echo 2) Full mode (with AI models and progress) - Port 8003
echo.
set /p MODE="Enter choice (1 or 2): "

if "%MODE%"=="1" (
    echo.
    echo [INFO] Starting Backend in FAST mode...
    python start_backend_fast.py
) else if "%MODE%"=="2" (
    echo.
    echo [INFO] Starting Backend with AI models...
    python start_backend_with_models.py
) else (
    echo Invalid choice. Defaulting to fast mode...
    python start_backend_fast.py
)
