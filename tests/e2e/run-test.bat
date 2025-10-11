@echo off
REM Helper script to run E2E smoke tests with correct environment setup

echo ============================================================
echo       E2E Test Runner
echo ============================================================
echo.

REM Check if servers are running
echo Checking if servers are running...
curl -s http://localhost:3000 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Frontend not running on port 3000
    echo Please start frontend: cd src/frontend ^&^& npm run dev
    exit /b 1
)

curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend not running on port 8000
    echo Please start backend: cd src/backend ^&^& python run_backend.py
    exit /b 1
)

echo [OK] Servers are running
echo.

REM Set environment variable for smoke tests
set E2E_SMOKE_TESTS=1

REM Run tests with provided arguments or default to all workflows
if "%~1"=="" (
    echo Running all workflow tests...
    npx playwright test workflows --project=chromium --workers=1 --reporter=list
) else (
    echo Running: %*
    npx playwright test %*
)
