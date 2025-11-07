"""
Main server manager class using modular components
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from .config import PID_FILE, BACKEND_DIR, FRONTEND_DIR, ServerStatus, LOG_DIR
from .server import Server
from .process_controller import ProcessController
from .health_monitor import HealthMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / f"server_manager_{datetime.now().strftime('%Y%m%d')}.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ServerManager")


class ProfessionalServerManager:
    """Professional server manager with modular architecture"""

    def __init__(self):
        self.servers: Dict[str, Server] = {}
        self.state: Dict = {"servers": {}, "last_action": None}
        self.health_monitor: Optional[HealthMonitor] = None
        self._setup_servers()
        self._load_state()

    def _setup_servers(self):
        """Initialize server configurations"""
        # Backend server configuration
        backend_venv = BACKEND_DIR / "api_venv" / "Scripts" / "python.exe"
        self.servers["backend"] = Server(
            name="backend",
            port=8000,
            health_url="http://localhost:8000/health",
            start_cmd=[str(backend_venv), "main.py"],
            cwd=BACKEND_DIR,
            startup_time=15,
        )

        # Frontend server configuration
        # Use cmd.exe on Windows to ensure npm is found
        import platform

        if platform.system() == "Windows":
            frontend_cmd = ["cmd.exe", "/c", "npm", "run", "dev"]
        else:
            frontend_cmd = ["npm", "run", "dev"]

        self.servers["frontend"] = Server(
            name="frontend",
            port=3000,
            health_url="http://localhost:3000",
            start_cmd=frontend_cmd,
            cwd=FRONTEND_DIR,
            startup_time=30,
        )

    def _load_state(self):
        """Load saved state and recover PIDs"""
        if PID_FILE.exists():
            try:
                with open(PID_FILE, "r") as f:
                    self.state = json.load(f)

                # Recover PIDs and check if processes still exist
                for name, info in self.state.get("servers", {}).items():
                    if name in self.servers and "pid" in info:
                        pid = info["pid"]
                        if ProcessController.is_process_running(pid):
                            self.servers[name].pid = pid
                            self.servers[name].status = ServerStatus.RUNNING
                            logger.info(f"Recovered {name} server with PID {pid}")
                        else:
                            logger.info(
                                f"Previous {name} server (PID {pid}) is not running"
                            )
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

    def _save_state(self):
        """Save current state to disk"""
        try:
            self.state["servers"] = {}
            self.state["last_action"] = datetime.now().isoformat()

            for name, server in self.servers.items():
                self.state["servers"][name] = {
                    "pid": server.pid,
                    "status": server.status.value,
                    "port": server.port,
                    "start_time": server.start_time.isoformat()
                    if server.start_time
                    else None,
                }

            with open(PID_FILE, "w") as f:
                json.dump(self.state, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def start_server(self, name: str) -> bool:
        """Start a specific server"""
        if name not in self.servers:
            logger.error(f"Unknown server: {name}")
            return False

        server = self.servers[name]

        if server.status == ServerStatus.RUNNING:
            logger.info(f"{name} server is already running")
            return True

        logger.info(f"Starting {name} server...")
        server.status = ServerStatus.STARTING

        try:
            # Clean up port if needed
            if server.is_port_in_use():
                logger.info(
                    f"Port {server.port} is in use, performing comprehensive cleanup..."
                )
                ProcessController.comprehensive_cleanup([server.port])
                time.sleep(3)

            # Start the process
            server.process = ProcessController.start_process(
                server.start_cmd, str(server.cwd)
            )
            server.pid = server.process.pid
            server.start_time = datetime.now()

            # Dynamic health check with polling
            max_wait_time = (
                60 if name == "backend" else 30
            )  # Backend needs more time for Whisper model
            poll_interval = 2
            elapsed = 0

            logger.info(f"Waiting for {name} to start (max {max_wait_time}s)...")

            while elapsed < max_wait_time:
                # First check if process is still alive
                if not server.is_process_alive():
                    logger.error(f"{name} process died unexpectedly")
                    server.status = ServerStatus.ERROR
                    return False

                # Check health
                if server.check_health():
                    server.status = ServerStatus.RUNNING
                    logger.info(
                        f"[SUCCESS] {name} server started successfully on port {server.port} after {elapsed}s"
                    )
                    self._save_state()
                    return True

                # Show progress with different messages based on timing
                if elapsed == 0:
                    logger.info(
                        f"  Process started with PID {server.pid}, waiting for initialization..."
                    )
                elif elapsed == 10:
                    logger.info(f"  {name} server is initializing... (this is normal)")
                elif elapsed == 20 and name == "backend":
                    logger.info(
                        "  Backend is loading AI models... (this may take a moment)"
                    )
                elif elapsed == 30 and name == "backend":
                    logger.info(
                        "  Still loading Whisper model... (large model takes time)"
                    )
                elif elapsed > 0 and elapsed % 10 == 0:
                    logger.info(
                        f"  Still waiting for {name} server... ({elapsed}s elapsed)"
                    )

                time.sleep(poll_interval)
                elapsed += poll_interval

            # Timeout reached
            logger.error(f"{name} server failed to start within {max_wait_time}s")
            server.status = ServerStatus.ERROR
            return False

        except Exception as e:
            logger.error(f"Failed to start {name} server: {e}")
            server.status = ServerStatus.ERROR
            return False

    def stop_server(self, name: str) -> bool:
        """Stop a specific server"""
        if name not in self.servers:
            logger.error(f"Unknown server: {name}")
            return False

        server = self.servers[name]

        if server.status == ServerStatus.STOPPED:
            logger.info(f"{name} server is already stopped")
            return True

        logger.info(f"Stopping {name} server...")
        server.status = ServerStatus.STOPPING

        try:
            if server.pid:
                success = ProcessController.kill_process_tree(server.pid)
                if success:
                    server.pid = None
                    server.process = None
                    server.status = ServerStatus.STOPPED
                    logger.info(f"{name} server stopped successfully")
                    self._save_state()
                    return True
                else:
                    logger.error(f"Failed to stop {name} server")
                    return False
            else:
                server.status = ServerStatus.STOPPED
                return True

        except Exception as e:
            logger.error(f"Error stopping {name} server: {e}")
            return False

    def start_all(self) -> bool:
        """Start all servers"""
        logger.info("Starting all servers")
        success = True

        # Start backend first
        if not self.start_server("backend"):
            success = False

        # Then start frontend
        if not self.start_server("frontend"):
            success = False

        return success

    def stop_all(self) -> bool:
        """Stop all servers with comprehensive cleanup"""
        logger.info("Stopping all servers")
        success = True

        # First try to stop servers gracefully
        for name in self.servers.keys():
            if not self.stop_server(name):
                success = False

        # Then perform comprehensive cleanup to ensure everything is stopped
        logger.info("Performing comprehensive cleanup...")
        if not ProcessController.comprehensive_cleanup():
            success = False

        return success

    def restart_all(self) -> bool:
        """Restart all servers"""
        logger.info("Restarting all servers")
        self.stop_all()
        time.sleep(2)
        return self.start_all()

    def print_status(self):
        """Print current status of all servers"""
        print("\n" + "=" * 60)
        print(" LangPlug Server Status")
        print("=" * 60)

        for name, server in self.servers.items():
            status_symbol = {
                ServerStatus.RUNNING: "[RUNNING]",
                ServerStatus.STOPPED: "[STOPPED]",
                ServerStatus.STARTING: "[STARTING]",
                ServerStatus.STOPPING: "[STOPPING]",
                ServerStatus.ERROR: "[ERROR]",
                ServerStatus.UNHEALTHY: "[UNHEALTHY]",
            }.get(server.status, "[UNKNOWN]")

            print(f"\n{status_symbol} {name.upper()} SERVER")
            print(f"   Status: {server.status.value}")
            print(f"   Port: {server.port}")

            if server.pid:
                print(f"   PID: {server.pid}")
                process_info = server.get_process_info()
                if process_info:
                    print(f"   CPU: {process_info.get('cpu_percent', 0):.1f}%")
                    print(f"   Memory: {process_info.get('memory_mb', 0):.1f} MB")

            if server.start_time:
                uptime = datetime.now() - server.start_time
                print(f"   Uptime: {uptime}")

            # Health check
            if server.status == ServerStatus.RUNNING:
                health = "✅ Healthy" if server.check_health() else "❌ Unhealthy"
                print(f"   Health: {health}")

        print("\n" + "=" * 60)

    def start_monitoring(self):
        """Start health monitoring"""
        if not self.health_monitor:
            self.health_monitor = HealthMonitor(self.servers, self)
        self.health_monitor.start_monitoring()

    def stop_monitoring(self):
        """Stop health monitoring"""
        if self.health_monitor:
            self.health_monitor.stop_monitoring()


# Add missing method to ProcessController
def is_process_running(pid: int) -> bool:
    """Check if process is running"""
    try:
        import psutil

        return psutil.pid_exists(pid)
    except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied) as e:
        # psutil not available or process not accessible
        return False


# Monkey patch for now
ProcessController.is_process_running = staticmethod(is_process_running)
