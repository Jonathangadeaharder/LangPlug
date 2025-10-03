@echo off
echo ============================================================
echo           LangPlug Full Stack Startup
echo ============================================================
echo.

REM Set the Backend port we want to use
set BACKEND_PORT=8000

REM Kill any existing processes on our ports
echo [CLEANUP] Stopping any existing services...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
powershell -Command "Get-NetTCPConnection -LocalPort %BACKEND_PORT%,3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
echo [CLEANUP] Ports cleared
echo.

REM Ask user which Backend mode to run
echo Select Backend startup mode:
echo 1) Fast mode (no AI models)
echo 2) Full mode (with AI models)
echo.
set /p MODE="Enter choice (1 or 2): "

REM Start Backend in new window
echo [BACKEND] Starting Backend on port %BACKEND_PORT%...
if "%MODE%"=="1" (
    start "LangPlug Backend" cmd /k "cd Backend && api_venv\Scripts\activate && set LANGPLUG_PORT=%BACKEND_PORT% && python -c \"import os; os.environ['TESTING']='1'; os.environ['LANGPLUG_PORT']='%BACKEND_PORT%'; import uvicorn; from core.config import settings; from cleanup_port import kill_process_on_port; kill_process_on_port(%BACKEND_PORT%); print('[INFO] Starting Backend in FAST mode on port %BACKEND_PORT%'); uvicorn.run('core.app:app', host='127.0.0.1', port=%BACKEND_PORT%, log_level='info', reload=False)\""
) else (
    start "LangPlug Backend" cmd /k "cd Backend && api_venv\Scripts\activate && set LANGPLUG_PORT=%BACKEND_PORT% && python -c \"import os; os.environ['LANGPLUG_PORT']='%BACKEND_PORT%'; import uvicorn; from core.config import settings; from cleanup_port import kill_process_on_port; kill_process_on_port(%BACKEND_PORT%); print('[INFO] Starting Backend with AI models on port %BACKEND_PORT%'); uvicorn.run('core.app:app', host='127.0.0.1', port=%BACKEND_PORT%, log_level='info', reload=False)\""
)

REM Wait for Backend to start
echo [WAIT] Waiting for Backend to initialize...
timeout /t 5 /nobreak >nul

REM Start Frontend in new window with correct Backend URL
echo [FRONTEND] Starting Frontend with Backend at http://localhost:%BACKEND_PORT%...
start "LangPlug Frontend" cmd /k "cd Frontend && set VITE_API_URL=http://localhost:%BACKEND_PORT% && npm run dev"

echo.
echo ============================================================
echo Services are starting up:
echo - Backend:  http://localhost:%BACKEND_PORT%
echo - Frontend: http://localhost:3000
echo ============================================================
echo.
echo Press any key to open the application in your browser...
pause >nul
start http://localhost:3000
