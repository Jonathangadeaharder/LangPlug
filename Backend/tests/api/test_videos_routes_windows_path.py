"""Windows path handling for subtitles route."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.auth_helpers import AuthTestHelperAsync


def _set_videos_path(monkeypatch, module, tmp_path: Path):
    monkeypatch.setattr(type(module.settings), "get_videos_path", lambda self: tmp_path)


@pytest.mark.anyio
@pytest.mark.timeout(30)
async def test_WhenWindowsAbsoluteSubtitlePath_ThenSucceeds(async_client, monkeypatch, tmp_path: Path):
    from api.routes import videos as vids
    _set_videos_path(monkeypatch, vids, tmp_path)

    (tmp_path / "example.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHi!\n\n", encoding="utf-8"
    )
    win_path = r"C:\\fake\\videos\\example.srt"

    auth = await AuthTestHelperAsync.register_and_login_async(async_client)
    response = await async_client.get(
        f"/api/videos/subtitles/{win_path}", headers=auth["headers"]
    )

    assert response.status_code == 200
    assert "Hi!" in response.text
