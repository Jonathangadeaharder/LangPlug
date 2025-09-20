"""Video contract tests aligned with the protective test policy."""
from __future__ import annotations

from unittest.mock import mock_open, patch

import pytest

from tests.auth_helpers import AuthTestHelper


def _auth_headers(client):
    flow = AuthTestHelper.register_and_login(client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenlist_videosCalled_ThenReturnscontract_payload(async_http_client, client):
    """Happy path: /videos returns a list of VideoInfo-like dictionaries."""
    headers = _auth_headers(client)
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["series"]),
        patch("os.path.isdir", return_value=True),
        patch("glob.glob", return_value=["series/S01E01.mp4"]),
    ):
        response = await async_http_client.get("/api/videos", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    if payload:
        video = payload[0]
        for field in {"series", "season", "episode", "title", "path", "has_subtitles"}:
            assert field in video


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenStreamVideoMissingFile_ThenReturns404(async_http_client, client):
    """Invalid input: streaming a missing video yields 404."""
    headers = _auth_headers(client)

    with patch("os.path.exists", return_value=False):
        response = await async_http_client.get(
            "/api/videos/missing/S01E01", headers=headers
        )

    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenupload_videoWithoutfile_ThenReturnsError(async_http_client, client):
    """Boundary: upload endpoint rejects requests without a file."""
    headers = _auth_headers(client)

    response = await async_http_client.post(
        "/api/videos/upload/test_series", headers=headers
    )

    assert response.status_code == 422
@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenUploadSubtitleAcceptsValidFile_ThenSucceeds(async_http_client, client):
    """Happy path: subtitle upload stores file when prerequisites satisfied."""
    headers = _auth_headers(client)
    subtitle_content = "1\n00:00:01,000 --> 00:00:02,000\nTest subtitle\n"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open()),
        patch("os.makedirs"),
    ):
        response = await async_http_client.post(
            "/api/videos/subtitle/upload",
            headers=headers,
            params={"video_path": "series/S01E01.mp4"},
            files={"subtitle_file": ("test.srt", subtitle_content.encode(), "text/plain")},
        )

    assert response.status_code in {200, 202}


