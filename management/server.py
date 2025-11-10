"""
Server class and related utilities for process management
"""
import socket
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    import requests
except ImportError:
    requests = None

from .config import ServerStatus


class Server:
    """Represents a managed server instance"""

    def __init__(self, name: str, port: int, health_url: str, start_cmd: List[str],
                 cwd: Path, startup_time: int = 10, max_retries: int = 3):
        self.name = name
        self.port = port
        self.health_url = health_url
        self.start_cmd = start_cmd
        self.cwd = cwd
        self.startup_time = startup_time
        self.max_retries = max_retries
        self.pid: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.status = ServerStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.health_check_failures = 0

    def is_port_in_use(self) -> bool:
        """Check if the server's port is already in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', self.port))
                return result == 0
        except (OSError, socket.error):
            # Socket operations failed - assume port not in use
            return False

    def check_health(self) -> bool:
        """Check if server is healthy via HTTP endpoint"""
        if not self.health_url:
            return self.pid is not None and psutil.pid_exists(self.pid)

        if requests is None:
            # Fallback to process check if requests not available
            return self.pid is not None and psutil.pid_exists(self.pid)

        try:
            # For frontend, accept any response (Vite may return 404 for root)
            if self.name == "frontend":
                response = requests.get(self.health_url, timeout=5)
                # Vite dev server may return 404 for root but still be running
                return response.status_code in [200, 404]
            else:
                response = requests.get(self.health_url, timeout=5)
                return response.status_code == 200
        except (requests.RequestException, ConnectionError, TimeoutError):
            # Network/HTTP errors - server not healthy
            return False

    def is_process_alive(self) -> bool:
        """Check if the process is still running"""
        if not self.pid:
            return False
        try:
            return psutil.pid_exists(self.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process doesn't exist or we can't access it
            return False

    def get_process_info(self) -> Dict:
        """Get detailed process information"""
        if not self.pid or not psutil.pid_exists(self.pid):
            return {}

        try:
            proc = psutil.Process(self.pid)
            return {
                "pid": self.pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                "num_threads": proc.num_threads()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process not accessible or in invalid state
            return {}
