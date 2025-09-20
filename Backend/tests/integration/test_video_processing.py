"""Integration tests for video processing endpoints."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.config import settings
from tests.auth_helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_Whenvideo_listingCalled_ThenReturnsempty_list(async_http_client, monkeypatch, tmp_path):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_http_client.get(
            "/api/videos", headers=flow["headers"]
        )

        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_stream_missing_video_returns_404(async_http_client, monkeypatch, tmp_path):
    flow = await AuthTestHelperAsync.register_and_login_async(async_http_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_http_client.get(
            "/api/videos/Default/episode.mp4", headers=flow["headers"]
        )

        assert response.status_code == 404
