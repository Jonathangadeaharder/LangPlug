@echo off
REM Batch script to run unified subtitle maker script with --no-preview flag
REM Runs from the parent directory where the unified script and venv are located

cd /d "%~dp0"

REM Check if venv exists in current directory
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "venv\Scripts\activate.bat"
) else if exist "venv\Scripts\python.exe" (
    echo Using virtual environment python directly...
    set PYTHON_PATH=venv\Scripts\python.exe
    goto :run_script
) else (
    echo Virtual environment not found in current directory.
    echo Looking for system Python...
    set PYTHON_PATH=python
)

:run_script
REM Look for common unified script names
if exist "subtitle_maker.py" (
    set SCRIPT_NAME=subtitle_maker.py
) else if exist "unified_subtitle_maker.py" (
    set SCRIPT_NAME=unified_subtitle_maker.py
) else if exist "unified_subtitle_processor.py" (
    set SCRIPT_NAME=unified_subtitle_processor.py
) else if exist "main.py" (
    set SCRIPT_NAME=main.py
) else (
    echo No unified script found in current directory.
    echo Looking for: subtitle_maker.py, unified_subtitle_maker.py, unified_subtitle_processor.py, main.py
    pause
    exit /b 1
)

echo Running %SCRIPT_NAME% with --no-preview flag...
if defined PYTHON_PATH (
    "%PYTHON_PATH%" "%SCRIPT_NAME%" --no-preview %*
) else (
    python "%SCRIPT_NAME%" --no-preview %*
)

echo.
echo Script finished. Press any key to exit...
pause >nul