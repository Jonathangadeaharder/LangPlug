@echo off
call "%~dp0venv\Scripts\activate.bat"
"%~dp0venv\Scripts\python.exe" "%~dp0unified_subtitle_processor.py"
pause