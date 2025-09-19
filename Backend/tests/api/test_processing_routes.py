"""Processing route smoke tests adhering to the 80/20 contract coverage."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


async def _auth(async_client):
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)
    return flow["headers"]


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenChunkEndpointProcessesExistingVideo_ThenSucceeds(async_client, tmp_path, monkeypatch):
    """Happy path: chunk processing returns a task id when the file exists."""
    headers = await _auth(async_client)
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"00")

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_client.post(
            "/api/process/chunk",
            json={"video_path": video_path.name, "start_time": 0, "end_time": 5},
            headers=headers,
        )

    assert response.status_code in {200, 202}
    assert "task" in response.text or "task_id" in response.text


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenchunk_endpointWithoutvalid_window_ThenReturnsError(async_client, tmp_path, monkeypatch):
    """Invalid input: end_time <= start_time triggers validation error."""
    headers = await _auth(async_client)
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"00")

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_client.post(
            "/api/process/chunk",
            json={"video_path": video_path.name, "start_time": 10, "end_time": 5},
            headers=headers,
        )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenchunk_endpointWithoutexisting_file_ThenReturnsError(async_client, tmp_path, monkeypatch):
    """Boundary: non-existent file returns 404 contract response."""
    headers = await _auth(async_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_client.post(
            "/api/process/chunk",
            json={"video_path": "missing.mp4", "start_time": 0, "end_time": 5},
            headers=headers,
        )

    assert response.status_code == 404
