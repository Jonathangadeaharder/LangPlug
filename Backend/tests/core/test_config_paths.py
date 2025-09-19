"""
Tests for Settings path helpers (videos, data, database path).
"""
from __future__ import annotations

from pathlib import Path
import pytest

from core.config import Settings


@pytest.mark.timeout(30)
def test_WhenGetVideos_path_overrideCalled_ThenSucceeds(tmp_path: Path):
    s = Settings(videos_path=str(tmp_path))
    assert s.get_videos_path() == tmp_path


@pytest.mark.timeout(30)
def test_Whenget_database_path_sqlite_urlCalled_ThenSucceeds(tmp_path: Path):
    db = tmp_path / "test.db"
    s = Settings(database_url=f"sqlite:///{db}")
    assert s.get_database_path() == db


@pytest.mark.timeout(30)
def test_Whenget_data_path_override_createsCalled_ThenSucceeds(tmp_path: Path):
    target = tmp_path / "d"
    s = Settings(data_path=str(target))
    p = s.get_data_path()
    assert p == target
    assert p.exists() and p.is_dir()

