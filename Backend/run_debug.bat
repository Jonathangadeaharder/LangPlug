@echo off
cd /d "%~dp0"
echo Starting backend with error capture...
api_venv\Scripts\python.exe run_backend.py > debug_output.txt 2>&1
echo.
echo === Backend Output ===
type debug_output.txt
echo.
echo === End Output ===
pause
