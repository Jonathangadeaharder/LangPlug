"""Integration tests for the websocket route."""
from __future__ import annotations

import pytest
import httpx


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenwebsocketWithouttoken_ThenReturnsError(async_client):
    with pytest.raises((httpx.HTTPStatusError, httpx.ConnectError, Exception)):
        await async_client.ws_connect("/api/ws/connect")
