"""
Configuration constants and settings for server management
"""
from pathlib import Path
from enum import Enum

# Configuration
PROJECT_DIR = Path(__file__).parent.parent
PID_FILE = PROJECT_DIR / "server_state.json"
LOG_DIR = PROJECT_DIR / "logs"
BACKEND_DIR = PROJECT_DIR / "Backend"
FRONTEND_DIR = PROJECT_DIR / "Frontend"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)


class ServerStatus(Enum):
    """Server status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    UNHEALTHY = "unhealthy"
