"""
Unit tests for ConnectionManager without real network websockets.
"""
from __future__ import annotations

import pytest

from api.websocket_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.sent.append(message)


class FailingWebSocket(FakeWebSocket):
    async def send_json(self, message):
        raise RuntimeError("fail")


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenconnect_send_disconnectCalled_ThenSucceeds():
    m = ConnectionManager()
    ws = FakeWebSocket()

    await m.connect(ws, "u1")
    assert ws.accepted is True
    assert m.get_connection_count() == 1
    assert m.get_user_connection_count("u1") == 1
    assert "connection" in ws.sent[0]["type"]

    # send user message
    await m.send_user_message("u1", {"hello": 1})
    assert any(msg.get("hello") == 1 for msg in ws.sent)

    # broadcast
    await m.broadcast({"b": 2})
    assert any(msg.get("b") == 2 for msg in ws.sent)

    # handle ping
    await m.handle_message(ws, {"type": "ping"})
    assert any(msg.get("type") == "pong" for msg in ws.sent)

    # disconnect
    m.disconnect(ws)
    assert m.get_connection_count() == 0


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensend_personal_message_failure_removes_connectionCalled_ThenSucceeds():
    m = ConnectionManager()
    ws = FailingWebSocket()
    await m.connect(ws, "u2")
    # Initial connection confirmation send fails and triggers disconnect immediately
    assert m.get_connection_count() == 0


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenhandle_message_subscribe_and_unknownCalled_ThenSucceeds():
    m = ConnectionManager()
    ws = FakeWebSocket()
    await m.connect(ws, "u3")
    # subscribe branch (no exception expected)
    await m.handle_message(ws, {"type": "subscribe", "event_type": "progress"})
    # unknown type
    await m.handle_message(ws, {"type": "wat"})
    m.disconnect(ws)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenstart_and_stop_health_checksCalled_ThenSucceeds():
    m = ConnectionManager()
    await m.start_health_checks()
    await m.stop_health_checks()
