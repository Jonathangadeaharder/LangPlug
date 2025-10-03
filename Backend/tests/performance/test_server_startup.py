"""Application factory lifespan smoke tests."""

from __future__ import annotations

import builtins
import contextlib
from unittest.mock import AsyncMock, Mock

import pytest

from core.app import create_app


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_Whenlifespan_skips_service_init_in_test_modeCalled_ThenSucceeds(monkeypatch) -> None:
    """When TESTING is set, service initialization should be bypassed."""
    init_mock = AsyncMock()
    monkeypatch.setattr("core.app.init_services", init_mock)

    app = create_app()
    async with app.router.lifespan_context(app):
        pass

    init_mock.assert_not_called()


@pytest.mark.anyio("asyncio")
@pytest.mark.timeout(30)
async def test_Whenlifespan_schedules_cleanupCalled_ThenSucceeds(monkeypatch) -> None:
    """Cleanup should be scheduled even if no loop is running during shutdown."""
    created_tasks = []

    async def fake_cleanup() -> None:
        created_tasks.append("cleanup")

    def mock_create_task(coro):
        if hasattr(coro, "__await__"):  # It's a coroutine
            # Close the coroutine to prevent warning
            with contextlib.suppress(builtins.BaseException):
                coro.close()
        created_tasks.append(coro)
        # Return a mock Task object with add_done_callback method
        mock_task = Mock()
        mock_task.add_done_callback = Mock()
        return mock_task

    monkeypatch.setattr("core.app.cleanup_services", fake_cleanup)
    # Patch the global asyncio.create_task since core.app imports asyncio locally
    monkeypatch.setattr("asyncio.create_task", mock_create_task, raising=False)

    app = create_app()
    async with app.router.lifespan_context(app):
        pass

    assert created_tasks, "Cleanup coroutine should be scheduled"
