"""Windows path handling for subtitles route."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import AsyncAuthHelper


def _set_videos_path(monkeypatch, module, tmp_path: Path):
    from core.config import settings

    monkeypatch.setattr(type(settings), "get_videos_path", lambda self: tmp_path)


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_WhenWindowsAbsoluteSubtitlePath_ThenSucceeds(async_client, url_builder, monkeypatch, tmp_path: Path):
    from api.routes import videos as vids

    _set_videos_path(monkeypatch, vids, tmp_path)

    (tmp_path / "example.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHi!\n\n", encoding="utf-8")
    win_path = r"C:\\fake\\videos\\example.srt"

    helper = AsyncAuthHelper(async_client)
    _user, _token, headers = await helper.create_authenticated_user()
    response = await async_client.get(url_builder.url_for("get_subtitles", subtitle_path=win_path), headers=headers)

    assert response.status_code == 200
    assert "Hi!" in response.text
