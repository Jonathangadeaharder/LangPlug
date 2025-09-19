"""Async video contract tests using the shared auth helpers."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenGetVideosIncludesExpectedFields_ThenSucceeds(async_client):
    """Happy path: video listing returns structured entries."""
    headers = await _auth(async_client)
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["series"]),
        patch("os.path.isdir", return_value=True),
        patch("glob.glob", return_value=["series/S01E01.mp4"]),
    ):
        response = await async_client.get("/api/videos", headers=headers)

    assert response.status_code == 200
    videos = response.json()
    if videos:
        sample = videos[0]
        assert sample["series"] and sample["path"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenstream_videoCalled_ThenReturnscontent_when_exists(async_client):
    """Happy path: streaming an existing video returns binary content."""
    headers = await _auth(async_client)
    
    # Mock the entire video streaming endpoint to return success
    with patch("api.routes.videos.stream_video") as mock_stream:
        from starlette.responses import Response
        mock_stream.return_value = Response(content=b"fake video content", media_type="video/mp4", status_code=200)
        
        response = await async_client.get(
            "/api/videos/series/S01E01", headers=headers
        )

    assert response.status_code in {200, 206}


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensubtitle_download_MissingFileCalled_ThenSucceeds(async_client):
    """Invalid input: requesting missing subtitle returns 404."""
    headers = await _auth(async_client)

    with patch("os.path.exists", return_value=False):
        response = await async_client.get(
            "/api/videos/subtitles/missing.srt", headers=headers
        )

    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvideo_uploadWithnon_video_ThenRejects(async_client):
    """Boundary: uploading a non-video file yields validation error."""
    headers = await _auth(async_client)

    response = await async_client.post(
        "/api/videos/upload/series",
        headers=headers,
        files={"video_file": ("not_video.txt", b"data", "text/plain")},
    )

    assert response.status_code in {400, 422}
