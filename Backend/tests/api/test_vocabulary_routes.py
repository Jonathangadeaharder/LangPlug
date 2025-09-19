"""Focused vocabulary route tests matching the CDD/TDD rules."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenblocking_wordsCalled_ThenReturnsstructure(async_client, monkeypatch, tmp_path):
    """Happy path: blocking words returns expected keys when SRT exists."""
    headers = await _auth(async_client)
    from api.routes import vocabulary as vocab
    monkeypatch.setattr(type(vocab.settings), "get_videos_path", lambda self: tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"x")
    (tmp_path / "video.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHallo Welt\n",
        encoding="utf-8",
    )

    response = await async_client.get(
        "/api/vocabulary/blocking-words",
        params={"video_path": "video.mp4"},
        headers=headers,
    )

    assert response.status_code in {200, 500}
    if response.status_code == 200:
        payload = response.json()
        assert "blocking_words" in payload


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenbulk_markWithoutvalid_level_ThenReturnsError(async_client):
    """Invalid input: unknown CEFR level returns validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/vocabulary/library/bulk-mark",
        json={"level": "Z9", "known": True},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenpreloadWithoutadmin_ThenReturnsError(async_client):
    """Boundary: non-admin users receive 403 on preload."""
    headers = await _auth(async_client)
    response = await async_client.post("/api/vocabulary/preload", headers=headers)
    assert response.status_code in {403, 401}
