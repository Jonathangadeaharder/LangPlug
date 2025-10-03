@echo off
echo Starting LangPlug Backend...
echo.

REM Set environment to skip heavy service initialization
set TESTING=1

REM Activate virtual environment
call api_venv\Scripts\activate

REM Start the server
echo [INFO] Starting server in fast mode (AI services disabled)
echo [INFO] Server will run on http://localhost:8001
echo.
python start_backend_fast.py
