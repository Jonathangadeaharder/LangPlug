"""Contract focused tests for the health monitor lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from management.config import ServerStatus
from management.health_monitor import HealthMonitor


@dataclass
class StubServer:
    name: str
    status: ServerStatus = ServerStatus.RUNNING
    health_check_failures: int = 0

    def check_health(self) -> bool:
        return True


class StubManager:
    def __init__(self, servers: dict[str, StubServer]) -> None:
        self.servers = servers

    def stop_server(self, name: str) -> bool:  # pragma: no cover - not invoked in these tests
        self.servers[name].status = ServerStatus.STOPPED
        return True

    def start_server(self, name: str) -> bool:  # pragma: no cover - not invoked in these tests
        self.servers[name].status = ServerStatus.RUNNING
        return True


@pytest.mark.timeout(30)
def test_Whenstart_monitoring_launches_daemon_threadCalled_ThenSucceeds() -> None:
    """The monitor should spawn a daemon thread that toggles the monitoring flag."""
    server = StubServer("backend")
    servers = {server.name: server}
    manager = StubManager(servers)
    monitor = HealthMonitor(servers, manager, sleep_interval=0.0)

    def stop_immediately(_: float) -> None:
        monitor.monitoring = False

    monitor.sleep_fn = stop_immediately

    monitor.start_monitoring()
    monitor.monitor_thread.join(timeout=1)

    assert monitor.monitor_thread.daemon is True
    assert monitor.monitoring is False


@pytest.mark.timeout(30)
def test_Whenstop_monitoring_waits_for_thread_completionCalled_ThenSucceeds() -> None:
    """Stopping should cleanly join an active monitoring thread."""
    server = StubServer("backend")
    servers = {server.name: server}
    manager = StubManager(servers)
    monitor = HealthMonitor(servers, manager, sleep_interval=0.0)

    def stop_after_first_sleep(_: float) -> None:
        monitor.monitoring = False

    monitor.sleep_fn = stop_after_first_sleep

    monitor.start_monitoring()
    monitor.stop_monitoring()

    assert monitor.monitor_thread is not None
    assert monitor.monitor_thread.is_alive() is False
