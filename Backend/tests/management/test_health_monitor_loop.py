"""Behavioral verification for the health monitor sweep logic."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from management.config import ServerStatus
from management.health_monitor import HealthMonitor


@dataclass
class StubServer:
    """Minimal server double that tracks health status for the monitor."""

    name: str
    check_result: bool
    status: ServerStatus = ServerStatus.RUNNING
    health_check_failures: int = 0

    def check_health(self) -> bool:
        return self.check_result


class StubManager:
    """Manager double that mirrors the production contract effects."""

    def __init__(self, servers: dict[str, StubServer], *, start_success: bool = True) -> None:
        self._servers = servers
        self._start_success = start_success

    def stop_server(self, name: str) -> bool:
        self._servers[name].status = ServerStatus.STOPPED
        return True

    def start_server(self, name: str) -> bool:
        if self._start_success:
            self._servers[name].status = ServerStatus.RUNNING
        return self._start_success


@pytest.fixture(name="server")
def stub_server() -> StubServer:
    return StubServer(name="backend", check_result=False, health_check_failures=2)


@pytest.mark.timeout(30)
def test_Whenevaluate_servers_once_recovers_after_thresholdCalled_ThenSucceeds(server: StubServer) -> None:
    """Once the failure threshold is crossed the monitor should attempt recovery."""
    servers = {server.name: server}
    manager = StubManager(servers)
    monitor = HealthMonitor(servers, manager, sleep_fn=lambda _: None)

    monitor.evaluate_servers_once()

    assert server.status is ServerStatus.RUNNING
    assert server.health_check_failures == 0


@pytest.mark.timeout(30)
def test_Whenevaluate_servers_once_marks_failure_if_recovery_failsCalled_ThenSucceeds(server: StubServer) -> None:
    """If recovery cannot restart the service the server remains unhealthy."""
    servers = {server.name: server}
    manager = StubManager(servers, start_success=False)
    monitor = HealthMonitor(servers, manager, sleep_fn=lambda _: None)

    monitor.evaluate_servers_once()

    assert server.status in {ServerStatus.UNHEALTHY, ServerStatus.STOPPED}
    assert server.health_check_failures == 3


@pytest.mark.timeout(30)
def test_Whensuccessful_health_check_resets_failure_counterCalled_ThenSucceeds() -> None:
    """A healthy response should clear accumulated failures."""
    server = StubServer(name="backend", check_result=True, health_check_failures=2)
    servers = {server.name: server}
    manager = StubManager(servers)
    monitor = HealthMonitor(servers, manager, sleep_fn=lambda _: None)

    monitor.evaluate_servers_once()

    assert server.status is ServerStatus.RUNNING
    assert server.health_check_failures == 0
