@echo off
cd /d "%~dp0"
echo Testing backend startup...
api_venv\Scripts\python.exe debug_startup.py > startup_log.txt 2>&1
echo.
echo === Startup Log ===
type startup_log.txt
echo.
echo === End of Log ===
pause
