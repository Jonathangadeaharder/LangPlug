# PowerShell script to start Backend quickly
Write-Host "Starting LangPlug Backend..." -ForegroundColor Green
Write-Host ""

# Set environment to skip heavy service initialization
$env:TESTING = "1"

# Activate virtual environment
& ".\api_venv\Scripts\activate.ps1"

# Start the server
Write-Host "[INFO] Starting server in fast mode (AI services disabled)" -ForegroundColor Yellow
Write-Host "[INFO] Server will run on http://localhost:8001" -ForegroundColor Yellow
Write-Host ""

python start_backend_fast.py
