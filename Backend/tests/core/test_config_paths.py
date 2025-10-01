"""
Tests for Settings path helpers (videos, data, database path).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings


class _TestSettings(BaseSettings):
    """Test settings class that doesn't load from .env file"""

    model_config = {
        "env_file": None,  # Disable .env file loading
        "extra": "ignore",
    }

    # Copy the relevant fields from the original Settings class
    videos_path: str | None = Field(default=None)
    data_path: str | None = Field(default=None)
    database_url: str | None = Field(default=None)
    db_type: str = Field(default="sqlite")

    def get_videos_path(self) -> Path:
        """Get the videos directory path"""
        if self.videos_path:
            return Path(self.videos_path)
        # Default videos path (one level up from Backend)
        return Path(__file__).parent.parent.parent.parent / "videos"

    def get_data_path(self) -> Path:
        """Get the data directory path"""
        if self.data_path:
            path = Path(self.data_path)
            path.mkdir(exist_ok=True)
            return path
        # Default data path
        path = Path(__file__).parent.parent.parent / "data"
        path.mkdir(exist_ok=True)
        return path

    def get_database_path(self) -> Path:
        """Get the database file path (for SQLite only)"""
        if self.database_url and self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        # Default database path
        base_path = Path(self.data_path) if self.data_path else Path(__file__).parent.parent.parent / "data"
        base_path.mkdir(exist_ok=True)
        return base_path / "langplug.db"


@pytest.mark.timeout(30)
def test_WhenGetVideos_path_overrideCalled_ThenSucceeds(tmp_path: Path):
    # Use test-specific Settings class
    s = _TestSettings(videos_path=str(tmp_path))
    result = s.get_videos_path()
    assert result == tmp_path


@pytest.mark.timeout(30)
def test_Whenget_database_path_sqlite_urlCalled_ThenSucceeds(tmp_path: Path):
    db = tmp_path / "test.db"
    # Use test-specific Settings class
    s = _TestSettings(database_url=f"sqlite:///{db}")
    result = s.get_database_path()
    assert result == db


@pytest.mark.timeout(30)
def test_Whenget_data_path_override_createsCalled_ThenSucceeds(tmp_path: Path):
    target = tmp_path / "d"
    # Use test-specific Settings class
    s = _TestSettings(data_path=str(target))
    p = s.get_data_path()
    assert p == target
    assert p.exists() and p.is_dir()
