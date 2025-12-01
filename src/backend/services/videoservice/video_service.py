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
    - Video file lookup cached with 60s TTL to optimize repeated lookups

Filename Parsing Patterns:
    - Episode: "episode 1", "ep1", "e1", "episode_01"
    - Season: "season 1", "s1", "staffel 1"
    - Case-insensitive matching
"""

import time
from pathlib import Path
from typing import Any, ClassVar

from fastapi import UploadFile

from api.models.video import VideoInfo
from api.models.vocabulary import VocabularyWord
from core.config import settings
from core.config.logging_config import get_logger
from core.config.media_config import VIDEO_EXTENSIONS
from core.exceptions import EpisodeNotFoundError, SeriesNotFoundError
from core.file_security import FileSecurityValidator

logger = get_logger(__name__)


class VideoService:
    """
    Service for video library management and metadata extraction.
    """

    # Class-level cache for video file lookups (shared across instances)
    _video_cache: ClassVar[dict[str, tuple[dict[str, Path], float]]] = {}
    _scan_cache: ClassVar[tuple[list, float] | None] = None  # Cache for get_available_videos
    _cache_ttl: ClassVar[int] = 60  # Cache TTL in seconds

    def __init__(self, db_manager, auth_service):
        self.db = db_manager
        self.auth_service = auth_service

    @classmethod
    def _get_series_video_index(cls, series_path: Path) -> dict[str, Path]:
        """Get or create a cached index of videos in a series directory.
        
        Returns a dict mapping normalized episode names to file paths.
        Uses class-level caching with TTL to avoid repeated directory scans.
        """
        cache_key = str(series_path)
        now = time.time()
        
        # Check if we have a valid cached entry
        if cache_key in cls._video_cache:
            cached_index, cached_time = cls._video_cache[cache_key]
            if now - cached_time < cls._cache_ttl:
                return cached_index
        
        # Build index of video files
        video_index: dict[str, Path] = {}
        if series_path.exists():
            for video_file in series_path.glob("*.mp4"):
                filename_lower = video_file.name.lower()
                # Index by multiple keys for flexible lookup
                video_index[filename_lower] = video_file
                video_index[video_file.stem.lower()] = video_file
        
        cls._video_cache[cache_key] = (video_index, now)
        return video_index

    @classmethod
    def clear_cache(cls, series_path: Path | None = None) -> None:
        """Clear the video cache. If series_path provided, only clear that entry."""
        if series_path:
            cls._video_cache.pop(str(series_path), None)
        else:
            cls._video_cache.clear()
            cls._scan_cache = None

    def validate_series_name(self, series: str) -> str:
        """Validate and sanitize series name to prevent path traversal"""
        safe_series = FileSecurityValidator.sanitize_filename(series)
        if safe_series != series or ".." in series or "/" in series or "\\" in series:
            raise ValueError("Invalid series name")
        return safe_series

    async def validate_video_file_upload(self, video_file: UploadFile) -> Path:
        """Validate uploaded video file for security"""
        return await FileSecurityValidator.validate_file_upload(video_file, set(VIDEO_EXTENSIONS))

    async def write_video_file(self, video_file: UploadFile, destination: Path) -> None:
        """Write uploaded video file in chunks for memory efficiency"""
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks

        with open(destination, "wb") as buffer:
            while True:
                chunk = await video_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer.write(chunk)

    async def upload_video(self, series: str, video_file: UploadFile) -> VideoInfo:
        """Upload a new video file to a series"""
        safe_series = self.validate_series_name(series)
        safe_path = await self.validate_video_file_upload(video_file)

        series_path = settings.get_videos_path() / safe_series
        series_path.mkdir(parents=True, exist_ok=True)

        final_path = FileSecurityValidator.get_safe_upload_path(video_file.filename, preserve_name=True)
        final_destination = series_path / final_path.name

        if final_destination.exists():
            raise FileExistsError(f"File already exists: {final_destination.name}")

        await self.write_video_file(video_file, final_destination)

        if safe_path.exists() and safe_path != final_destination:
            safe_path.unlink(missing_ok=True)

        logger.info("Uploaded video", path=str(final_destination))

        # Build VideoInfo response
        episode_info = self._parse_episode_filename(final_destination.stem)
        return VideoInfo(
            series=safe_series,
            season=episode_info.get("season", "1"),
            episode=episode_info.get("episode", "Unknown"),
            title=episode_info.get("title", final_destination.stem),
            path=str(final_destination.relative_to(settings.get_videos_path())),
            has_subtitles=False,
            duration=0,
        )

    async def upload_subtitle(self, video_path: str, subtitle_file: UploadFile) -> Path:
        """
        Upload a subtitle file for a video.

        Args:
            video_path: Relative path to the video file
            subtitle_file: Uploaded subtitle file object

        Returns:
            Path to the saved subtitle file

        Raises:
            ValueError: If file type or path is invalid
            FileNotFoundError: If video file does not exist
        """
        # Validate file extension
        allowed_extensions = {".srt", ".vtt", ".sub"}
        await FileSecurityValidator.validate_file_upload(subtitle_file, allowed_extensions)

        # Resolve video path
        videos_path = settings.get_videos_path()
        try:
            video_full_path = videos_path / video_path
            # Validate path security
            FileSecurityValidator.validate_file_path(str(video_full_path))
        except ValueError as e:
            raise ValueError(f"Invalid video path: {e}") from e

        if not video_full_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Determine subtitle path (same name as video, but .srt)
        subtitle_path = video_full_path.with_suffix(".srt")

        # Write file content
        content = await subtitle_file.read()
        with open(subtitle_path, "wb") as buffer:
            buffer.write(content)

        logger.info("Subtitle uploaded", path=str(subtitle_path))
        return subtitle_path

    def get_video_status(self, video_id: str, task_progress: dict[str, Any]) -> dict[str, Any]:
        """Get processing status for a video"""
        # Logic moved from routes
        video_tasks = [
            (task_id, progress)
            for task_id, progress in task_progress.items()
            if video_id in task_id or video_id in str(progress.get("video_path", ""))
        ]

        if not video_tasks:
            videos_path = settings.get_videos_path()
            video_path = videos_path / video_id

            if not video_path.exists():
                return None  # Not found

            srt_path = video_path.with_suffix(".srt")
            if srt_path.exists():
                return {
                    "status": "completed",
                    "progress": 100.0,
                    "current_step": "Processing completed",
                    "message": "Video has been fully processed",
                    "subtitle_path": str(srt_path.relative_to(videos_path)),
                }
            else:
                return {
                    "status": "completed",
                    "progress": 0.0,
                    "current_step": "Not processed",
                    "message": "Video has not been processed yet",
                }

        _latest_task_id, latest_progress = video_tasks[-1]
        return latest_progress

    def get_video_vocabulary(self, video_id: str) -> list[VocabularyWord]:
        """Get vocabulary words extracted from a video's subtitles.
        
        Note: This endpoint returns vocabulary that was extracted during
        video processing. If no vocabulary exists, an empty list is returned.
        Full vocabulary extraction happens during chunk processing via
        ChunkTranscriptionService.
        
        Args:
            video_id: Video identifier (path relative to videos directory)
            
        Returns:
            List of VocabularyWord objects extracted from video subtitles
            
        Raises:
            FileNotFoundError: If video or subtitle file not found
        """
        videos_path = settings.get_videos_path()
        video_path = videos_path / video_id

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_id}")

        srt_path = video_path.with_suffix(".srt")
        if not srt_path.exists():
            # No subtitles = no vocabulary to extract
            logger.debug("No subtitles found for video", video_id=video_id)
            return []

        # Vocabulary is extracted during chunk processing and stored in the database.
        # This method returns empty until database integration is complete.
        # See: services/processing/chunk_transcription_service.py for extraction logic
        logger.debug("Vocabulary lookup for video", video_id=video_id)
        return []

    def _validate_videos_path(self, videos_path: Path) -> bool:
        """Validate videos path exists and is accessible"""
        if not videos_path.exists():
            logger.error("Videos path does not exist", path=str(videos_path))
            return False

        if not videos_path.is_dir():
            logger.error("Videos path not a directory", path=str(videos_path))
            return False

        try:
            list(videos_path.iterdir())
            return True
        except PermissionError:
            logger.error("Permission denied accessing videos", path=str(videos_path))
            return False
        except Exception as e:
            logger.error("Error accessing videos directory", path=str(videos_path), error=str(e))
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
            logger.error("Error creating VideoInfo", file=str(video_file), error=str(e))
            return None

    def _scan_direct_videos(self, videos_path: Path) -> list[VideoInfo]:
        """Scan for video files directly in videos_path root"""
        videos = []
        direct_videos = list(videos_path.glob("*.mp4"))
        logger.debug("Found direct video files", count=len(direct_videos))

        for video_file in direct_videos:
            video_info = self._create_video_info(video_file, videos_path, "Default")
            if video_info:
                videos.append(video_info)
                logger.debug("Added direct video", title=video_info.title)

        return videos

    def _scan_series_directories(self, videos_path: Path) -> list[VideoInfo]:
        """Scan for video files in series directories"""
        videos = []
        series_dirs = [d for d in videos_path.iterdir() if d.is_dir()]
        logger.debug("Found series directories", count=len(series_dirs))

        for series_dir in series_dirs:
            try:
                series_name = series_dir.name
                logger.debug("Scanning series directory", series=series_name)

                series_videos = list(series_dir.glob("*.mp4"))
                logger.debug("Found videos in series", count=len(series_videos), series=series_name)

                for video_file in series_videos:
                    video_info = self._create_video_info(video_file, videos_path, series_name)
                    if video_info:
                        videos.append(video_info)
                        logger.debug("Added series video", title=video_info.title, series=series_name)
            except Exception as e:
                logger.error("Error processing series directory", dir=str(series_dir), error=str(e))

        return videos

    def get_available_videos(self) -> list[VideoInfo]:
        """Get list of available videos/series (Refactored for lower complexity)
        
        Uses class-level caching with TTL to reduce disk I/O.
        """
        # Check cache first
        now = time.time()
        if VideoService._scan_cache is not None:
            cached_videos, cached_time = VideoService._scan_cache
            if now - cached_time < self._cache_ttl:
                logger.debug("Returning cached video list", count=len(cached_videos))
                return cached_videos
        
        try:
            videos_path = settings.get_videos_path()
            logger.debug("Scanning for videos", path=str(videos_path))

            if not self._validate_videos_path(videos_path):
                return []

            videos = []
            videos.extend(self._scan_direct_videos(videos_path))
            videos.extend(self._scan_series_directories(videos_path))

            # Cache the results
            VideoService._scan_cache = (videos, now)
            
            logger.info("Videos scan complete", count=len(videos))
            if len(videos) == 0:
                logger.warning("No videos were found! Check directory structure and file permissions.")
                logger.info("Expected structure: videos/[SeriesName]/episode.mp4 or videos/episode.mp4")

            return videos

        except Exception as e:
            logger.error("Error scanning videos", error=str(e), exc_info=True)
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

    def _parse_episode_filename(self, filename: str) -> dict[str, str | None]:
        """Parse episode information from filename using regex patterns (Refactored for lower complexity)"""
        episode_info: dict[str, str | None] = {"title": filename}

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
            logger.debug("Found direct videos", count=len(direct_videos))
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
                    logger.debug("Found videos in series", count=len(series_videos), series=item.name)
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

            logger.debug("Scanning videos directory", path=str(videos_path))

            if not self._validate_videos_directory(videos_path, result):
                return result

            self._scan_direct_video_files(videos_path, result)
            self._scan_series_directory_videos(videos_path, result)

            logger.info("Video scan complete", total=result["total_videos"])
            return result

        except Exception as e:
            logger.error("Fatal error during video scan", error=str(e), exc_info=True)
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
                logger.debug("Converted absolute path to relative")
            except (StopIteration, IndexError):
                logger.warning("Could not find videos directory in path")
                subtitle_file = videos_root / Path(subtitle_path).name
        else:
            # Regular relative path handling
            subtitle_file = videos_root / subtitle_path

        return subtitle_file

    def get_video_file_path(self, series: str, episode: str) -> Path:
        """Get video file path for a series and episode.

        Args:
            series: Name of the video series/folder
            episode: Episode identifier (number or name)

        Returns:
            Path to the video file

        Raises:
            SeriesNotFoundError: If series directory doesn't exist
            EpisodeNotFoundError: If episode not found in series
        """
        videos_path = settings.get_videos_path() / series
        if not videos_path.exists():
            raise SeriesNotFoundError(series)

        # Optimization: Try direct file match first (O(1))
        potential_paths = [
            videos_path / episode,
            videos_path / f"{episode}.mp4",
        ]
        for p in potential_paths:
            if p.exists() and p.is_file() and p.suffix.lower() == ".mp4":
                return p

        # Use cached index for flexible matching (O(1) lookup after initial scan)
        video_index = self._get_series_video_index(videos_path)
        episode_lower = episode.lower()

        # Try direct index lookups first
        if episode_lower in video_index:
            return video_index[episode_lower]
        if f"{episode_lower}.mp4" in video_index:
            return video_index[f"{episode_lower}.mp4"]

        # Search through index with pattern matching
        for key, video_file in video_index.items():
            matches = (
                f"episode {episode_lower}" in key  # "episode 1"
                or f"episode_{episode_lower}" in key  # "episode_1"
                or f"e{episode_lower}" in key  # "e1"
                or episode_lower in key  # direct match
            )
            if matches:
                return video_file

        raise EpisodeNotFoundError(episode, series)
