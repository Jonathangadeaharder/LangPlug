@echo off
REM Cleanup script for Playwright hanging issues

echo ============================================================
echo       Playwright Test Environment Cleanup
echo ============================================================
echo.

echo [1/4] Killing orphaned Node processes (keeping frontend)...
REM Get frontend server PID
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do set FRONTEND_PID=%%a
echo Frontend server PID: %FRONTEND_PID%

REM Kill all Node processes except frontend
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr "PID:"') do (
  if not "%%a"=="%FRONTEND_PID%" (
    echo Killing Node process %%a
    taskkill /F /PID %%a >nul 2>&1
  )
)

echo.
echo [2/4] Clearing Playwright test artifacts...
if exist "test-results" rmdir /s /q "test-results"
if exist "playwright-report" rmdir /s /q "playwright-report"
if exist ".playwright" rmdir /s /q ".playwright"

echo.
echo [3/4] Waiting for cleanup to complete...
timeout /t 3 /nobreak >nul

echo.
echo [4/4] Verifying frontend is still running...
netstat -ano | findstr ":3000.*LISTENING" >nul
if %ERRORLEVEL%==0 (
  echo [OK] Frontend server still running on port 3000
) else (
  echo [WARN] Frontend server not detected - you may need to restart it
)

echo.
echo ============================================================
echo       Cleanup Complete
echo ============================================================
echo.
echo You can now run: npx playwright test workflows/vocabulary-learning.workflow.test.ts --grep WhenUserAccessesVocabularyLibrary --project=chromium
echo.
