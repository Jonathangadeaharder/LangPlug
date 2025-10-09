@echo off
echo ============================================================
echo           Stopping All LangPlug Services
echo ============================================================
echo.

REM Kill cmd windows started by start-all.bat (identified by their command line)
echo [1/5] Closing LangPlug cmd terminal windows...
powershell -Command "& { $active = $env:LANGPLUG_ACTIVE_CMD_PID; Get-WmiObject Win32_Process -Filter \"Name='cmd.exe'\" | Where-Object { ($_.CommandLine -match 'LangPlug\\\\src\\\\backend.*run_backend' -or $_.CommandLine -match 'LangPlug\\\\src\\\\frontend.*npm run dev') -and (-not $active -or $_.ProcessId -ne [int]$active) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }"

REM Kill Python processes ONLY if they're running LangPlug-related scripts
echo [2/5] Killing LangPlug Python processes...
powershell -Command "& { Get-WmiObject Win32_Process -Filter \"Name LIKE 'python%%'\" | Where-Object { $_.CommandLine -match 'LangPlug\\\\src\\\\backend|run_backend|uvicorn|multiprocessing' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }"

REM Kill Node processes ONLY if they're running in LangPlug directories
echo [3/5] Killing LangPlug Node.js processes...
powershell -Command "& { Get-WmiObject Win32_Process -Filter \"Name='node.exe'\" | Where-Object { $_.CommandLine -match 'LangPlug\\\\src\\\\frontend|vite' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }"

REM Kill processes on all common ports (8000-8003, 3000-3002, 5173)
echo [4/5] Clearing LangPlug ports...
powershell -Command "& { $ports = @(8000, 8001, 8002, 8003, 3000, 3001, 3002, 5173); foreach ($port in $ports) { Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } } }"

REM Final cleanup: Kill any remaining cmd windows that are running LangPlug scripts
echo [5/5] Closing remaining LangPlug terminal windows...
powershell -Command "& { $active = $env:LANGPLUG_ACTIVE_CMD_PID; Get-WmiObject Win32_Process -Filter \"Name='cmd.exe'\" | Where-Object { $_.CommandLine -match 'LangPlug' -and (-not $active -or $_.ProcessId -ne [int]$active) -and $_.CommandLine -notmatch 'stop-all' -and $_.CommandLine -notmatch 'start-all' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }"

REM Kill WSL LangPlug processes if WSL is installed (optional)
powershell -Command "& { if (Get-Command wsl -ErrorAction SilentlyContinue) { wsl pkill -f 'langplug' 2>$null; wsl pkill -f 'uvicorn.*8000' 2>$null; wsl pkill -f 'vite.*3000' 2>$null } }" >nul 2>&1

echo.
echo ============================================================
echo           All LangPlug services stopped!
echo ============================================================
echo.
