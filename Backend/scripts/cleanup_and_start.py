#!/usr/bin/env python3
"""
Comprehensive cleanup and server startup script
- Kills processes on ports 8000 and 3000
- Stops any existing LangPlug processes
- Starts backend server
- Writes detailed logs to cleanup_and_start_log.txt
"""

import builtins
import contextlib
import subprocess
import sys
import time
from pathlib import Path

import psutil

LOG_PATH = Path(__file__).parent.parent / "logs" / "cleanup_and_start_log.txt"


def log_line(msg: str):
    """Write to both console and log file"""
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
        f.flush()


def kill_port_processes(port: int):
    """Kill all processes using the specified port"""
    log_line(f"Checking for processes on port {port}...")
    killed_count = 0

    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            connections = proc.info["connections"]
            if connections:
                for conn in connections:
                    if hasattr(conn, "laddr") and conn.laddr and conn.laddr.port == port:
                        log_line(f"Killing {proc.info['name']} (PID {proc.info['pid']}) on port {port}")
                        proc.kill()
                        killed_count += 1
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    log_line(f"Killed {killed_count} processes on port {port}")
    return killed_count


def kill_langplug_processes():
    """Kill processes with 'python' that are running LangPlug scripts"""
    log_line("Checking for LangPlug Python processes...")
    killed_count = 0

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if proc.info["name"] in ["python.exe", "python3.exe", "python"]:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if any(keyword in cmdline.lower() for keyword in ["langplug", "run_backend", "uvicorn"]):
                    log_line(f"Killing LangPlug process {proc.info['name']} (PID {proc.info['pid']})")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    log_line(f"Killed {killed_count} LangPlug processes")
    return killed_count


def wait_for_port_free(port: int, timeout: int = 10):
    """Wait for port to be free"""
    log_line(f"Waiting for port {port} to be free...")
    for _i in range(timeout):
        port_free = True
        for proc in psutil.process_iter(["connections"]):
            try:
                connections = proc.info["connections"]
                if connections:
                    for conn in connections:
                        if hasattr(conn, "laddr") and conn.laddr and conn.laddr.port == port:
                            port_free = False
                            break
                if not port_free:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if port_free:
            log_line(f"Port {port} is now free")
            return True

        time.sleep(1)

    log_line(f"Port {port} still in use after {timeout}s timeout")
    return False


def start_backend():
    """Start the backend server"""
    log_line("Starting backend server...")
    backend_dir = Path(__file__).parent.parent
    python_exe = backend_dir / "api_venv" / "Scripts" / "python.exe"
    run_script = backend_dir / "run_backend.py"

    if not python_exe.exists():
        log_line(f"ERROR: Python executable not found at {python_exe}")
        return None

    if not run_script.exists():
        log_line(f"ERROR: Backend script not found at {run_script}")
        return None

    try:
        # Start backend process
        proc = subprocess.Popen(
            [str(python_exe), str(run_script)],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        log_line(f"Backend started with PID {proc.pid}")
        return proc
    except Exception as e:
        log_line(f"ERROR starting backend: {e}")
        return None


def verify_server_health():
    """Verify server is responding to health checks"""
    log_line("Waiting for server to start...")
    time.sleep(3)

    import json
    from urllib import request as urlreq

    for attempt in range(10):
        try:
            req = urlreq.Request("http://localhost:8000/health")
            with urlreq.urlopen(req, timeout=3) as resp:
                code = resp.getcode()
                text = resp.read().decode("utf-8")
                if code == 200:
                    data = json.loads(text)
                    log_line(f"Server health check PASSED: {data.get('status')}")
                    return True
                else:
                    log_line(f"Server health check returned {code}")
        except Exception as e:
            log_line(f"Health check attempt {attempt + 1}: {e}")

        time.sleep(2)

    log_line("Server health check FAILED after 10 attempts")
    return False


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Clear previous log
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write("=== LangPlug Cleanup and Startup Log ===\n")

    log_line("Starting comprehensive cleanup...")

    # Kill processes on ports
    kill_port_processes(8000)
    kill_port_processes(3000)

    # Kill LangPlug processes
    kill_langplug_processes()

    # Wait for ports to be free
    port_8000_free = wait_for_port_free(8000)
    wait_for_port_free(3000)

    if not port_8000_free:
        log_line("WARNING: Port 8000 still not free, continuing anyway...")

    # Start backend
    backend_proc = start_backend()
    if not backend_proc:
        log_line("FAILED to start backend")
        return 1

    # Verify server health
    if verify_server_health():
        log_line("SUCCESS: Backend server is running and healthy")
        log_line(f"Backend PID: {backend_proc.pid}")
        log_line("Server available at http://localhost:8000")
        return 0
    else:
        log_line("FAILED: Backend server not responding to health checks")
        with contextlib.suppress(builtins.BaseException):
            backend_proc.kill()
        return 1


if __name__ == "__main__":
    sys.exit(main())
