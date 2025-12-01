$ErrorActionPreference = "Stop"

Write-Host "Cleaning up existing environment..." -ForegroundColor Cyan

if (Test-Path "api_venv") {
    Remove-Item -Path "api_venv" -Recurse -Force
    Write-Host "Removed existing api_venv." -ForegroundColor Green
}

Write-Host "Running setup_project.py with Python 3.11..." -ForegroundColor Cyan
py -3.11 setup_project.py --backend --dev

Write-Host "Environment setup complete." -ForegroundColor Green
Write-Host "To activate: . .\api_venv\Scripts\Activate.ps1" -ForegroundColor Yellow
