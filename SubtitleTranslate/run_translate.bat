@echo off
REM Batch file to run subtitle translation with virtual environment from parent directory
REM This assumes the virtual environment is in the parent directory

echo Starting Subtitle Translation Tool...
echo.

REM Check if virtual environment exists in parent directory
set VENV_ACTIVATED=0

if exist "..\venv\Scripts\activate.bat" (
    echo Found virtual environment in parent directory
    call "..\venv\Scripts\activate.bat"
    set VENV_ACTIVATED=1
    goto :continue
)

if exist "..\env\Scripts\activate.bat" (
    echo Found virtual environment ^(env^) in parent directory
    call "..\env\Scripts\activate.bat"
    set VENV_ACTIVATED=1
    goto :continue
)

if exist "..\subtitle_env\Scripts\activate.bat" (
    echo Found virtual environment ^(subtitle_env^) in parent directory
    call "..\subtitle_env\Scripts\activate.bat"
    set VENV_ACTIVATED=1
    goto :continue
)

echo Warning: No virtual environment found in parent directory
echo Looking for common venv names: venv, env, subtitle_env
echo Continuing without virtual environment...
echo.

:continue

REM Change to the script directory
cd /d "%~dp0"

REM Run the subtitle translation script
echo Running subtitle_translate.py...
echo.
python subtitle_translate.py

REM Check if the script ran successfully
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: Script execution failed with error code %ERRORLEVEL%
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Translation completed successfully!
echo.
pause