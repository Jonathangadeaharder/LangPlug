"""Async video contract tests using the shared auth helpers."""

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

    # Create a temporary file for testing
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_file.write(b"fake video content")
        temp_file.flush()
        temp_path = Path(temp_file.name)

    try:
        # Mock the video service to return our temporary file
        with patch("services.videoservice.video_service.VideoService.get_video_file_path") as mock_path:
            mock_path.return_value = temp_path

            response = await async_client.get("/api/videos/series/S01E01", headers=headers)

        # Without Range header, should return 200 (full content)
        assert response.status_code == 200, f"Expected 200 (full content), got {response.status_code}"
    finally:
        # Clean up the temporary file
        if temp_path.exists():
            os.unlink(temp_path)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensubtitle_download_MissingFileCalled_ThenSucceeds(async_client):
    """Invalid input: requesting missing subtitle returns 404."""
    headers = await _auth(async_client)

    with patch("os.path.exists", return_value=False):
        response = await async_client.get("/api/videos/subtitles/missing.srt", headers=headers)

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

    # Invalid file type should return 422 (validation error)
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for wrong file type), got {response.status_code}: {response.text}"
