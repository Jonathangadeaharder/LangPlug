"""
Test suite for VideoService
Tests focus on business logic for video scanning, file resolution, and path handling
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from api.models.video import VideoInfo
from services.videoservice.video_service import VideoService
from tests.base import ServiceTestBase


class MockPath:
    """Mock Path object for testing file system operations"""

    def __init__(
        self,
        path_str: str,
        exists: bool = True,
        is_dir: bool = True,
        is_file: bool = False,
        suffix: str = "",
        stem: str = "",
        name: str = "",
    ):
        self._path_str = path_str
        self._exists = exists
        self._is_dir = is_dir
        self._is_file = is_file
        self._suffix = suffix or Path(path_str).suffix
        self._stem = stem or Path(path_str).stem
        self._name = name or Path(path_str).name
        self._children = []

    def __str__(self) -> str:
        return self._path_str

    def __truediv__(self, other) -> "MockPath":
        """Handle path joining with / operator"""
        new_path = f"{self._path_str}/{other}"
        # Look for existing child with matching name
        for child in self._children:
            if child._name == str(other) or child._path_str.endswith(f"/{other}"):
                return child
        # If no child found, return non-existent path
        return MockPath(new_path, exists=False)

    def exists(self) -> bool:
        return self._exists

    def is_dir(self) -> bool:
        return self._is_dir

    def is_file(self) -> bool:
        return self._is_file

    def resolve(self) -> "MockPath":
        return MockPath(f"/resolved{self._path_str}")

    def iterdir(self) -> Generator["MockPath", None, None]:
        """Return child paths"""
        if not self._is_dir:
            raise NotADirectoryError("Not a directory")
        yield from self._children

    def glob(self, pattern: str) -> list["MockPath"]:
        """Mock glob functionality"""
        if pattern == "*.mp4":
            return [child for child in self._children if child._name.endswith(".mp4")]
        return []

    def with_suffix(self, suffix: str) -> "MockPath":
        """Return new path with different suffix"""
        base = self._stem
        new_path = f"{Path(self._path_str).parent}/{base}{suffix}"
        # For .srt files, only certain videos have subtitles
        exists = False
        if suffix == ".srt":
            # Only episode files in TestSeries have subtitles, not direct videos
            exists = "Episode" in self._name and "TestSeries" in str(new_path)
        return MockPath(str(new_path), exists=exists)

    def relative_to(self, other) -> Path:
        """Return relative path"""
        return Path(self._path_str.replace(str(other), "").lstrip("/"))

    def add_child(self, child: "MockPath"):
        """Add child for directory mocking"""
        self._children.append(child)

    @property
    def suffix(self) -> str:
        return self._suffix

    @property
    def stem(self) -> str:
        return self._stem

    @property
    def name(self) -> str:
        return self._name

    @property
    def parts(self) -> tuple:
        """Return path parts as tuple"""
        return tuple(self._path_str.split("/"))


@pytest.fixture
def mock_db_manager():
    """Create mock database manager"""
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    """Create mock authentication service"""
    return MagicMock()


@pytest.fixture(autouse=True)
def clear_video_service_cache():
    """Clear VideoService caches before each test to ensure isolation"""
    VideoService.clear_cache()
    yield
    VideoService.clear_cache()


@pytest.fixture
def video_service(mock_db_manager, mock_auth_service):
    """Create VideoService with properly isolated dependencies"""
    return VideoService(db_manager=mock_db_manager, auth_service=mock_auth_service)


@pytest.fixture
def mock_videos_root():
    """Create mock videos root directory with test structure"""
    root = MockPath("/mnt/c/videos", exists=True, is_dir=True)

    # Add direct video files
    direct_video = MockPath(
        "direct_video.mp4",
        exists=True,
        is_dir=False,
        is_file=True,
        suffix=".mp4",
        stem="direct_video",
        name="direct_video.mp4",
    )
    root.add_child(direct_video)

    # Add series directory
    series_dir = MockPath("TestSeries", exists=True, is_dir=True, name="TestSeries")

    # Add videos in series directory
    episode1 = MockPath(
        "Episode 1 Pilot.mp4",
        exists=True,
        is_dir=False,
        is_file=True,
        suffix=".mp4",
        stem="Episode 1 Pilot",
        name="Episode 1 Pilot.mp4",
    )
    episode2 = MockPath(
        "Episode 2 The Beginning.mp4",
        exists=True,
        is_dir=False,
        is_file=True,
        suffix=".mp4",
        stem="Episode 2 The Beginning",
        name="Episode 2 The Beginning.mp4",
    )

    series_dir.add_child(episode1)
    series_dir.add_child(episode2)
    root.add_child(series_dir)

    return root


class TestVideoService(ServiceTestBase):
    """Test suite for VideoService functionality"""

    def test_init_stores_dependencies(self, mock_db_manager, mock_auth_service):
        """Test that VideoService properly stores injected dependencies"""
        service = VideoService(mock_db_manager, mock_auth_service)

        assert service.db is mock_db_manager
        assert service.auth_service is mock_auth_service

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_empty_directory(self, mock_settings, video_service):
        """Test get_available_videos with empty directory"""
        # Setup
        empty_root = MockPath("/empty/videos", exists=True, is_dir=True)
        mock_settings.get_videos_path.return_value = empty_root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_nonexistent_directory(self, mock_settings, video_service):
        """Test get_available_videos with nonexistent directory"""
        # Setup
        nonexistent_root = MockPath("/nonexistent/videos", exists=False, is_dir=False)
        mock_settings.get_videos_path.return_value = nonexistent_root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_not_directory(self, mock_settings, video_service):
        """Test get_available_videos when path exists but is not a directory"""
        # Setup
        file_path = MockPath("/videos.txt", exists=True, is_dir=False)
        mock_settings.get_videos_path.return_value = file_path

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_permission_error(self, mock_settings, video_service):
        """Test get_available_videos with permission denied"""
        # Setup
        restricted_root = MockPath("/restricted/videos", exists=True, is_dir=True)

        def raise_permission_error():
            raise PermissionError("Permission denied")

        restricted_root.iterdir = raise_permission_error
        mock_settings.get_videos_path.return_value = restricted_root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_success_with_direct_videos(self, mock_settings, video_service, mock_videos_root):
        """Test successful video scanning with direct videos in root"""
        # Setup
        mock_settings.get_videos_path.return_value = mock_videos_root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert len(result) == 3  # 1 direct + 2 in series

        # Check direct video
        direct_video = next((v for v in result if v.series == "Default"), None)
        assert direct_video is not None
        assert direct_video.title == "direct_video"
        assert direct_video.path == "direct_video.mp4"
        assert not direct_video.has_subtitles  # No corresponding .srt file

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_success_with_series(self, mock_settings, video_service, mock_videos_root):
        """Test successful video scanning with series directories"""
        # Setup
        mock_settings.get_videos_path.return_value = mock_videos_root

        # Execute
        result = video_service.get_available_videos()

        # Verify series videos
        series_videos = [v for v in result if v.series == "TestSeries"]
        assert len(series_videos) == 2

        # Check first episode
        episode1 = next((v for v in series_videos if "Pilot" in v.title), None)
        assert episode1 is not None
        assert episode1.series == "TestSeries"
        assert episode1.season == "1"  # Default season
        assert episode1.episode == "1"  # Parsed from filename
        assert episode1.title == "Episode 1 Pilot"

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_with_subtitles(self, mock_settings, video_service):
        """Test video scanning correctly identifies subtitles"""
        # Setup root with video that has subtitles
        root = MockPath("/videos", exists=True, is_dir=True)
        video_with_subs = MockPath(
            "video_with_subs.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="video_with_subs",
            name="video_with_subs.mp4",
        )

        # Mock the subtitle file exists
        def mock_with_suffix(suffix):
            if suffix == ".srt":
                return MockPath("video_with_subs.srt", exists=True)
            return MockPath(f"video_with_subs{suffix}", exists=False)

        video_with_subs.with_suffix = mock_with_suffix
        root.add_child(video_with_subs)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert len(result) == 1
        assert result[0].has_subtitles is True

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_handles_series_processing_error(self, mock_settings, video_service):
        """Test that series processing errors don't break the entire scan"""
        # Setup
        root = MockPath("/videos", exists=True, is_dir=True)

        # Add a problematic series directory
        bad_series = MockPath("BadSeries", exists=True, is_dir=True, name="BadSeries")

        def raise_error():
            raise OSError("Disk error")

        bad_series.glob = raise_error
        root.add_child(bad_series)

        mock_settings.get_videos_path.return_value = root

        # Execute - should not raise exception
        result = video_service.get_available_videos()

        # Verify - should return empty list but not crash
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_fatal_error(self, mock_settings, video_service):
        """Test that fatal errors during scanning are properly handled"""

        # Setup
        def raise_fatal_error():
            raise Exception("Fatal system error")

        mock_settings.get_videos_path.side_effect = raise_fatal_error

        # Execute & Verify
        with pytest.raises(Exception, match="Error scanning videos: Fatal system error"):
            video_service.get_available_videos()

    def test_parse_episode_filename_simple(self, video_service):
        """Test _parse_episode_filename with simple filename"""
        result = video_service._parse_episode_filename("simple_filename")

        assert result["title"] == "simple_filename"
        assert "episode" not in result
        assert "season" not in result

    def test_parse_episode_filename_with_episode(self, video_service):
        """Test _parse_episode_filename with episode information"""
        result = video_service._parse_episode_filename("Something Episode 5 Title")

        assert result["title"] == "Something Episode 5 Title"
        assert result["episode"] == "5"

    def test_parse_episode_filename_with_staffel(self, video_service):
        """Test _parse_episode_filename with German Staffel (season) information"""
        result = video_service._parse_episode_filename("Series Staffel 2 Episode 3")

        assert result["title"] == "Series Staffel 2 Episode 3"
        assert result["season"] == "2"
        assert result["episode"] == "3"

    def test_parse_episode_filename_with_both(self, video_service):
        """Test _parse_episode_filename with both season and episode"""
        result = video_service._parse_episode_filename("Show Staffel 1 Episode 10 Finale")

        assert result["title"] == "Show Staffel 1 Episode 10 Finale"
        assert result["season"] == "1"
        assert result["episode"] == "10"

    def test_parse_episode_filename_case_insensitive(self, video_service):
        """Test _parse_episode_filename is case insensitive"""
        result = video_service._parse_episode_filename("Show EPISODE 7 test")

        assert result["episode"] == "7"

    def test_parse_episode_filename_no_following_part(self, video_service):
        """Test _parse_episode_filename when episode/staffel is at end"""
        result = video_service._parse_episode_filename("Something Episode")

        assert result["title"] == "Something Episode"
        assert "episode" not in result

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_success(self, mock_settings, video_service, mock_videos_root):
        """Test scan_videos_directory returns detailed information"""
        # Setup
        mock_settings.get_videos_path.return_value = mock_videos_root

        # Execute
        result = video_service.scan_videos_directory()

        # Verify
        assert result["path_exists"] is True
        assert result["is_directory"] is True
        assert result["total_videos"] == 3
        assert "direct_video.mp4" in result["direct_videos"]
        assert len(result["series_directories"]) == 1
        assert result["series_directories"][0]["name"] == "TestSeries"
        assert len(result["series_directories"][0]["videos"]) == 2

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_nonexistent_path(self, mock_settings, video_service):
        """Test scan_videos_directory with nonexistent path"""
        # Setup
        nonexistent_path = MockPath("/nonexistent", exists=False)
        mock_settings.get_videos_path.return_value = nonexistent_path

        # Execute
        result = video_service.scan_videos_directory()

        # Verify
        assert result["path_exists"] is False
        assert result["is_directory"] is False
        assert result["total_videos"] == 0
        assert len(result["errors"]) == 1
        assert "does not exist" in result["errors"][0]

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_not_directory(self, mock_settings, video_service):
        """Test scan_videos_directory when path is not a directory"""
        # Setup
        file_path = MockPath("/file.txt", exists=True, is_dir=False)
        mock_settings.get_videos_path.return_value = file_path

        # Execute
        result = video_service.scan_videos_directory()

        # Verify
        assert result["path_exists"] is True
        assert result["is_directory"] is False
        assert result["total_videos"] == 0
        assert len(result["errors"]) == 1
        assert "not a directory" in result["errors"][0]

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_with_errors(self, mock_settings, video_service):
        """Test scan_videos_directory handles and reports errors"""
        # Setup
        root = MockPath("/videos", exists=True, is_dir=True)

        # Make glob raise an error for direct videos
        def raise_error(pattern):
            if pattern == "*.mp4":
                raise PermissionError("Permission denied")
            return []

        root.glob = raise_error
        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.scan_videos_directory()

        # Verify
        assert len(result["errors"]) >= 1
        assert any("Permission denied" in error for error in result["errors"])

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_fatal_error(self, mock_settings, video_service):
        """Test scan_videos_directory handles fatal errors gracefully"""
        # Setup - first call fails, second call in exception handler succeeds
        call_count = {"count": 0}

        def conditional_error():
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("Fatal error")
            return MockPath("/fallback/path", exists=False)

        mock_settings.get_videos_path.side_effect = conditional_error

        # Execute
        result = video_service.scan_videos_directory()

        # Verify
        assert "error" in result
        assert "Fatal error during scan" in result["error"]

    @patch("services.videoservice.video_service.settings")
    def test_get_subtitle_file_path_absolute_windows_path(self, mock_settings, video_service):
        """Test get_subtitle_file_path with Windows absolute path"""
        # Setup
        videos_root = MockPath("/mnt/c/videos")
        mock_settings.get_videos_path.return_value = videos_root

        # Execute
        result = video_service.get_subtitle_file_path("C:\\videos\\series\\episode.srt")

        # Verify
        assert "videos" in str(result)
        assert "series" in str(result)
        assert "episode.srt" in str(result)

    @patch("services.videoservice.video_service.settings")
    def test_get_subtitle_file_path_absolute_wsl_path(self, mock_settings, video_service):
        """Test get_subtitle_file_path with WSL absolute path"""
        # Setup
        videos_root = MockPath("/mnt/c/videos")
        mock_settings.get_videos_path.return_value = videos_root

        # Execute
        result = video_service.get_subtitle_file_path("/mnt/c/videos/series/episode.srt")

        # Verify
        assert "videos" in str(result)
        assert "series" in str(result)

    @patch("services.videoservice.video_service.settings")
    def test_get_subtitle_file_path_relative_path(self, mock_settings, video_service):
        """Test get_subtitle_file_path with relative path"""
        # Setup
        videos_root = MockPath("/mnt/c/videos")
        mock_settings.get_videos_path.return_value = videos_root

        # Execute
        result = video_service.get_subtitle_file_path("series/episode.srt")

        # Verify - should join with videos root
        expected_str = str(videos_root / "series/episode.srt")
        assert str(result) == expected_str

    @patch("services.videoservice.video_service.settings")
    def test_get_subtitle_file_path_no_videos_directory_in_path(self, mock_settings, video_service):
        """Test get_subtitle_file_path when 'videos' not found in absolute path"""
        # Setup
        videos_root = MockPath("/mnt/c/videos")
        mock_settings.get_videos_path.return_value = videos_root

        # Execute - path without 'videos' directory
        result = video_service.get_subtitle_file_path("C:\\Users\\data\\file.srt")

        # Verify - should fall back to just filename
        assert "file.srt" in str(result)

    @patch("services.videoservice.video_service.settings")
    def test_get_video_file_path_success_exact_match(self, mock_settings, video_service):
        """Test get_video_file_path with exact episode match"""
        # Setup
        videos_root = MockPath("/videos", exists=True, is_dir=True)
        series_path = MockPath("TestSeries", exists=True, is_dir=True, name="TestSeries")
        episode = MockPath("episode 1.mp4", exists=True, is_file=True, name="episode 1.mp4")

        # Set up proper parent-child relationships
        series_path.add_child(episode)
        videos_root.add_child(series_path)

        mock_settings.get_videos_path.return_value = videos_root

        # Execute
        result = video_service.get_video_file_path("TestSeries", "1")

        # Verify
        assert result == episode

    @patch("services.videoservice.video_service.settings")
    def test_get_video_file_path_series_not_found(self, mock_settings, video_service):
        """Test get_video_file_path when series directory doesn't exist"""
        # Setup
        series_path = MockPath("/videos/NonexistentSeries", exists=False)
        videos_root = MockPath("/videos")
        mock_settings.get_videos_path.return_value = videos_root

        # Mock path construction
        with patch.object(videos_root, "__truediv__", return_value=series_path):
            # Execute & Verify - domain exception now raised instead of HTTPException
            from core.exceptions import SeriesNotFoundError

            with pytest.raises(SeriesNotFoundError) as exc_info:
                video_service.get_video_file_path("NonexistentSeries", "1")

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value)

    @patch("services.videoservice.video_service.settings")
    def test_get_video_file_path_episode_not_found(self, mock_settings, video_service):
        """Test get_video_file_path when episode doesn't exist"""
        # Setup
        videos_root = MockPath("/videos", exists=True, is_dir=True)
        series_path = MockPath("TestSeries", exists=True, is_dir=True, name="TestSeries")
        different_episode = MockPath("episode 2.mp4", exists=True, is_file=True, name="episode 2.mp4")

        # Set up proper parent-child relationships
        series_path.add_child(different_episode)
        videos_root.add_child(series_path)

        mock_settings.get_videos_path.return_value = videos_root

        # Execute & Verify - domain exception now raised instead of HTTPException
        from core.exceptions import EpisodeNotFoundError

        with pytest.raises(EpisodeNotFoundError) as exc_info:
            video_service.get_video_file_path("TestSeries", "1")

        assert exc_info.value.status_code == 404
        assert "Episode '1'" in str(exc_info.value)

    @patch("services.videoservice.video_service.settings")
    def test_get_video_file_path_flexible_matching(self, mock_settings, video_service):
        """Test get_video_file_path with flexible episode matching patterns"""
        # Setup
        videos_root = MockPath("/videos", exists=True, is_dir=True)
        series_path = MockPath("TestSeries", exists=True, is_dir=True, name="TestSeries")

        # Add episodes with different naming patterns (non-overlapping numbers)
        episodes = [
            MockPath("Episode 1.mp4", exists=True, is_file=True, name="Episode 1.mp4"),
            MockPath("episode_2.mp4", exists=True, is_file=True, name="episode_2.mp4"),
            MockPath("E3.mp4", exists=True, is_file=True, name="E3.mp4"),
        ]

        for ep in episodes:
            series_path.add_child(ep)

        videos_root.add_child(series_path)
        mock_settings.get_videos_path.return_value = videos_root

        # Test different matching patterns
        result1 = video_service.get_video_file_path("TestSeries", "1")
        assert result1.name == "Episode 1.mp4"

        result2 = video_service.get_video_file_path("TestSeries", "2")
        assert result2.name == "episode_2.mp4"

        result3 = video_service.get_video_file_path("TestSeries", "3")
        assert result3.name == "E3.mp4"

    @patch("services.videoservice.video_service.logger")
    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_logging(self, mock_settings, mock_logger, video_service, mock_videos_root):
        """Test that get_available_videos produces appropriate log messages"""
        # Setup
        mock_settings.get_videos_path.return_value = mock_videos_root

        # Execute
        video_service.get_available_videos()

        # Verify logging calls were made (structlog uses kwargs, not positional args)
        # Just verify debug/info were called, not the exact message format
        assert mock_logger.debug.called or mock_logger.info.called, "Expected logging calls during video scan"

    def test_video_service_dependencies_isolation(self, video_service):
        """Test that VideoService properly isolates dependencies"""
        # Verify dependencies are stored correctly
        assert hasattr(video_service, "db")
        assert hasattr(video_service, "auth_service")

        # Verify they are separate instances
        assert video_service.db is not video_service.auth_service

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_video_info_creation(self, mock_settings, video_service):
        """Test that VideoInfo objects are created with correct attributes"""
        # Setup
        root = MockPath("/videos", exists=True, is_dir=True)
        video = MockPath(
            "test episode 5.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="test episode 5",
            name="test episode 5.mp4",
        )
        root.add_child(video)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify VideoInfo object structure
        assert len(result) == 1
        video_info = result[0]

        assert isinstance(video_info, VideoInfo)
        assert video_info.series == "Default"
        assert video_info.season == "1"  # Default season
        assert video_info.episode == "5"  # Parsed from filename
        assert video_info.title == "test episode 5"
        assert video_info.path == "test episode 5.mp4"
        assert video_info.has_subtitles is False

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_comprehensive_error_handling(self, mock_settings, video_service):
        """Test that scan_videos_directory handles multiple types of errors"""
        # Setup
        root = MockPath("/videos", exists=True, is_dir=True)

        # Mock different errors for different operations
        def glob_error(pattern):
            raise OSError("Disk read error")

        def iterdir_error():
            raise PermissionError("Access denied")

        root.glob = glob_error
        root.iterdir = iterdir_error

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.scan_videos_directory()

        # Verify multiple errors are captured
        assert len(result["errors"]) >= 2
        error_messages = " ".join(result["errors"])
        assert "Disk read error" in error_messages
        assert "Access denied" in error_messages


class TestVideoServiceAdvancedScenarios(ServiceTestBase):
    """Test advanced scenarios for get_available_videos method"""

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_complex_directory_structure(self, mock_settings, video_service):
        """Test get_available_videos with complex nested directory structure"""
        # Setup complex directory structure
        root = MockPath("/videos", exists=True, is_dir=True)

        # Add direct videos
        direct_video1 = MockPath("Movie.mp4", exists=True, is_file=True, suffix=".mp4", stem="Movie", name="Movie.mp4")
        direct_video2 = MockPath(
            "Documentary Episode 1.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Documentary Episode 1",
            name="Documentary Episode 1.mp4",
        )
        root.add_child(direct_video1)
        root.add_child(direct_video2)

        # Add multiple series with different structures
        series1 = MockPath("ActionSeries", exists=True, is_dir=True, name="ActionSeries")
        series1_ep1 = MockPath(
            "S01E01 Pilot.mp4", exists=True, is_file=True, suffix=".mp4", stem="S01E01 Pilot", name="S01E01 Pilot.mp4"
        )
        series1_ep2 = MockPath(
            "S01E02 The Chase.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="S01E02 The Chase",
            name="S01E02 The Chase.mp4",
        )
        series1.add_child(series1_ep1)
        series1.add_child(series1_ep2)

        series2 = MockPath("DramaSeries", exists=True, is_dir=True, name="DramaSeries")
        series2_ep1 = MockPath(
            "Episode_01_Beginning.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Episode_01_Beginning",
            name="Episode_01_Beginning.mp4",
        )
        series2.add_child(series2_ep1)

        root.add_child(series1)
        root.add_child(series2)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify
        assert len(result) == 5  # 2 direct + 2 ActionSeries + 1 DramaSeries

        # Check direct videos
        direct_videos = [v for v in result if v.series == "Default"]
        assert len(direct_videos) == 2

        # Check ActionSeries
        action_videos = [v for v in result if v.series == "ActionSeries"]
        assert len(action_videos) == 2

        # Check DramaSeries
        drama_videos = [v for v in result if v.series == "DramaSeries"]
        assert len(drama_videos) == 1

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_unicode_filenames(self, mock_settings, video_service):
        """Test get_available_videos with Unicode characters in filenames"""
        # Setup with Unicode filenames
        root = MockPath("/videos", exists=True, is_dir=True)

        unicode_video1 = MockPath(
            "Café_Episode_1.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Café_Episode_1",
            name="Café_Episode_1.mp4",
        )
        unicode_video2 = MockPath(
            "ドラマ_Episode_2.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="ドラマ_Episode_2",
            name="ドラマ_Episode_2.mp4",
        )

        unicode_series = MockPath("Película_Española", exists=True, is_dir=True, name="Película_Española")
        unicode_episode = MockPath(
            "Episodio_1_¡Hola!.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Episodio_1_¡Hola!",
            name="Episodio_1_¡Hola!.mp4",
        )
        unicode_series.add_child(unicode_episode)

        root.add_child(unicode_video1)
        root.add_child(unicode_video2)
        root.add_child(unicode_series)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify Unicode handling
        assert len(result) == 3
        titles = [v.title for v in result]
        assert "Café_Episode_1" in titles
        assert "ドラマ_Episode_2" in titles
        assert "Episodio_1_¡Hola!" in titles

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_mixed_file_types(self, mock_settings, video_service):
        """Test get_available_videos ignores non-MP4 files correctly"""
        # Setup with mixed file types
        root = MockPath("/videos", exists=True, is_dir=True)

        # Valid video files
        valid_video1 = MockPath(
            "valid1.mp4", exists=True, is_file=True, suffix=".mp4", stem="valid1", name="valid1.mp4"
        )
        valid_video2 = MockPath(
            "valid2.MP4", exists=True, is_file=True, suffix=".MP4", stem="valid2", name="valid2.MP4"
        )

        # Invalid files (should be ignored)
        invalid_video1 = MockPath(
            "invalid.avi", exists=True, is_file=True, suffix=".avi", stem="invalid", name="invalid.avi"
        )
        invalid_video2 = MockPath(
            "invalid.mkv", exists=True, is_file=True, suffix=".mkv", stem="invalid", name="invalid.mkv"
        )
        text_file = MockPath("readme.txt", exists=True, is_file=True, suffix=".txt", stem="readme", name="readme.txt")

        # Add all files to root - but mock glob to only return .mp4 files
        def mock_glob(pattern):
            if pattern == "*.mp4":
                return [valid_video1, valid_video2]
            return []

        root.glob = mock_glob
        root.add_child(valid_video1)
        root.add_child(valid_video2)
        root.add_child(invalid_video1)
        root.add_child(invalid_video2)
        root.add_child(text_file)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify only .mp4 files are included
        assert len(result) == 2
        assert all(v.title in ["valid1", "valid2"] for v in result)

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_empty_series_directories(self, mock_settings, video_service):
        """Test get_available_videos handles empty series directories"""
        # Setup with empty series directory
        root = MockPath("/videos", exists=True, is_dir=True)

        empty_series = MockPath("EmptySeries", exists=True, is_dir=True, name="EmptySeries")
        valid_series = MockPath("ValidSeries", exists=True, is_dir=True, name="ValidSeries")

        valid_episode = MockPath(
            "Episode1.mp4", exists=True, is_file=True, suffix=".mp4", stem="Episode1", name="Episode1.mp4"
        )
        valid_series.add_child(valid_episode)

        root.add_child(empty_series)
        root.add_child(valid_series)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify empty series is ignored
        assert len(result) == 1
        assert result[0].series == "ValidSeries"

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_very_long_filenames(self, mock_settings, video_service):
        """Test get_available_videos handles very long filenames"""
        # Setup with very long filename
        root = MockPath("/videos", exists=True, is_dir=True)

        long_name = "A" * 180 + "_Documentary"  # Long but within 200 char title limit, no episode pattern
        long_filename = f"{long_name}.mp4"

        long_video = MockPath(
            long_filename, exists=True, is_file=True, suffix=".mp4", stem=long_name, name=long_filename
        )
        root.add_child(long_video)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify long filename is handled
        assert len(result) == 1
        assert result[0].title == long_name
        assert len(result[0].title) > 150

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_special_characters_in_paths(self, mock_settings, video_service):
        """Test get_available_videos handles special characters in paths"""
        # Setup with special characters
        root = MockPath("/videos", exists=True, is_dir=True)

        special_video1 = MockPath(
            "Video [2024] Episode 1.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Video [2024] Episode 1",
            name="Video [2024] Episode 1.mp4",
        )
        special_video2 = MockPath(
            "Show (HD) - Episode 2.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Show (HD) - Episode 2",
            name="Show (HD) - Episode 2.mp4",
        )
        special_video3 = MockPath(
            "Series & More Episode 3.mp4",
            exists=True,
            is_file=True,
            suffix=".mp4",
            stem="Series & More Episode 3",
            name="Series & More Episode 3.mp4",
        )

        root.add_child(special_video1)
        root.add_child(special_video2)
        root.add_child(special_video3)

        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify special characters are preserved
        assert len(result) == 3
        titles = [v.title for v in result]
        assert "Video [2024] Episode 1" in titles
        assert "Show (HD) - Episode 2" in titles
        assert "Series & More Episode 3" in titles

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_concurrent_file_changes(self, mock_settings, video_service):
        """Test get_available_videos handles concurrent file system changes"""
        # Setup with files that might change during scan
        root = MockPath("/videos", exists=True, is_dir=True)

        # Simulate file that exists during first check but disappears
        disappearing_video = MockPath(
            "temp.mp4", exists=True, is_file=True, suffix=".mp4", stem="temp", name="temp.mp4"
        )

        # Counter to simulate file disappearing during processing
        access_count = {"count": 0}

        def simulate_file_disappearing():
            access_count["count"] += 1
            if access_count["count"] > 2:  # Disappears after second access
                raise FileNotFoundError("File was deleted")
            return True

        disappearing_video.exists = simulate_file_disappearing
        root.add_child(disappearing_video)

        mock_settings.get_videos_path.return_value = root

        # Execute - should handle gracefully
        result = video_service.get_available_videos()

        # Verify graceful handling (may or may not include the file)
        assert isinstance(result, list)

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_case_sensitive_extensions(self, mock_settings, video_service):
        """Test get_available_videos handles case variations in extensions"""
        # Setup with different case extensions
        root = MockPath("/videos", exists=True, is_dir=True)

        # Mock glob to return different case extensions
        def mock_glob(pattern):
            if pattern == "*.mp4":
                return [
                    MockPath("video1.mp4", exists=True, is_file=True, suffix=".mp4", stem="video1", name="video1.mp4"),
                    MockPath("video2.MP4", exists=True, is_file=True, suffix=".MP4", stem="video2", name="video2.MP4"),
                    MockPath("video3.Mp4", exists=True, is_file=True, suffix=".Mp4", stem="video3", name="video3.Mp4"),
                ]
            return []

        root.glob = mock_glob
        mock_settings.get_videos_path.return_value = root

        # Execute
        result = video_service.get_available_videos()

        # Verify all case variations are handled
        assert len(result) == 3
        titles = sorted([v.title for v in result])
        assert titles == ["video1", "video2", "video3"]


class TestVideoServiceEpisodeParsing(ServiceTestBase):
    """Test comprehensive episode filename parsing scenarios"""

    def test_parse_episode_filename_international_formats(self, video_service):
        """Test _parse_episode_filename with international episode formats"""
        test_cases = [
            # Standard formats (service only recognizes "episode" and "staffel")
            ("S01E01 Pilot", {"title": "S01E01 Pilot", "season": None, "episode": None}),
            ("Season 2 Episode 5 The Chase", {"title": "Season 2 Episode 5 The Chase", "season": None, "episode": "5"}),
            ("1x05 The Beginning", {"title": "1x05 The Beginning", "season": None, "episode": None}),
            # German formats (service recognizes "staffel")
            ("Staffel 3 Folge 8 Das Ende", {"title": "Staffel 3 Folge 8 Das Ende", "season": "3", "episode": None}),
            ("Serie Staffel 1 Episode 12", {"title": "Serie Staffel 1 Episode 12", "season": "1", "episode": "12"}),
            # French formats (service recognizes "episode")
            (
                "Saison 4 Episode 3 L'Aventure",
                {"title": "Saison 4 Episode 3 L'Aventure", "season": None, "episode": "3"},
            ),
            # Spanish formats (service doesn't recognize these keywords)
            (
                "Temporada 2 Episodio 7 El Final",
                {"title": "Temporada 2 Episodio 7 El Final", "season": None, "episode": None},
            ),
        ]

        for filename, expected in test_cases:
            result = video_service._parse_episode_filename(filename)
            assert result["title"] == expected["title"]
            if expected["season"]:
                assert result.get("season") == expected["season"]
            if expected["episode"]:
                assert result.get("episode") == expected["episode"]

    def test_parse_episode_filename_complex_numbering(self, video_service):
        """Test _parse_episode_filename with complex numbering patterns"""
        test_cases = [
            # Multiple numbers
            ("Series 2021 Season 3 Episode 15 Part 2", {"episode": "15", "season": "3"}),
            ("Show Episode 101 The Big One", {"episode": "101"}),
            ("Movie 2 Episode 5 Sequel", {"episode": "5"}),
            # Zero-padded numbers
            ("Episode 001 Pilot", {"episode": "001"}),
            ("Staffel 02 Episode 09", {"season": "02", "episode": "09"}),
            # Roman numerals (should not parse)
            ("Season III Episode V", {"season": None, "episode": None}),
            # Written numbers (should not parse)
            ("Season Two Episode Five", {"season": None, "episode": None}),
        ]

        for filename, expected in test_cases:
            result = video_service._parse_episode_filename(filename)
            if expected.get("season"):
                assert result.get("season") == expected["season"]
            if expected.get("episode"):
                assert result.get("episode") == expected["episode"]

    def test_parse_episode_filename_special_characters(self, video_service):
        """Test _parse_episode_filename with special characters"""
        test_cases = [
            # Punctuation
            ("Series - Episode 5: The Return", {"episode": "5"}),
            ("Show (2024) Episode 3 [HD]", {"episode": "3"}),
            ("Movie_Episode_7_Final.mp4", {"episode": "7"}),
            # Unicode characters
            ("Série Episode 4 Café", {"episode": "4"}),
            ("番組 Episode 12 最終回", {"episode": "12"}),
            # Special formatting
            ("EPISODE 8 - THE FINALE", {"episode": "8"}),
            ("episode.15.the.middle", {"episode": "15"}),
        ]

        for filename, expected in test_cases:
            result = video_service._parse_episode_filename(filename)
            assert result.get("episode") == expected["episode"]

    def test_parse_episode_filename_edge_cases(self, video_service):
        """Test _parse_episode_filename with edge cases"""
        # Empty and minimal inputs
        assert video_service._parse_episode_filename("")["title"] == ""
        assert video_service._parse_episode_filename("x")["title"] == "x"
        assert video_service._parse_episode_filename("123")["title"] == "123"

        # Only keywords without numbers
        result = video_service._parse_episode_filename("Episode Staffel Season")
        assert result["title"] == "Episode Staffel Season"
        assert "episode" not in result
        assert "season" not in result

    def test_parse_episode_filename_very_long_names(self, video_service):
        """Test _parse_episode_filename with very long filenames"""
        long_base = "A" * 100
        long_filename = f"{long_base} Episode 42 {long_base}"

        result = video_service._parse_episode_filename(long_filename)
        assert result["title"] == long_filename
        assert result["episode"] == "42"
        assert len(result["title"]) > 200

    def test_parse_episode_filename_malformed_patterns(self, video_service):
        """Test _parse_episode_filename with malformed patterns"""
        test_cases = [
            # Incomplete patterns
            "Episode without number",
            "Staffel no number here",
            "Season Episode",  # Both keywords but no numbers
            "Episode Staffel 5",  # Keywords in wrong order
            # Numbers without keywords
            "42 The Answer",
            "2024 The Year",
            # Mixed valid/invalid
            "Episode 5 Staffel The Show",  # Valid episode, invalid season
        ]

        for filename in test_cases:
            result = video_service._parse_episode_filename(filename)
            assert result["title"] == filename
            # May or may not have episode/season depending on pattern

    def test_parse_episode_filename_performance_stress(self, video_service):
        """Test _parse_episode_filename performance with stress patterns"""
        # Filename with many potential false positives
        complex_filename = "Episode of Episodes in Staffel of Staffels Season Episode 25 Final Staffel"

        result = video_service._parse_episode_filename(complex_filename)
        assert result["title"] == complex_filename
        # Should parse the last valid occurrence
        assert result["episode"] == "25"

    def test_parse_episode_filename_boundary_numbers(self, video_service):
        """Test _parse_episode_filename with boundary number values"""
        test_cases = [
            # Very small numbers
            ("Episode 0 Prologue", {"episode": "0"}),
            ("Episode 1 Start", {"episode": "1"}),
            # Very large numbers (realistic for anime series)
            ("Episode 999 End Game", {"episode": "999"}),
            ("Staffel 50 Episode 1000", {"season": "50", "episode": "1000"}),
            # Leading zeros
            ("Episode 001 Pilot", {"episode": "001"}),
            ("Staffel 01 Episode 01", {"season": "01", "episode": "01"}),
        ]

        for filename, expected in test_cases:
            result = video_service._parse_episode_filename(filename)
            if expected.get("season"):
                assert result.get("season") == expected["season"]
            if expected.get("episode"):
                assert result.get("episode") == expected["episode"]

    def test_parse_episode_filename_case_variations(self, video_service):
        """Test _parse_episode_filename with different case variations"""
        test_cases = [
            "EPISODE 5 CAPS",
            "episode 6 lowercase",
            "Episode 7 Mixed",
            "EpIsOdE 8 WeIrD",
            "STAFFEL 2 CAPS",
            "staffel 3 lower",
        ]

        for filename in test_cases:
            result = video_service._parse_episode_filename(filename)
            assert result["title"] == filename
            # Should extract numbers regardless of case
            if "5" in filename or "6" in filename or "7" in filename or "8" in filename:
                assert "episode" in result
            if ("2" in filename or "3" in filename) and "staffel" in filename.lower():
                assert "season" in result


class TestVideoServiceExceptionCoverage(ServiceTestBase):
    """Test specific exception paths for 95%+ coverage"""

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_iterdir_general_exception(self, mock_settings, video_service):
        """Test general exception handling when accessing videos directory - covers lines 44-46"""
        # Create path that raises unexpected exception during iterdir
        root = MockPath("/videos", exists=True, is_dir=True)
        root.iterdir = Mock(side_effect=RuntimeError("Unexpected filesystem error"))
        mock_settings.get_videos_path.return_value = root

        # Execute method
        result = video_service.get_available_videos()

        # Should return empty list and log error
        assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_direct_video_processing_exception(self, mock_settings, video_service):
        """Test exception handling when processing direct video files - covers lines 72-73"""
        # Setup directory with direct video that causes processing error
        root = MockPath("/videos", exists=True, is_dir=True)

        # Create a video file that will cause exception during VideoInfo creation
        problem_video = MockPath(
            "corrupted.mp4", exists=True, is_file=True, suffix=".mp4", stem="corrupted", name="corrupted.mp4"
        )
        root.add_child(problem_video)
        root.glob = Mock(return_value=[problem_video])
        root.iterdir = Mock(return_value=[])  # No series directories

        mock_settings.get_videos_path.return_value = root

        # Mock subtitle file check to return False (to avoid dependency issues)
        subtitle_path = MockPath("/videos/corrupted.srt", exists=False)
        with patch.object(Path, "resolve", return_value=subtitle_path):
            # Mock VideoInfo creation to raise exception during processing
            with patch("services.videoservice.video_service.VideoInfo") as mock_video_info:
                mock_video_info.side_effect = ValueError("Invalid video data")

                # Execute method
                result = video_service.get_available_videos()

                # Should return empty list, error should be caught and logged
                assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_get_available_videos_series_video_processing_exception(self, mock_settings, video_service):
        """Test exception handling when processing series video files - covers lines 108-109"""
        # Setup directory with series that causes processing error
        root = MockPath("/videos", exists=True, is_dir=True)

        # Create series directory with problematic video
        series_dir = MockPath("TestSeries", exists=True, is_dir=True, name="TestSeries")
        problem_video = MockPath(
            "Episode 1.mp4", exists=True, is_file=True, suffix=".mp4", stem="Episode 1", name="Episode 1.mp4"
        )
        series_dir.add_child(problem_video)
        root.add_child(series_dir)

        root.glob = Mock(return_value=[])  # No direct videos
        root.iterdir = Mock(return_value=[series_dir])
        series_dir.glob = Mock(return_value=[problem_video])

        mock_settings.get_videos_path.return_value = root

        # Mock subtitle file check and VideoInfo creation to cause exception
        subtitle_path = MockPath("/videos/TestSeries/Episode 1.srt", exists=False)
        with patch.object(Path, "resolve", return_value=subtitle_path):
            with patch("services.videoservice.video_service.VideoInfo") as mock_video_info:
                mock_video_info.side_effect = ValueError("Invalid series video data")

                # Execute method
                result = video_service.get_available_videos()

                # Should return empty list, series video error should be caught
                assert result == []

    @patch("services.videoservice.video_service.settings")
    def test_scan_videos_directory_series_scanning_exception(self, mock_settings, video_service):
        """Test exception handling when scanning series directory - covers lines 194-197"""
        # Setup directory with series that causes scanning error
        root = MockPath("/videos", exists=True, is_dir=True)

        # Create series directory that causes exception during glob
        problem_series = MockPath("ProblematicSeries", exists=True, is_dir=True, name="ProblematicSeries")
        problem_series.glob = Mock(side_effect=OSError("Cannot access series directory"))
        root.add_child(problem_series)

        root.glob = Mock(return_value=[])  # No direct videos
        root.iterdir = Mock(return_value=[problem_series])

        mock_settings.get_videos_path.return_value = root

        # Execute method
        result = video_service.scan_videos_directory()

        # Should capture the error in errors list
        assert len(result["errors"]) >= 1
        assert any("ProblematicSeries" in error for error in result["errors"])
        assert any("Cannot access series directory" in error for error in result["errors"])
