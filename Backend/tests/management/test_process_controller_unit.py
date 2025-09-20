"""Contract-centric tests for the process controller utilities."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from management.process_controller import ProcessController


class FakeConnection:
    def __init__(self, port: int) -> None:
        self.laddr = SimpleNamespace(port=port)


class FakeProcess:
    def __init__(self, pid: int, name: str, port: int) -> None:
        self.info = {"pid": pid, "name": name}
        self._connection = FakeConnection(port)
        self.terminated = False

    def connections(self, kind: str = "inet"):
        return [self._connection]


@pytest.mark.timeout(30)
def test_Whencleanup_port_terminates_processCalled_ThenSucceeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Processes bound to the target port should be terminated."""
    proc = FakeProcess(pid=123, name="uvicorn", port=8000)
    process_map: dict[int, FakeProcess] = {proc.info["pid"]: proc}

    monkeypatch.setattr(
        "management.process_controller.psutil.process_iter",
        lambda _: [proc],
    )

    def fake_kill(pid: int) -> bool:
        process_map[pid].terminated = True
        return True

    monkeypatch.setattr(ProcessController, "kill_process_tree", fake_kill)

    assert ProcessController.cleanup_port(8000) is True
    assert proc.terminated is True


@pytest.mark.timeout(30)
def test_Whencleanup_portCalled_ThenReturnsfalse_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected errors should surface as a False return value."""
    monkeypatch.setattr(
        "management.process_controller.psutil.process_iter",
        lambda _: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert ProcessController.cleanup_port(5555) is False


@pytest.mark.timeout(30)
def test_Whenstart_processCalled_ThenReturnspopen_handle(monkeypatch: pytest.MonkeyPatch) -> None:
    """start_process should forward command and working directory to Popen."""
    captured: dict[str, object] = {}

    class FakePopen:
        def __init__(self, cmd, cwd=None, stdout=None, stderr=None, env=None, creationflags=0):
            captured.update({"cmd": cmd, "cwd": cwd, "env": env, "creationflags": creationflags})
            self.pid = 42

    monkeypatch.setattr("management.process_controller.subprocess.Popen", FakePopen)

    process = ProcessController.start_process(["echo", "hello"], cwd="/tmp")

    assert process.pid == 42
    assert captured["cmd"] == ["echo", "hello"]
    assert captured["cwd"] == "/tmp"
    # On Windows, creationflags is set to CREATE_NEW_PROCESS_GROUP (512), on Unix it's 0
    import os
    expected_flags = 512 if os.name == 'nt' else 0
    assert captured["creationflags"] == expected_flags
