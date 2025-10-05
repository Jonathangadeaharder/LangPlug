"""Video negative-path tests under the 80/20 policy."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.config import settings
from tests.helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensubtitle_uploadWithoutsrt_extension_ThenReturnsError(async_client):
    """Invalid input: uploading non-.srt subtitles returns 400/422."""
    headers = await _auth(async_client)
    files = {"subtitle_file": ("bad.txt", b"content", "text/plain")}

    response = await async_client.post(
        "/api/videos/subtitle/upload",
        params={"video_path": "video.mp4"},
        files=files,
        headers=headers,
    )

    # Invalid subtitle file should return 400 (bad request)
    assert (
        response.status_code == 400
    ), f"Expected 400 (bad request for wrong file type), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenVideoUploadConflict_ThenReturns409(async_client, monkeypatch, tmp_path):
    """Boundary: uploading the same filename twice yields 409 conflict."""
    from core.file_security import FileSecurityValidator

    headers = await _auth(async_client)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    with (
        patch.object(type(settings), "get_videos_path", return_value=tmp_path),
        patch.object(FileSecurityValidator, "ALLOWED_UPLOAD_DIR", upload_dir),
    ):
        files = {"video_file": ("Episode.mp4", b"x", "video/mp4")}
        first = await async_client.post("/api/videos/upload/Series", files=files, headers=headers)
        assert first.status_code == 200
        second = await async_client.post("/api/videos/upload/Series", files=files, headers=headers)
    assert second.status_code == 409


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenstream_unknown_videoCalled_ThenReturnsnot_found(async_client):
    """Invalid input: requesting an unknown video returns 404."""
    headers = await _auth(async_client)
    with patch("os.path.exists", return_value=False):
        response = await async_client.get("/api/videos/unknown/episode", headers=headers)
    assert response.status_code == 404
