"""Behavior-first tests for the professional server manager."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Iterator

import pytest

from management.config import ServerStatus
from management.server_manager import ProfessionalServerManager


@dataclass
class StubManagedServer:
    """Lightweight stand-in for the managed Server class."""

    name: str
    port: int
    status: ServerStatus = ServerStatus.STOPPED
    pid: int | None = None
    start_cmd: list[str] = field(default_factory=lambda: ["python", "main.py"])
    cwd: Path = field(default_factory=lambda: Path("/tmp"))
    process = None
    start_time = None
    is_port_in_use_result: bool = False
    is_process_alive_result: bool = True
    _health_sequence: Iterator[bool] = field(default_factory=lambda: iter((True,)))

    def set_health_responses(self, responses: Iterable[bool]) -> None:
        self._health_sequence = iter(responses)

    def check_health(self) -> bool:
        try:
            return next(self._health_sequence)
        except StopIteration:
            return True

    def is_port_in_use(self) -> bool:
        return self.is_port_in_use_result

    def is_process_alive(self) -> bool:
        return self.is_process_alive_result


@pytest.fixture
def manager_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> tuple[
    ProfessionalServerManager,
    StubManagedServer,
    StubManagedServer,
    list[int],
    list[int],
    dict[str, object],
]:
    """Create a manager with stubbed process control and monitor dependencies."""
    backend = StubManagedServer("backend", 8000)
    frontend = StubManagedServer("frontend", 3000)
    servers = {"backend": backend, "frontend": frontend}

    cleaned_ports: list[int] = []
    killed_pids: list[int] = []
    monitor_state: dict[str, object] = {}

    class ProcessControllerStub:
        @staticmethod
        def start_process(cmd, cwd):
            return SimpleNamespace(pid=555)

        @staticmethod
        def cleanup_port(port):
            cleaned_ports.append(port)
            return True

        @staticmethod
        def kill_process_tree(pid):
            killed_pids.append(pid)
            return True

        @staticmethod
        def comprehensive_cleanup(ports=None):
            if ports is None:
                cleaned_ports.append(None)
            else:
                cleaned_ports.extend(list(ports))
            return True

        @staticmethod
        def is_process_running(pid):
            return False

    class MonitorStub:
        def __init__(self, servers_ref, manager_ref, **kwargs):
            monitor_state["instance"] = self
            self.servers = servers_ref
            self.manager = manager_ref
            self.started = False
            self.stopped = False

        def start_monitoring(self):
            self.started = True

        def stop_monitoring(self):
            self.stopped = True

    monkeypatch.setattr(
        ProfessionalServerManager,
        "_setup_servers",
        lambda self: setattr(self, "servers", servers),
    )
    monkeypatch.setattr(ProfessionalServerManager, "_load_state", lambda self: None)
    monkeypatch.setattr("management.server_manager.PID_FILE", tmp_path / "state.json")
    monkeypatch.setattr("management.server_manager.ProcessController", ProcessControllerStub)
    monkeypatch.setattr("management.server_manager.HealthMonitor", MonitorStub)
    monkeypatch.setattr("management.server_manager.time.sleep", lambda _: None)

    manager = ProfessionalServerManager()
    manager.servers = servers
    manager.health_monitor = None

    return manager, backend, frontend, cleaned_ports, killed_pids, monitor_state


@pytest.mark.timeout(30)
def test_Whenstart_server_marks_backend_runningCalled_ThenSucceeds(manager_env) -> None:
    manager, backend, _, _, _, _ = manager_env
    backend.set_health_responses((True,))

    result = manager.start_server("backend")

    assert result is True
    assert backend.status is ServerStatus.RUNNING
    assert backend.pid == 555


@pytest.mark.timeout(30)
def test_Whenstart_server_cleans_port_when_in_useCalled_ThenSucceeds(manager_env) -> None:
    manager, backend, _, cleaned_ports, _, _ = manager_env
    backend.is_port_in_use_result = True
    backend.set_health_responses((True,))

    manager.start_server("backend")

    assert backend.port in cleaned_ports


@pytest.mark.timeout(30)
def test_Whenstart_server_flags_error_when_process_diesCalled_ThenSucceeds(manager_env) -> None:
    manager, backend, _, _, _, _ = manager_env
    backend.is_process_alive_result = False
    backend.set_health_responses((False,))

    result = manager.start_server("backend")

    assert result is False
    assert backend.status is ServerStatus.ERROR


@pytest.mark.timeout(30)
def test_Whenstart_unknown_serverCalled_ThenReturnsfalse(manager_env) -> None:
    manager, _, _, _, _, _ = manager_env
    assert manager.start_server("unknown") is False


@pytest.mark.timeout(30)
def test_Whenstop_server_resets_pid_and_statusCalled_ThenSucceeds(manager_env) -> None:
    manager, backend, _, _, killed_pids, _ = manager_env
    backend.pid = 777
    backend.status = ServerStatus.RUNNING

    assert manager.stop_server("backend") is True
    assert backend.status is ServerStatus.STOPPED
    assert backend.pid is None
    assert killed_pids == [777]


@pytest.mark.timeout(30)
def test_Whenstop_unknown_serverCalled_ThenReturnsfalse(manager_env) -> None:
    manager, _, _, _, _, _ = manager_env
    assert manager.stop_server("does-not-exist") is False


@pytest.mark.timeout(30)
def test_Whenstart_allCalled_ThenReturnsfalse_if_any_server_fails(manager_env) -> None:
    manager, backend, frontend, _, _, _ = manager_env
    backend.is_process_alive_result = False
    backend.set_health_responses((False,))
    frontend.set_health_responses((True,))

    assert manager.start_all() is False
    assert backend.status is ServerStatus.ERROR
    assert frontend.status is ServerStatus.RUNNING


@pytest.mark.timeout(30)
def test_Whenstop_all_runs_cleanupCalled_ThenSucceeds(manager_env) -> None:
    manager, backend, frontend, cleaned_ports, killed_pids, _ = manager_env
    backend.pid = 100
    backend.status = ServerStatus.RUNNING
    frontend.pid = 200
    frontend.status = ServerStatus.RUNNING

    assert manager.stop_all() is True
    assert backend.status is ServerStatus.STOPPED
    assert frontend.status is ServerStatus.STOPPED
    assert killed_pids == [100, 200]
    assert None in cleaned_ports


@pytest.mark.timeout(30)
def test_Whenrestart_all_restarts_servicesCalled_ThenSucceeds(manager_env, monkeypatch: pytest.MonkeyPatch) -> None:
    manager, _, _, _, _, _ = manager_env

    calls: list[str] = []
    monkeypatch.setattr(manager, "stop_all", lambda: calls.append("stop") or True)
    monkeypatch.setattr(manager, "start_all", lambda: calls.append("start") or True)

    assert manager.restart_all() is True
    assert calls == ["stop", "start"]


@pytest.mark.timeout(30)
def test_Whenmonitoring_lifecycle_uses_health_monitorCalled_ThenSucceeds(manager_env) -> None:
    manager, _, _, _, _, monitor_state = manager_env

    manager.start_monitoring()
    monitor = monitor_state["instance"]
    assert monitor.started is True

    manager.stop_monitoring()
    assert monitor.stopped is True
