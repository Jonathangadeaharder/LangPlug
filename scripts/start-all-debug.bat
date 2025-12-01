@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Keep launcher console alive during cleanup
title Service Launcher - DEBUG MODE

echo ============================================================
echo           LangPlug Full Stack Launcher - DEBUG
echo           (Small/Fast Models)
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
echo           Starting Fresh LangPlug Stack - DEBUG
echo ============================================================
echo.

REM Configuration - Using default ports
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

REM DEBUG MODE: Small/Fast Models
set LANGPLUG_TRANSCRIPTION_SERVICE=whisper-tiny
set LANGPLUG_TRANSLATION_SERVICE=opus-de-es
set LANGPLUG_DEFAULT_LANGUAGE=de

echo.
echo [DEBUG MODE] Model Configuration:
echo   - Transcription: %LANGPLUG_TRANSCRIPTION_SERVICE% (fast)
echo   - Translation:   %LANGPLUG_TRANSLATION_SERVICE% (fast)
echo   - Language:      %LANGPLUG_DEFAULT_LANGUAGE%
echo.

echo.
echo [BACKEND] Starting Backend on port %BACKEND_PORT%...

REM Start Backend in new window with small/fast models
REM Using /k to keep terminal open for long-running server
REM LANGPLUG_RELOAD=0 to avoid Windows reload mode issues (0=False, 1=True)
start "Backend Server (DEBUG)" cmd /k "cd /d "%REPO_ROOT%\src\backend" && "%REPO_ROOT%\api_venv\Scripts\activate" && set LANGPLUG_PORT=%BACKEND_PORT%&& set LANGPLUG_RELOAD=0&& set LANGPLUG_TRANSCRIPTION_SERVICE=%LANGPLUG_TRANSCRIPTION_SERVICE%&& set LANGPLUG_TRANSLATION_SERVICE=%LANGPLUG_TRANSLATION_SERVICE%&& set LANGPLUG_DEFAULT_LANGUAGE=%LANGPLUG_DEFAULT_LANGUAGE%&& echo [INFO] Starting Backend in DEBUG mode with small models on port %BACKEND_PORT%... && python run_backend.py"
echo Started Backend with DEBUG models (whisper-tiny, opus-de-es)
echo Waiting for Backend to initialize...
timeout /t 10 /nobreak >nul

echo.
echo [FRONTEND] Starting Frontend on port %FRONTEND_PORT%...

REM Start Frontend in new window with correct API URL
REM Using /k to keep terminal open for long-running server
start "Frontend Server (DEBUG)" cmd /k "cd /d "%REPO_ROOT%\src\frontend" && set VITE_API_URL=http://localhost:%BACKEND_PORT% && echo [INFO] Starting Frontend on port %FRONTEND_PORT% with API at http://localhost:%BACKEND_PORT% && npm run dev"

echo.
echo ============================================================
echo           Services Starting Up - DEBUG MODE
echo ============================================================
echo.
echo Backend:  http://localhost:%BACKEND_PORT%
echo           - API Docs: http://localhost:%BACKEND_PORT%/docs
echo           - Health:   http://localhost:%BACKEND_PORT%/health
echo.
echo Frontend: http://localhost:%FRONTEND_PORT%
echo.
echo DEBUG MODE: Using small/fast models for quick processing
echo   - Transcription: whisper-tiny
echo   - Translation:   opus-de-es
echo.
echo ============================================================
echo.
echo Launch sequence complete. Servers running in their own windows.
echo.
echo To stop all services, run: scripts\stop-all.bat
echo.
