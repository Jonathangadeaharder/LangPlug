"""Focused negative tests for processing endpoints following the 80/20 guidelines."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import settings
from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFullPipelineMissingFields_ThenReturns422(async_client, url_builder):
    """Invalid input: omitting required fields yields validation errors."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    response = await async_client.post(
        url_builder.url_for("full_pipeline"),
        json={"source_lang": "en"},
        headers=auth["headers"],
    )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhentranscribeWithnon_video_extension_ThenRejects(async_client, url_builder):
    """Boundary: non-video file extension is rejected even when the file exists."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch.object(type(settings), "get_videos_path", return_value=Path("/videos")),
    ):
        response = await async_client.post(
            url_builder.url_for("transcribe_video"),
            json={"video_path": "notes.txt"},
            headers=auth["headers"],
        )

    assert response.status_code == 422


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFilterSubtitlesMissingFile_ThenReturns422(async_client, url_builder):
    """Invalid input: filtering without an existing subtitle file returns 422."""
    auth = await AuthTestHelperAsync.register_and_login_async(async_client)

    def mock_exists_func(self):
        return str(self).endswith(".mp4")

    with patch("pathlib.Path.exists", mock_exists_func):
        response = await async_client.post(
            url_builder.url_for("filter_subtitles"),
            json={"video_path": "series/video.mp4"},
            headers=auth["headers"],
        )

    assert response.status_code == 422
