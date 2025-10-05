"""Integration tests for file processing workflows."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.config import settings
from tests.helpers import AuthTestHelperAsync


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenFilterSubtitlesWithoutexisting_file_ThenRejected(async_client, url_builder, monkeypatch, tmp_path):
    """Invalid input: filter-subtitles fails when subtitle file absent."""
    flow = await AuthTestHelperAsync.register_and_login_async(async_client)

    with patch.object(type(settings), "get_videos_path", return_value=tmp_path):
        response = await async_client.post(
            url_builder.url_for("filter_subtitles"),
            json={"video_path": "missing.mp4"},
            headers=flow["headers"],
        )

        assert response.status_code == 422


# Test removed: /api/process/translate-subtitles endpoint was deprecated during refactoring
# Use /api/process/apply-selective-translations instead
