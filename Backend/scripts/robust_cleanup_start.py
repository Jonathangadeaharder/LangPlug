#!/usr/bin/env python3
"""
Robust cleanup and server startup (no external deps)
Uses Windows built-in commands for process cleanup
"""
import json
import subprocess
import time
from pathlib import Path
from urllib import request as urlreq

LOG_PATH = Path(__file__).parent.parent / "logs" / "robust_cleanup_log.txt"

def log_line(msg: str):
    """Write to log file with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    line = f"{timestamp} {msg}"
    print(line)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except Exception as e:
        print(f"Log write failed: {e}")

def run_cmd(cmd: str, description: str):
    """Run command and log results"""
    log_line(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True, timeout=30)
        log_line(f"Exit code: {result.returncode}")
        if result.stdout:
            log_line(f"Output: {result.stdout.strip()}")
        if result.stderr:
            log_line(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log_line(f"Command timed out: {cmd}")
        return False
    except Exception as e:
        log_line(f"Command failed: {e}")
        return False

def kill_processes_on_port(port: int):
    """Kill processes using netstat and taskkill"""
    log_line(f"Killing processes on port {port}...")

    # Find PIDs using the port
    cmd = f'netstat -ano | findstr ":{port}"'
    try:
        result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids.add(pid)

            log_line(f"Found PIDs on port {port}: {list(pids)}")

            # Kill each PID
            for pid in pids:
                kill_cmd = f"taskkill /F /PID {pid}"
                run_cmd(kill_cmd, f"Kill PID {pid}")
        else:
            log_line(f"No processes found on port {port}")
    except Exception as e:
        log_line(f"Error checking port {port}: {e}")

def cleanup_langplug_processes():
    """Kill Python processes that might be LangPlug"""
    log_line("Killing potential LangPlug processes...")

    # Kill any python processes with uvicorn/langplug in command line
    patterns = ["uvicorn", "run_backend", "langplug"]
    for pattern in patterns:
        cmd = f'tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "{pattern}"'
        run_cmd(cmd, f"Search for {pattern} processes")

    # Broad kill of python.exe processes (safer than guessing)
    # This might kill other Python processes, but it's thorough
    cmd = 'taskkill /F /IM "python.exe" /T'
    run_cmd(cmd, "Kill all python.exe processes")

def start_backend_server():
    """Start backend server"""
    log_line("Starting backend server...")

    backend_dir = Path(__file__).parent.parent
    python_exe = backend_dir / "api_venv" / "Scripts" / "python.exe"
    run_script = backend_dir / "run_backend.py"

    if not python_exe.exists():
        log_line(f"ERROR: {python_exe} not found")
        return False

    if not run_script.exists():
        log_line(f"ERROR: {run_script} not found")
        return False

    # Start in background
    cmd = f'start /B "" "{python_exe}" "{run_script}"'
    success = run_cmd(cmd, "Start backend server")

    if success:
        log_line("Backend start command executed")
        time.sleep(3)  # Give server time to start
        return True
    else:
        log_line("Failed to execute backend start command")
        return False

def test_server_health():
    """Test if server responds to health endpoint"""
    log_line("Testing server health...")

    for attempt in range(15):  # 15 attempts, 2s each = 30s total
        try:
            req = urlreq.Request("http://localhost:8000/health")
            with urlreq.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                text = resp.read().decode("utf-8")

                if code == 200:
                    data = json.loads(text)
                    log_line(f"SUCCESS: Server health check passed - {data.get('status')}")
                    return True
                else:
                    log_line(f"Health check returned {code}")
        except Exception as e:
            log_line(f"Health check attempt {attempt + 1}: {e}")

        time.sleep(2)

    log_line("FAILED: Server not responding after 30 seconds")
    return False

def main():
    # Clear log file
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("w", encoding="utf-8") as f:
            f.write("=== Robust LangPlug Cleanup and Startup ===\n")
    except Exception as e:
        print(f"Cannot create log file: {e}")

    log_line("Starting cleanup process...")

    # Step 1: Kill processes on ports
    kill_processes_on_port(8000)
    kill_processes_on_port(3000)

    # Step 2: Kill LangPlug processes
    cleanup_langplug_processes()

    # Step 3: Wait a moment for cleanup
    log_line("Waiting 3 seconds for cleanup to complete...")
    time.sleep(3)

    # Step 4: Start backend
    if not start_backend_server():
        log_line("FAILED: Could not start backend server")
        return 1

    # Step 5: Test health
    if test_server_health():
        log_line("SUCCESS: Backend is running and healthy at http://localhost:8000")
        return 0
    else:
        log_line("FAILED: Backend not responding to health checks")
        return 1

if __name__ == "__main__":
    exit(main())
