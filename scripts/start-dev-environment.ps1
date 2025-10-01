# LangPlug Development Environment Startup Script
# This script ensures both backend and frontend are properly started and healthy before proceeding

param(
    [int]$TimeoutSeconds = 120,
    [switch]$SkipE2E
)

$ErrorActionPreference = "Stop"

# Define the server management script path
$ManageServersScript = "$PSScriptRoot\manage-servers.ps1"

function Write-DevMessage {
    param([string]$Message, [string]$Status = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host "[$timestamp] " -NoNewline
    Write-Host "DEV-ENV" -ForegroundColor $color -NoNewline
    Write-Host ": $Message"
}

Write-DevMessage "Starting LangPlug Development Environment..." "INFO"

# Step 1: Clean up any existing processes
Write-DevMessage "Cleaning up existing processes..." "INFO"
& $ManageServersScript -Action stop -Service both

# Step 2: Start both servers
Write-DevMessage "Starting backend and frontend servers..." "INFO"
$startResult = & $ManageServersScript -Action start -Service both -TimeoutSeconds $TimeoutSeconds

if ($LASTEXITCODE -ne 0) {
    Write-DevMessage "Failed to start servers. Attempting diagnostic..." "ERROR"

    # Try to get more information
    & $ManageServersScript -Action status

    Write-DevMessage "Development environment startup failed!" "ERROR"
    exit 1
}

# Step 3: Final health check
Write-DevMessage "Performing final health check..." "INFO"
$healthResult = & $ManageServersScript -Action health

if ($LASTEXITCODE -eq 0) {
    Write-DevMessage "✅ Development environment is ready!" "SUCCESS"
    Write-DevMessage "  Backend: http://127.0.0.1:8000" "SUCCESS"
    Write-DevMessage "  Frontend: http://localhost:3000" "SUCCESS"
    Write-DevMessage "  API Docs: http://127.0.0.1:8000/docs" "SUCCESS"

    if (-not $SkipE2E) {
        Write-DevMessage "Environment is ready for E2E testing!" "SUCCESS"
    }

    exit 0
} else {
    Write-DevMessage "❌ Some services are not healthy" "ERROR"
    Write-DevMessage "Run 'scripts\\manage-servers.ps1 -Action status' for details" "ERROR"
    exit 1
}
