@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Keep launcher console alive during cleanup
title Service Launcher

echo ============================================================
echo           LangPlug Full Stack Launcher
echo ============================================================
echo.

REM Resolve repo root relative to this script's directory
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set REPO_ROOT=%SCRIPT_DIR%\..

REM Capture the current launcher console PID so stop-all can avoid killing it
for /f "delims=" %%P in ('powershell -NoProfile -Command "(Get-Process -Id $pid).Parent.Id"') do set LANGPLUG_ACTIVE_CMD_PID=%%P

REM Normalize to absolute path
pushd "%REPO_ROOT%" >nul
set REPO_ROOT=%CD%
popd >nul

REM First stop all existing services for a clean start
echo [CLEANUP] Stopping all existing services...
call "%SCRIPT_DIR%\stop-all.bat"

REM Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo           Starting Fresh LangPlug Stack
echo ============================================================
echo.

REM Configuration - Using default ports
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

echo.
echo [BACKEND] Starting Backend on port %BACKEND_PORT%...

REM Start Backend in new window with AI models (using small models for quick startup)
REM Using /k to keep terminal open for long-running server
REM LANGPLUG_RELOAD=0 to avoid Windows reload mode issues (0=False, 1=True)
start "Backend Server" cmd /k "cd /d "%REPO_ROOT%\src\backend" && api_venv\Scripts\activate && set LANGPLUG_PORT=%BACKEND_PORT%&& set LANGPLUG_RELOAD=0&& echo [INFO] Starting Backend with AI models on port %BACKEND_PORT%... && python run_backend.py"
echo Started Backend with AI models (using small models)
echo Waiting for Backend to initialize...
timeout /t 10 /nobreak >nul

echo.
echo [FRONTEND] Starting Frontend on port %FRONTEND_PORT%...

REM Start Frontend in new window with correct API URL
REM Using /k to keep terminal open for long-running server
start "Frontend Server" cmd /k "cd /d "%REPO_ROOT%\src\frontend" && set VITE_API_URL=http://localhost:%BACKEND_PORT% && echo [INFO] Starting Frontend on port %FRONTEND_PORT% with API at http://localhost:%BACKEND_PORT% && npm run dev"

echo.
echo ============================================================
echo           Services Starting Up
echo ============================================================
echo.
echo Backend:  http://localhost:%BACKEND_PORT%
echo           - API Docs: http://localhost:%BACKEND_PORT%/docs
echo           - Health:   http://localhost:%BACKEND_PORT%/health
echo.
echo Frontend: http://localhost:%FRONTEND_PORT%
echo.
echo ============================================================
echo.
echo Launch sequence complete. Servers running in their own windows.
echo.
echo To stop all services, run: scripts\stop-all.bat
echo.
