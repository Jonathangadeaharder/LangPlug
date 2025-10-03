# LangPlug Test Suite Execution Script
# PowerShell script to run all tests with proper configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "     LangPlug Complete Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set start time
$startTime = Get-Date

# Frontend Tests
Write-Host "[1/3] Running Frontend Tests..." -ForegroundColor Yellow
Write-Host "----------------------------------------"
Set-Location Frontend
npm test -- --run --reporter=verbose 2>&1 | Select-String "Test Files|Tests|passed|failed" -Context 0,1 | Select-Object -Last 5
$frontendStatus = $LASTEXITCODE
Write-Host ""

# Backend Tests
Write-Host "[2/3] Running Backend Tests..." -ForegroundColor Yellow
Write-Host "----------------------------------------"
Set-Location ../Backend
. api_venv/Scripts/activate
$env:TESTING = "1"
$env:ANYIO_BACKEND = "asyncio"
python -m pytest tests/unit/core tests/unit/models tests/unit/test_game_models.py --tb=short -q --timeout=30
$backendStatus = $LASTEXITCODE
Write-Host ""

# Contract Tests
Write-Host "[3/3] Running Contract Tests..." -ForegroundColor Yellow
Write-Host "----------------------------------------"
Set-Location ../Frontend
npm run test:contract 2>&1 | Select-String "Test|pass|fail" | Select-Object -Last 5
$contractStatus = $LASTEXITCODE
Write-Host ""

# Calculate duration
$endTime = Get-Date
$duration = $endTime - $startTime

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "          Test Suite Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($frontendStatus -eq 0) {
    Write-Host "[PASS] Frontend Tests" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Frontend Tests (Exit: $frontendStatus)" -ForegroundColor Red
}

if ($backendStatus -eq 0) {
    Write-Host "[PASS] Backend Tests" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Backend Tests (Exit: $backendStatus)" -ForegroundColor Red
}

if ($contractStatus -eq 0) {
    Write-Host "[PASS] Contract Tests" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Contract Tests (Exit: $contractStatus)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Total Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor Cyan
Write-Host ""

# Return to root
Set-Location ..

# Exit with appropriate code
$totalStatus = $frontendStatus + $backendStatus + $contractStatus
if ($totalStatus -eq 0) {
    Write-Host "All tests passed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Please review the output above." -ForegroundColor Yellow
    exit 1
}
