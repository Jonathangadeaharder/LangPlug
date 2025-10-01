"""Integration tests for upload endpoints using the in-process client."""

from __future__ import annotations

import io

import pytest

from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whensubtitle_uploadWithnon_srt_ThenRejects(async_http_client):
    """Invalid input: uploading a non-.srt file is rejected."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    response = await async_http_client.post(
        "/api/videos/subtitle/upload",
        headers=flow["headers"],
        files={"subtitle_file": ("notes.txt", b"not subtitle", "text/plain")},
        params={"video_path": "missing.mp4"},
    )

    # Invalid file type should return 422 (validation error)
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for invalid file), got {response.status_code}: {response.text}"


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvideo_uploadWithoutmp_ThenReturnsError4(async_http_client):
    """Boundary: non-mp4 uploads return a validation error."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    response = await async_http_client.post(
        "/api/videos/upload/series",
        headers=flow["headers"],
        files={"video_file": ("clip.txt", io.BytesIO(b"content"), "text/plain")},
    )

    # Invalid file type should return 422 (validation error)
    assert (
        response.status_code == 422
    ), f"Expected 422 (validation error for invalid file), got {response.status_code}: {response.text}"
