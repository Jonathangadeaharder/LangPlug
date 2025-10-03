"""
Video Service

Video file management and metadata extraction for LangPlug video library.
This module handles video discovery, series organization, and subtitle file management.

Key Components:
    - VideoService: Main service for video operations
    - Video scanning and discovery (direct files and series directories)
    - Episode metadata parsing from filenames
    - Subtitle file detection and path resolution

Video Organization:
    Supports two structures:
    1. Direct videos: /videos/video.mp4
    2. Series structure: /videos/SeriesName/episode.mp4

    Subtitle files: Automatically detected as video_name.srt

Usage Example:
    ```python
    from services.videoservice.video_service import VideoService

    service = VideoService(db_manager, auth_service)

    # Get all available videos
    videos = service.get_available_videos()
    # Returns: [VideoInfo(series="SeriesName", episode="1", ...)]

    # Scan directory structure
    scan_result = service.scan_videos_directory()
    # Returns: {"direct_videos": [...], "series_directories": [...], ...}

    # Get subtitle file path
    subtitle_path = service.get_subtitle_file_path("SeriesName/episode.srt")

    # Get video file path
    video_path = service.get_video_file_path("SeriesName", "Episode 1")
    ```

Dependencies:
    - pathlib: Path manipulation
    - core.config: Videos directory configuration
    - api.models.video: VideoInfo data model

Thread Safety:
    Yes. Service is stateless, all operations use local variables.

Performance Notes:
    - Video scanning: O(n) where n = total video files
    - Uses glob patterns for efficient file discovery
    - Caches not implemented - rescans on each call

Filename Parsing Patterns:
    - Episode: "episode 1", "ep1", "e1", "episode_01"
    - Season: "season 1", "s1", "staffel 1"
    - Case-insensitive matching
"""

import logging
from pathlib import Path

from api.models.video import VideoInfo
from core.config import settings

logger = logging.getLogger(__name__)


class VideoService:
    """
    Service for video library management and metadata extraction.

    Handles video file discovery, series organization, episode parsing, and subtitle detection.
    Supports both standalone videos and series directory structures.

    Attributes:
        db: Database manager instance
        auth_service: Authentication service instance

    Example:
        ```python
        service = VideoService(db_manager, auth_service)

        # Discover all videos
        videos = service.get_available_videos()
        for video in videos:
            print(f"{video.series} - {video.episode}: {video.title}")
            print(f"  Has subtitles: {video.has_subtitles}")

        # Get video path for playback
        video_file = service.get_video_file_path("Dark", "Episode 1")

        # Resolve subtitle path (handles Windows/WSL paths)
        subtitle_file = service.get_subtitle_file_path("Dark/s01e01.srt")
        ```

    Note:
        Methods are refactored to keep complexity low (<15 lines per method).
        Supports Windows absolute paths and WSL path conversion.
        Episode parsing is case-insensitive and flexible (handles multiple formats).
    """

    def __init__(self, db_manager, auth_service):
        self.db = db_manager
        self.auth_service = auth_service

    def _validate_videos_path(self, videos_path: Path) -> bool:
        """Validate videos path exists and is accessible"""
        if not videos_path.exists():
            logger.error(f"Videos path does not exist: {videos_path}")
            logger.error(f"Attempted absolute path: {videos_path.resolve()}")
            return False

        if not videos_path.is_dir():
            logger.error(f"Videos path exists but is not a directory: {videos_path}")
            return False

        try:
            list(videos_path.iterdir())
            return True
        except PermissionError:
            logger.error(f"Permission denied accessing videos directory: {videos_path}")
            return False
        except Exception as e:
            logger.error(f"Error accessing videos directory {videos_path}: {e}")
            return False

    def _create_video_info(self, video_file: Path, videos_path: Path, series_name: str) -> VideoInfo | None:
        """Create VideoInfo from a video file"""
        try:
            srt_file = video_file.with_suffix(".srt")
            has_subtitles = srt_file.exists()

            filename = video_file.stem
            episode_info = self._parse_episode_filename(filename)

            episode = episode_info.get("episode", filename if series_name == "Default" else "Unknown")
            if len(episode) > 20:
                episode = episode[:17] + "..."

            return VideoInfo(
                series=series_name,
                season=episode_info.get("season", "1"),
                episode=episode,
                title=episode_info.get("title", filename),
                path=str(video_file.relative_to(videos_path)),
                has_subtitles=has_subtitles,
            )
        except Exception as e:
            logger.error(f"Error creating VideoInfo for {video_file}: {e}")
            return None

    def _scan_direct_videos(self, videos_path: Path) -> list[VideoInfo]:
        """Scan for video files directly in videos_path root"""
        videos = []
        direct_videos = list(videos_path.glob("*.mp4"))
        logger.info(f"Found {len(direct_videos)} direct video files in {videos_path}")

        for video_file in direct_videos:
            video_info = self._create_video_info(video_file, videos_path, "Default")
            if video_info:
                videos.append(video_info)
                logger.info(f"Added direct video: {video_info.title}")

        return videos

    def _scan_series_directories(self, videos_path: Path) -> list[VideoInfo]:
        """Scan for video files in series directories"""
        videos = []
        series_dirs = [d for d in videos_path.iterdir() if d.is_dir()]
        logger.info(f"Found {len(series_dirs)} series directories: {[d.name for d in series_dirs]}")

        for series_dir in series_dirs:
            try:
                series_name = series_dir.name
                logger.info(f"Scanning series directory: {series_name}")

                series_videos = list(series_dir.glob("*.mp4"))
                logger.info(f"Found {len(series_videos)} videos in series '{series_name}'")

                for video_file in series_videos:
                    video_info = self._create_video_info(video_file, videos_path, series_name)
                    if video_info:
                        videos.append(video_info)
                        logger.info(f"Added series video: {video_info.title} (series: {series_name})")
            except Exception as e:
                logger.error(f"Error processing series directory {series_dir}: {e}")

        return videos

    def get_available_videos(self) -> list[VideoInfo]:
        """Get list of available videos/series (Refactored for lower complexity)"""
        try:
            videos_path = settings.get_videos_path()
            logger.info(f"Scanning for videos in: {videos_path}")
            logger.info(f"Videos path absolute: {videos_path.resolve()}")

            if not self._validate_videos_path(videos_path):
                return []

            videos = []
            videos.extend(self._scan_direct_videos(videos_path))
            videos.extend(self._scan_series_directories(videos_path))

            logger.info(f"Total videos found: {len(videos)}")
            if len(videos) == 0:
                logger.warning("No videos were found! Check directory structure and file permissions.")
                logger.info("Expected structure: videos/[SeriesName]/episode.mp4 or videos/episode.mp4")

            return videos

        except Exception as e:
            logger.error(f"Error scanning videos: {e!s}", exc_info=True)
            raise Exception(f"Error scanning videos: {e!s}") from e

    def _search_pattern_in_filename(self, patterns: list[str], filename: str) -> str | None:
        """Search for pattern match in filename"""
        import re

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _validate_episode_info(self, episode_info: dict[str, str]) -> None:
        """Validate and clean episode info (remove non-digit values)"""
        if "episode" in episode_info and not episode_info["episode"].isdigit():
            del episode_info["episode"]
        if "season" in episode_info and not episode_info["season"].isdigit():
            del episode_info["season"]

    def _parse_episode_filename(self, filename: str) -> dict[str, str]:
        """Parse episode information from filename using regex patterns (Refactored for lower complexity)"""
        episode_info = {"title": filename}

        if not filename or len(filename.strip()) < 2:
            return episode_info

        # Episode patterns
        episode_patterns = [
            r"episode[\s_\.]*(\d+)",
            r"ep[\s_\.]*(\d+)",
            r"e(\d+)",
        ]

        # Season patterns
        season_patterns = [
            r"season[\s_\.]*(\d+)",
            r"staffel[\s_\.]*(\d+)",
            r"s(\d+)",
        ]

        # Search for episode and season numbers
        episode_num = self._search_pattern_in_filename(episode_patterns, filename)
        if episode_num:
            episode_info["episode"] = episode_num

        season_num = self._search_pattern_in_filename(season_patterns, filename)
        if season_num:
            episode_info["season"] = season_num

        # Validate and clean
        self._validate_episode_info(episode_info)

        return episode_info

    def _initialize_scan_result(self, videos_path: Path) -> dict[str, any]:
        """Initialize scan result dictionary"""
        return {
            "videos_path": str(videos_path),
            "videos_path_absolute": str(videos_path.resolve()),
            "path_exists": videos_path.exists(),
            "is_directory": videos_path.is_dir() if videos_path.exists() else False,
            "direct_videos": [],
            "series_directories": [],
            "total_videos": 0,
            "errors": [],
        }

    def _validate_videos_directory(self, videos_path: Path, result: dict) -> bool:
        """Validate videos directory exists and is accessible"""
        if not videos_path.exists():
            error_msg = f"Videos directory does not exist: {videos_path}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            return False

        if not videos_path.is_dir():
            error_msg = f"Videos path exists but is not a directory: {videos_path}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            return False

        return True

    def _scan_direct_video_files(self, videos_path: Path, result: dict) -> None:
        """Scan for direct video files in videos path"""
        try:
            direct_videos = list(videos_path.glob("*.mp4"))
            result["direct_videos"] = [str(v.name) for v in direct_videos]
            result["total_videos"] += len(direct_videos)
            logger.info(f"Found {len(direct_videos)} direct videos")
        except Exception as e:
            error_msg = f"Error scanning direct videos: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

    def _scan_series_directory_videos(self, videos_path: Path, result: dict) -> None:
        """Scan for videos in series directories"""
        try:
            for item in videos_path.iterdir():
                if not item.is_dir():
                    continue

                series_info = {"name": item.name, "path": str(item), "videos": []}

                try:
                    series_videos = list(item.glob("*.mp4"))
                    series_info["videos"] = [v.name for v in series_videos]
                    result["total_videos"] += len(series_videos)
                    logger.info(f"Found {len(series_videos)} videos in series '{item.name}'")
                except Exception as e:
                    error_msg = f"Error scanning series {item.name}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)

                result["series_directories"].append(series_info)
        except Exception as e:
            error_msg = f"Error scanning series directories: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

    def scan_videos_directory(self) -> dict[str, any]:
        """Scan and return detailed information about the videos directory (Refactored for lower complexity)"""
        try:
            videos_path = settings.get_videos_path()
            result = self._initialize_scan_result(videos_path)

            logger.info(f"Detailed scan of videos directory: {videos_path}")

            if not self._validate_videos_directory(videos_path, result):
                return result

            self._scan_direct_video_files(videos_path, result)
            self._scan_series_directory_videos(videos_path, result)

            logger.info(f"Scan complete. Total videos: {result['total_videos']}")
            return result

        except Exception as e:
            logger.error(f"Fatal error during video scan: {e}", exc_info=True)
            return {
                "error": f"Fatal error during scan: {e}",
                "videos_path": str(settings.get_videos_path()) if settings else "Unknown",
            }

    def get_subtitle_file_path(self, subtitle_path: str) -> Path:
        """Convert subtitle path to actual file path, handling Windows absolute paths"""
        videos_root = settings.get_videos_path()

        if subtitle_path.startswith(("C:", "D:", "/mnt/c/", "/mnt/d/")) or "\\" in subtitle_path:
            # This is an absolute Windows path - convert to relative
            path_obj = Path(subtitle_path.replace("\\", "/"))

            # Find the videos directory in the path and get the relative part
            path_parts = path_obj.parts
            try:
                videos_index = next(i for i, part in enumerate(path_parts) if part.lower() == "videos")
                relative_path = Path(*path_parts[videos_index + 1 :])
                subtitle_file = videos_root / relative_path
                logger.info(f"Converted absolute path {subtitle_path} to relative: {relative_path}")
            except (StopIteration, IndexError):
                logger.warning(f"Could not find 'videos' directory in path: {subtitle_path}")
                subtitle_file = videos_root / Path(subtitle_path).name
        else:
            # Regular relative path handling
            subtitle_file = videos_root / subtitle_path

        return subtitle_file

    def get_video_file_path(self, series: str, episode: str) -> Path:
        """Get video file path for a series and episode"""
        from fastapi import HTTPException

        videos_path = settings.get_videos_path() / series
        if not videos_path.exists():
            raise HTTPException(status_code=404, detail=f"Series '{series}' not found")

        # Find matching video file
        for video_file in videos_path.glob("*.mp4"):
            # More flexible matching - check if episode number is in filename
            # This handles both "1" matching "Episode 1" and full episode names
            filename_lower = video_file.name.lower()
            episode_lower = episode.lower()

            # Try different matching patterns
            matches = (
                f"episode {episode_lower}" in filename_lower  # "episode 1"
                or f"episode_{episode_lower}" in filename_lower  # "episode_1"
                or f"e{episode_lower}" in filename_lower  # "e1"
                or episode_lower in filename_lower  # direct match
            )

            if matches:
                return video_file

        raise HTTPException(status_code=404, detail=f"Episode '{episode}' not found in series '{series}'")
