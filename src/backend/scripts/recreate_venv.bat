@echo off
REM Recreate the virtual environment with correct paths

cd /d "%~dp0"

echo Removing old virtual environment...
if exist api_venv (
    rmdir /s /q api_venv
    echo Old venv removed.
)

echo Creating new virtual environment...
python -m venv api_venv
if errorlevel 1 (
    echo Failed to create virtual environment. Make sure Python is installed and in PATH.
    pause
    exit /b 1
)

echo Activating virtual environment...
call api_venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Virtual environment recreated successfully!
echo Location: %CD%\api_venv
echo.
echo To activate: api_venv\Scripts\activate
pause
