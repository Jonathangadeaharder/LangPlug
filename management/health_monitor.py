"""
Health monitoring and auto-recovery for servers
"""
import logging
import threading
import time
from typing import Callable, Dict

from .config import ServerStatus

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors server health and handles auto-recovery"""

    def __init__(
        self,
        servers: Dict,
        manager_instance,
        *,
        sleep_interval: float = 30.0,
        sleep_fn: Callable[[float], None] | None = None,
    ):
        self.servers = servers
        self.manager = manager_instance
        self.monitor_thread: threading.Thread = None
        self.monitoring = False
        self.sleep_interval = sleep_interval
        self.sleep_fn = sleep_fn or time.sleep

    def start_monitoring(self):
        """Start the health monitoring thread"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Health monitoring started")

    def stop_monitoring(self):
        """Stop the health monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.evaluate_servers_once()
                self.sleep_fn(self.sleep_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.sleep_fn(self.sleep_interval)

    def evaluate_servers_once(self) -> None:
        """Run a single health check sweep across all managed servers."""
        for name, server in self.servers.items():
            if server.status == ServerStatus.RUNNING and not server.check_health():
                server.health_check_failures += 1
                logger.warning(
                    "%s server health check failed (%s)",
                    name,
                    server.health_check_failures,
                )

                if server.health_check_failures >= 3:
                    logger.error("%s server is unhealthy, attempting restart", name)
                    server.status = ServerStatus.UNHEALTHY

                    success = self._recover_server(server)
                    if success:
                        server.health_check_failures = 0
                        logger.info("Successfully recovered %s server", name)
                    else:
                        logger.error("Failed to recover %s server", name)
            else:
                if server.health_check_failures > 0:
                    logger.info("%s server health recovered", name)
                    server.health_check_failures = 0

    def _recover_server(self, server) -> bool:
        """Attempt to recover a failed server"""
        try:
            # Stop the failed server
            logger.info(f"Stopping failed {server.name} server")
            self.manager.stop_server(server.name)

            # Wait a moment
            time.sleep(5)

            # Restart the server
            logger.info(f"Restarting {server.name} server")
            success = self.manager.start_server(server.name)

            return success

        except Exception as e:
            logger.error(f"Error recovering server {server.name}: {e}")
            return False
