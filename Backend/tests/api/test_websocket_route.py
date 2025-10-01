"""
Direct unit tests for websocket route function using a fake WebSocket.
Exercises missing-token, invalid-token, and happy-path branches without a real server.
"""

from __future__ import annotations

import pytest


class FakeWS:
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.sent = []
        self._recv = []

    async def accept(self):
        self.accepted = True

    async def close(self, code: int, reason: str = ""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def receive_json(self):
        if not self._recv:
            # Simulate client disconnect after first loop
            from fastapi import WebSocketDisconnect

            raise WebSocketDisconnect
        return self._recv.pop(0)

    async def send_json(self, data):
        self.sent.append(data)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenws_missing_token_closesCalled_ThenSucceeds(monkeypatch):
    from api.routes.websocket import websocket_endpoint

    ws = FakeWS()
    await websocket_endpoint(ws, token=None)
    assert ws.closed is True
    assert ws.close_code == 1008
    assert "Missing" in (ws.close_reason or "")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_ws_InvalidToken_closes(monkeypatch):
    from api.routes import websocket as wsmod

    class MockJWTAuthBad:
        async def authenticate(self, token: str, db):
            # Simulate authentication failure by returning None
            return None

    monkeypatch.setattr("core.auth.jwt_authentication", MockJWTAuthBad())

    ws = FakeWS()
    await wsmod.websocket_endpoint(ws, token="nope")
    assert ws.closed is True
    # Invalid authentication uses code 1008
    assert ws.close_code == 1008


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenws_success_connect_and_disconnectCalled_ThenSucceeds(monkeypatch):
    from api.routes import websocket as wsmod
    from database.models import User

    # Create a fake user for authentication
    fake_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="fake_hash",
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )
    fake_user.id = 42  # Set ID directly

    class MockJWTAuth:
        async def authenticate(self, token: str, db):
            if token == "ok":
                return fake_user
            return None

    events = {"connected": False, "disconnected": False}

    async def fake_connect(ws, user_id):
        events["connected"] = True

    async def fake_handle_message(ws, data):
        # Immediately simulate disconnect by raising the same exception
        from fastapi import WebSocketDisconnect

        raise WebSocketDisconnect

    def fake_disconnect(ws):
        events["disconnected"] = True

    # Mock JWT authentication instead of auth service
    monkeypatch.setattr("core.auth.jwt_authentication", MockJWTAuth())
    monkeypatch.setattr(wsmod.manager, "connect", fake_connect)
    monkeypatch.setattr(wsmod.manager, "handle_message", fake_handle_message)
    monkeypatch.setattr(wsmod.manager, "disconnect", fake_disconnect)

    ws = FakeWS()
    await wsmod.websocket_endpoint(ws, token="ok")
    # Our fake connect does not call accept; just ensure lifecycle hooks ran
    assert events["connected"] is True
    assert events["disconnected"] is True


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenws_status_routeCalled_ThenSucceeds(monkeypatch):
    from api.routes import websocket as wsmod

    class WS(FakeWS):
        async def receive_text(self):
            from fastapi import WebSocketDisconnect

            # trigger a single receive then disconnect
            raise WebSocketDisconnect

    ws = WS()
    await wsmod.websocket_status(ws)
    # Accepted was called
    assert ws.accepted is True
    # First send should be a status message
    assert ws.sent and ws.sent[0].get("type") == "status"
