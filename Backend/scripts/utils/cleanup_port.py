#!/usr/bin/env python3
"""
Port cleanup utility for Backend startup
Kills any process using the specified port before starting
"""

import subprocess
import sys


def kill_process_on_port(port):
    """Kill any process using the specified port"""

    try:
        # Windows command to find and kill process on port (without shell=True)
        port_str = str(int(port))  # Validate port is an integer
        command = [
            "powershell.exe",
            "-Command",
            f"Get-NetTCPConnection -LocalPort {port_str} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}",
        ]
        subprocess.run(
            command,
            check=False,
            shell=False,  # Security: avoid shell=True
            capture_output=True,
            text=True,
        )

    except (ValueError, Exception):
        # Silently handle errors (port validation or subprocess errors)
        pass


def kill_all_python_processes():
    """Kill all Python processes (more aggressive)"""

    try:
        command = ["taskkill", "/F", "/IM", "python.exe"]
        subprocess.run(
            command,
            check=False,
            shell=False,  # Security: avoid shell=True
            capture_output=True,
            text=True,
        )

    except Exception:
        pass


if __name__ == "__main__":
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    # First try to kill process on specific port
    kill_process_on_port(port)

    # Also clear common Backend ports
    for p in [8000, 8001, 8002, 8003]:
        if p != port:
            kill_process_on_port(p)
