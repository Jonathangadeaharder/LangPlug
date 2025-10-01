"""
Unit tests for parse_episode_filename helper in videos route.
"""

from __future__ import annotations

import pytest


@pytest.mark.timeout(30)
def test_Whenparse_episode_filename_basicCalled_ThenSucceeds():
    from api.routes.videos import parse_episode_filename

    info = parse_episode_filename("Episode 1 Staffel 2 My Show")
    assert info.get("episode") == "1"
    assert info.get("season") == "2"
    assert info.get("title").startswith("Episode 1")


@pytest.mark.timeout(30)
def test_Whenparse_episode_filename_missing_tokensCalled_ThenSucceeds():
    from api.routes.videos import parse_episode_filename

    info = parse_episode_filename("Pilot")
    assert info.get("episode") is None or info.get("episode") == "Pilot"
    assert info.get("title") == "Pilot"
