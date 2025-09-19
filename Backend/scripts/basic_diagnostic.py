#!/usr/bin/env python3
"""Basic diagnostic to identify startup issues"""
import os
import subprocess
import sys
from pathlib import Path

# Force create log in current directory first
log_path = Path(__file__).parent / "diagnostic_output.txt"

def write_log(msg):
    print(msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear log
with open(log_path, "w", encoding="utf-8") as f:
    f.write("=== Basic Diagnostic ===\n")

write_log(f"Python executable: {sys.executable}")
write_log(f"Current working directory: {os.getcwd()}")
write_log(f"Script location: {__file__}")

# Check venv python
backend_dir = Path(__file__).parent.parent
venv_python = backend_dir / "api_venv" / "Scripts" / "python.exe"
write_log(f"Expected venv python: {venv_python}")
write_log(f"Venv python exists: {venv_python.exists()}")

if venv_python.exists():
    try:
        result = subprocess.run([str(venv_python), "--version"], check=False, capture_output=True, text=True, timeout=10)
        write_log(f"Venv python version: {result.stdout.strip()}")
    except Exception as e:
        write_log(f"Venv python test failed: {e}")

# Check run_backend.py
run_backend = backend_dir / "run_backend.py"
write_log(f"run_backend.py path: {run_backend}")
write_log(f"run_backend.py exists: {run_backend.exists()}")

# Check logs directory
logs_dir = backend_dir / "logs"
write_log(f"Logs directory: {logs_dir}")
write_log(f"Logs directory exists: {logs_dir.exists()}")

if logs_dir.exists():
    try:
        # Test write permissions
        test_file = logs_dir / "write_test.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        test_file.unlink()
        write_log("Logs directory is writable")
    except Exception as e:
        write_log(f"Logs directory write test failed: {e}")

# Check if any python processes are running
try:
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], check=False, capture_output=True, text=True)
    if "python.exe" in result.stdout:
        write_log("Python processes found:")
        write_log(result.stdout)
    else:
        write_log("No python.exe processes found")
except Exception as e:
    write_log(f"Process check failed: {e}")

# Check port 8000
try:
    result = subprocess.run(["netstat", "-ano"], check=False, capture_output=True, text=True)
    port_8000_lines = [line for line in result.stdout.split('\n') if ':8000' in line]
    if port_8000_lines:
        write_log("Port 8000 usage:")
        for line in port_8000_lines:
            write_log(line.strip())
    else:
        write_log("Port 8000 is free")
except Exception as e:
    write_log(f"Port check failed: {e}")

write_log("=== Diagnostic complete ===")
