"""Focused tests around the managed server behavior contracts."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from management.config import ServerStatus
from management.server import Server


@pytest.fixture
def backend_server(tmp_path) -> Server:
    return Server(
        name="backend",
        port=8000,
        health_url="http://localhost:8000/health",
        start_cmd=["uvicorn"],
        cwd=tmp_path,
    )


@pytest.mark.timeout(30)
def test_Whenis_port_in_use_reflects_socket_connectionCalled_ThenSucceeds(monkeypatch: pytest.MonkeyPatch, backend_server: Server) -> None:
    """Sockets returning success should be reported as the port being occupied."""

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def settimeout(self, _):
            pass

        def connect_ex(self, addr):
            assert addr == ("localhost", 8000)
            return 0

    monkeypatch.setattr("management.server.socket.socket", lambda *args, **kwargs: FakeSocket())

    assert backend_server.is_port_in_use() is True


@pytest.mark.timeout(30)
def test_Whencheck_health_falls_back_to_process_statusCalled_ThenSucceeds(monkeypatch: pytest.MonkeyPatch, backend_server: Server) -> None:
    """When HTTP is unavailable the server should rely on an active PID."""
    backend_server.pid = 123

    monkeypatch.setattr("management.server.requests", None)
    monkeypatch.setattr("management.server.psutil.pid_exists", lambda pid: pid == 123)

    assert backend_server.check_health() is True


@pytest.mark.timeout(30)
def test_frontend_health_accepts_404(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """The frontend contract allows 404 responses while dev server boots."""
    frontend = Server(
        name="frontend",
        port=3000,
        health_url="http://localhost:3000",
        start_cmd=["npm", "run", "dev"],
        cwd=tmp_path,
    )

    monkeypatch.setattr(
        "management.server.requests",
        SimpleNamespace(get=lambda *_args, **_kwargs: SimpleNamespace(status_code=404)),
    )

    assert frontend.check_health() is True


@pytest.mark.timeout(30)
def test_Whenget_process_infoCalled_ThenReturnsmetrics(monkeypatch: pytest.MonkeyPatch, backend_server: Server) -> None:
    """Process info should be summarised when the PID is active."""
    backend_server.pid = 999

    class FakeProcess:
        def __init__(self, pid):
            self._pid = pid

        def name(self):
            return "proc"

        def status(self):
            return "running"

        def cpu_percent(self, interval=0.1):
            return 1.5

        def memory_info(self):
            return SimpleNamespace(rss=10 * 1024 * 1024)

        def create_time(self):
            return 0

        def num_threads(self):
            return 2

    monkeypatch.setattr("management.server.psutil.pid_exists", lambda pid: True)
    monkeypatch.setattr("management.server.psutil.Process", lambda pid: FakeProcess(pid))

    info = backend_server.get_process_info()

    assert info["pid"] == 999
    assert info["name"] == "proc"
    assert info["memory_mb"] == pytest.approx(10, rel=0.01)
    assert info["num_threads"] == 2
