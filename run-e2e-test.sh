#!/bin/bash
set -e

# Define paths
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/src/backend"
LOG_FILE="$PROJECT_ROOT/backend_test.log"

# Export environment variables
export LANGPLUG_PORT=8000
export LANGPLUG_HOST=0.0.0.0
export LANGPLUG_RELOAD=0
export LANGPLUG_TRANSCRIPTION_SERVICE=whisper-tiny
export LANGPLUG_TRANSLATION_SERVICE=opus-de-es
export LANGPLUG_DEFAULT_LANGUAGE=de
export LANGPLUG_SECRET_KEY=test_secret_key_for_e2e_tests_min_32_chars

echo "Starting backend server..."
cd "$BACKEND_DIR"

# Use PowerShell to run python because we are in WSL/Windows mix environment
if [ -d "api_venv" ]; then
    PYTHON_CMD="api_venv/Scripts/python.exe"
elif [ -d "../../api_venv" ]; then
    PYTHON_CMD="../../api_venv/Scripts/python.exe"
else
    echo "Error: Could not find api_venv"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
powershell.exe -Command "& $PYTHON_CMD run_backend.py" > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID. Logs in $LOG_FILE"

# Wait for health check
echo "Waiting for backend to be healthy..."
MAX_RETRIES=60
COUNT=0
BACKEND_URL="http://127.0.0.1:8000"
WINDOWS_HOST_IP=$(ip route show | grep default | awk '{print $3}')

while [ $COUNT -lt $MAX_RETRIES ]; do
    # Try localhost (Linux)
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "Backend is healthy on localhost!"
        BACKEND_URL="http://127.0.0.1:8000"
        break
    fi

    # Try Windows Host IP
    if curl -s "http://$WINDOWS_HOST_IP:8000/health" > /dev/null; then
        echo "Backend is healthy on $WINDOWS_HOST_IP!"
        BACKEND_URL="http://$WINDOWS_HOST_IP:8000"
        break
    fi
    
    # Check if process is still running (PowerShell wrapper)
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo "Backend wrapper process died!"
        cat "$LOG_FILE"
        exit 1
    fi
    
    echo "Waiting... ($COUNT/$MAX_RETRIES)"
    sleep 5
    COUNT=$((COUNT+1))
done

if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "Timeout waiting for backend!"
    cat "$LOG_FILE"
    kill $BACKEND_PID || true
    exit 1
fi

echo "Backend accessible at: $BACKEND_URL"
export VITE_API_URL="$BACKEND_URL"
export VITE_BACKEND_URL="$BACKEND_URL"
# Also set BASE_URL for Playwright if needed, but Playwright uses frontend URL (3000)
# The frontend will use VITE_API_URL to proxy/call backend.

# Run Playwright tests
echo "Running Playwright tests..."
cd "$PROJECT_ROOT"
# We use 'npx playwright test' which uses the config.
# Config starts Frontend (npm run dev).
# npm run dev should pick up VITE_API_URL.
npx playwright test tests/e2e/auth-pom.spec.ts

TEST_EXIT_CODE=$?

# Cleanup
echo "Stopping backend..."
kill $BACKEND_PID || true
taskkill.exe /F /IM python.exe /FI "WINDOWTITLE eq run_backend.py*" || true

exit $TEST_EXIT_CODE