"""Focused video route tests that follow the 80/20 contract rules."""

from __future__ import annotations

import pytest

from tests.helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlist_videosCalled_ThenReturnsempty_when_path_missing(async_client, monkeypatch, tmp_path):
    """Boundary: missing videos directory yields empty list without error."""
    headers = await _auth(async_client)

    from api.routes import videos as vids

    missing = tmp_path / "none"
    monkeypatch.setattr(type(vids.settings), "get_videos_path", lambda self: missing)

    response = await async_client.get("/api/videos", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenGetSubtitlesServesExistingFile_ThenSucceeds(async_client, monkeypatch, tmp_path):
    """Happy path: subtitle retrieval returns stored content."""
    headers = await _auth(async_client)

    from api.routes import videos as vids

    monkeypatch.setattr(type(vids.settings), "get_videos_path", lambda self: tmp_path)

    subtitle = tmp_path / "example.srt"
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")

    response = await async_client.get("/api/videos/subtitles/example.srt", headers=headers)

    assert response.status_code == 200
    assert "Hello" in response.text


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenStreamVideoSetsAcceptRanges_ThenSucceeds(async_client, monkeypatch, tmp_path):
    """Happy path: streaming video responds with Accept-Ranges header."""
    headers = await _auth(async_client)

    from api.routes import videos as vids

    monkeypatch.setattr(type(vids.settings), "get_videos_path", lambda self: tmp_path)

    series_dir = tmp_path / "Series"
    series_dir.mkdir(parents=True)
    (series_dir / "Episode 1.mp4").write_bytes(b"video")

    response = await async_client.get("/api/videos/Series/Episode%201.mp4", headers=headers)

    # Without Range header, should return 200 (full content)
    assert (
        response.status_code == 200
    ), f"Expected 200 (full content without Range header), got {response.status_code}: {response.text}"
    assert response.headers.get("accept-ranges") == "bytes"
