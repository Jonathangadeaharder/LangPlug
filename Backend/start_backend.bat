@echo off
REM LangPlug Backend Startup Script
echo Starting LangPlug Backend...

REM Change to backend directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "api_venv\Scripts\python.exe" (
    echo Error: Virtual environment not found at api_venv\Scripts\python.exe
    echo Please create the virtual environment first
    pause
    exit /b 1
)

REM Activate virtual environment and run the application
echo Activating virtual environment...
call api_venv\Scripts\activate.bat

echo Testing environment...
python test_env.py

echo Starting FastAPI server...
python main.py

pause
