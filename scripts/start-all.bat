@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Resolve repo root relative to this script's directory
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set REPO_ROOT=%SCRIPT_DIR%\..

REM Normalize to absolute path
pushd "%REPO_ROOT%" >nul
set REPO_ROOT=%CD%
popd >nul

REM Start backend in a new window
start "LangPlug Backend" cmd /k "cd /d "%REPO_ROOT%\Backend" && echo Starting Backend... && api_venv\Scripts\python.exe run_backend.py"

REM Start frontend in a new window
start "LangPlug Frontend" cmd /k "cd /d "%REPO_ROOT%\Frontend" && echo Starting Frontend... && npm run dev"

REM Auto-close this launcher window
timeout /t 2 >nul
taskkill /F /PID %CMDCMDLINE:"=% >nul 2>&1
