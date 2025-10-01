# LangPlug Server Management Script
# Provides robust server startup, shutdown, and health checking

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "health")]
    [string]$Action,

    [ValidateSet("backend", "frontend", "both")]
    [string]$Service = "both",

    [int]$TimeoutSeconds = 60
)

# Configuration
$Config = @{
    Backend = @{
        Port = 8000
        Path = "Backend"
        StartCommand = "api_venv\Scripts\python.exe run_backend.py"
        HealthEndpoint = "http://127.0.0.1:8000/health"
        ProcessName = "python"
    }
    Frontend = @{
        Port = 3000
        Path = "Frontend"
        StartCommand = "npm run dev"
        HealthEndpoint = "http://localhost:3000"
        ProcessName = "node"
    }
}

# Helper Functions
function Write-StatusMessage {
    param([string]$Message, [string]$Status = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "White" }
    }
    Write-Host "[$timestamp] " -NoNewline
    Write-Host "$Status" -ForegroundColor $color -NoNewline
    Write-Host ": $Message"
}

function Test-PortAvailable {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -eq $connection
}

function Stop-ServiceOnPort {
    param([int]$Port, [string]$ServiceName)

    Write-StatusMessage "Checking for processes on port $Port..." "INFO"
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
                 Select-Object -ExpandProperty OwningProcess -Unique

    if ($processes) {
        Write-StatusMessage "Found $($processes.Count) process(es) on port $Port. Stopping..." "WARNING"
        foreach ($processId in $processes) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-StatusMessage "Stopped process $processId" "SUCCESS"
            } catch {
                Write-StatusMessage "Failed to stop process $processId`: $_" "ERROR"
            }
        }
        # Wait a moment for processes to clean up
        Start-Sleep -Seconds 2
    }

    # Verify port is now free
    if (Test-PortAvailable -Port $Port) {
        Write-StatusMessage "Port $Port is now available" "SUCCESS"
        return $true
    } else {
        Write-StatusMessage "Port $Port is still occupied after cleanup" "ERROR"
        return $false
    }
}

function Wait-ForHealthCheck {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$TimeoutSeconds = 60,
        [int[]]$FallbackPorts = @()
    )

    Write-StatusMessage "Waiting for $ServiceName to be healthy at $Url..." "INFO"
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    $urlsToTry = @($Url)

    # Add fallback URLs if ports are provided
    if ($FallbackPorts.Length -gt 0) {
        $baseUrl = ($Url -split "://")[0] + "://" + (($Url -split "://")[1] -split ":")[0]
        foreach ($port in $FallbackPorts) {
            $fallbackUrl = "${baseUrl}:${port}"
            if ($fallbackUrl -ne $Url) {
                $urlsToTry += $fallbackUrl
            }
        }
    }

    while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        foreach ($testUrl in $urlsToTry) {
            try {
                $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-StatusMessage "$ServiceName is healthy! Response: $($response.StatusCode) at $testUrl" "SUCCESS"
                    # Update the global config with the working URL for future health checks
                    if ($ServiceName -eq "Frontend" -and $testUrl -ne $Url) {
                        $Config.Frontend.HealthEndpoint = $testUrl
                        $portPart = ($testUrl -split ":")
                        if ($portPart.Length -gt 2) {
                            $Config.Frontend.Port = [int]$portPart[2]
                        }
                    }
                    return $true
                }
            } catch {
                # Continue trying other URLs
            }
        }

        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }

    Write-Host "" # New line after dots
    Write-StatusMessage "$ServiceName health check timed out after $TimeoutSeconds seconds" "ERROR"
    return $false
}

function Start-BackendServer {
    Write-StatusMessage "Starting Backend Server..." "INFO"

    # Stop any existing processes on port 8000
    if (-not (Stop-ServiceOnPort -Port 8000 -ServiceName "Backend")) {
        return $false
    }

    # Change to backend directory and start server
    $backendPath = Join-Path $PWD "Backend"
    if (-not (Test-Path $backendPath)) {
        Write-StatusMessage "Backend directory not found: $backendPath" "ERROR"
        return $false
    }

    try {
        Write-StatusMessage "Starting backend process..." "INFO"
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-Command",
            "cd '$backendPath'; api_venv\Scripts\python.exe run_backend.py"
        ) -PassThru -WindowStyle Hidden

        Write-StatusMessage "Backend process started with PID $($process.Id)" "SUCCESS"

        # Wait for health check
        return Wait-ForHealthCheck -Url $Config.Backend.HealthEndpoint -ServiceName "Backend" -TimeoutSeconds $TimeoutSeconds

    } catch {
        Write-StatusMessage "Failed to start backend: $_" "ERROR"
        return $false
    }
}

function Start-FrontendServer {
    Write-StatusMessage "Starting Frontend Server..." "INFO"

    # Stop any existing processes on port 3000
    if (-not (Stop-ServiceOnPort -Port 3000 -ServiceName "Frontend")) {
        return $false
    }

    # Change to frontend directory and start server
    $frontendPath = Join-Path $PWD "Frontend"
    if (-not (Test-Path $frontendPath)) {
        Write-StatusMessage "Frontend directory not found: $frontendPath" "ERROR"
        return $false
    }

    try {
        Write-StatusMessage "Starting frontend process..." "INFO"
        $process = Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-Command",
            "cd '$frontendPath'; npm run dev"
        ) -PassThru -WindowStyle Hidden

        Write-StatusMessage "Frontend process started with PID $($process.Id)" "SUCCESS"

        # Wait for health check (frontend takes longer to start)
        # Try common development ports in case frontend starts on a different port
        $fallbackPorts = @(3000, 3001, 3002)
        return Wait-ForHealthCheck -Url $Config.Frontend.HealthEndpoint -ServiceName "Frontend" -TimeoutSeconds $TimeoutSeconds -FallbackPorts $fallbackPorts

    } catch {
        Write-StatusMessage "Failed to start frontend: $_" "ERROR"
        return $false
    }
}

function Get-ServiceStatus {
    Write-StatusMessage "Checking Service Status..." "INFO"

    $backendHealthy = $false
    $frontendHealthy = $false

    # Check Backend
    Write-Host "Backend (Port 8000): " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Config.Backend.HealthEndpoint -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "HEALTHY" -ForegroundColor Green
            $backendHealthy = $true
        }
    } catch {
        Write-Host "UNHEALTHY" -ForegroundColor Red
    }

    # Check Frontend - try multiple ports
    $frontendPorts = @(3000, 3001, 3002)
    $frontendPort = "Unknown"

    foreach ($port in $frontendPorts) {
        $testUrl = "http://localhost:$port"
        try {
            $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $frontendPort = $port
                $frontendHealthy = $true
                # Update config with working endpoint
                $Config.Frontend.HealthEndpoint = $testUrl
                $Config.Frontend.Port = $port
                break
            }
        } catch {
            # Continue to next port
        }
    }

    Write-Host "Frontend (Port $frontendPort): " -NoNewline
    if ($frontendHealthy) {
        Write-Host "HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "UNHEALTHY" -ForegroundColor Red
    }

    return @{
        Backend = $backendHealthy
        Frontend = $frontendHealthy
        Overall = $backendHealthy -and $frontendHealthy
    }
}

# Main Logic
Write-StatusMessage "LangPlug Server Management - Action: $Action, Service: $Service" "INFO"

switch ($Action.ToLower()) {
    "start" {
        $success = $true

        if ($Service -eq "backend" -or $Service -eq "both") {
            $success = $success -and (Start-BackendServer)
        }

        if ($Service -eq "frontend" -or $Service -eq "both") {
            $success = $success -and (Start-FrontendServer)
        }

        if ($success) {
            Write-StatusMessage "All requested services started successfully!" "SUCCESS"
            exit 0
        } else {
            Write-StatusMessage "Some services failed to start" "ERROR"
            exit 1
        }
    }

    "stop" {
        if ($Service -eq "backend" -or $Service -eq "both") {
            Stop-ServiceOnPort -Port 8000 -ServiceName "Backend"
        }

        if ($Service -eq "frontend" -or $Service -eq "both") {
            Stop-ServiceOnPort -Port 3000 -ServiceName "Frontend"
        }

        Write-StatusMessage "Stop operation completed" "SUCCESS"
    }

    "restart" {
        # Stop first
        & $PSCommandPath -Action stop -Service $Service
        Start-Sleep -Seconds 3
        # Then start
        & $PSCommandPath -Action start -Service $Service -TimeoutSeconds $TimeoutSeconds
    }

    "status" {
        $status = Get-ServiceStatus
        if ($status.Overall) {
            Write-StatusMessage "All services are healthy!" "SUCCESS"
            exit 0
        } else {
            Write-StatusMessage "Some services are unhealthy" "WARNING"
            exit 1
        }
    }

    "health" {
        # Same as status but with more detailed output
        $status = Get-ServiceStatus
        Write-StatusMessage "Health Check Results:" "INFO"
        Write-StatusMessage "  Backend: $(if ($status.Backend) { 'HEALTHY' } else { 'UNHEALTHY' })" "INFO"
        Write-StatusMessage "  Frontend: $(if ($status.Frontend) { 'HEALTHY' } else { 'UNHEALTHY' })" "INFO"
        Write-StatusMessage "  Overall: $(if ($status.Overall) { 'HEALTHY' } else { 'UNHEALTHY' })" "INFO"

        exit $(if ($status.Overall) { 0 } else { 1 })
    }
}
