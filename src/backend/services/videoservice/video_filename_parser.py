"""
Video filename parser using guessit library

Handles parsing of video filenames to extract:
- Series name
- Season number
- Episode number
- Quality info
- Codec information
"""

from typing import Any

from guessit import guessit

from core.config.logging_config import get_logger

logger = get_logger(__name__)


class VideoFilenameParser:
    """
    Parse video filenames using guessit library.

    Handles various naming conventions:
    - S01E01 format (Breaking.Bad.S01E01.720p)
    - 1x01 format (Lost.1x01.Pilot)
    - Episode N format (The.Office.Episode.1)
    - Many other variations
    """

    @staticmethod
    def parse(filename: str) -> dict[str, Any]:
        """
        Parse video filename and extract metadata.

        Args:
            filename: Video filename (with or without extension)

        Returns:
            Dictionary with extracted metadata:
            {
                'title': str,
                'series': str,
                'season': int,
                'episode': int,
                'quality': str,
                'codec': str,
                'raw': dict (all guessit results)
            }
        """
        # Remove extension if present
        if filename.endswith((".mp4", ".mkv", ".avi", ".mov", ".m4v")):
            filename_clean = filename.rsplit(".", 1)[0]
        else:
            filename_clean = filename

        # Use guessit to parse
        try:
            result = guessit(filename_clean)

            return {
                "title": result.get("title", ""),
                "series": result.get("series", result.get("title", "")),
                "season": result.get("season"),
                "episode": result.get("episode"),
                "quality": result.get("screen_size"),  # e.g., '720p', '1080p'
                "codec": result.get("video_codec"),
                "audio_codec": result.get("audio_codec"),
                "format": result.get("source"),  # e.g., 'Web-DL', 'HDTV'
                "raw": dict(result),
            }
        except Exception as e:
            logger.error("Error parsing filename", filename=filename, error=str(e))
            return {
                "title": filename,
                "series": filename,
                "season": None,
                "episode": None,
                "quality": None,
                "codec": None,
                "audio_codec": None,
                "format": None,
                "raw": {},
            }

    @staticmethod
    def get_episode_number(filename: str) -> int | None:
        """
        Extract episode number from filename.

        Args:
            filename: Video filename

        Returns:
            Episode number or None
        """
        result = VideoFilenameParser.parse(filename)
        return result.get("episode")

    @staticmethod
    def get_season_number(filename: str) -> int | None:
        """
        Extract season number from filename.

        Args:
            filename: Video filename

        Returns:
            Season number or None
        """
        result = VideoFilenameParser.parse(filename)
        return result.get("season")

    @staticmethod
    def get_series_name(filename: str) -> str:
        """
        Extract series name from filename.

        Args:
            filename: Video filename

        Returns:
            Series name
        """
        result = VideoFilenameParser.parse(filename)
        return result.get("series", "")

    @staticmethod
    def is_valid_video(filename: str) -> bool:
        """
        Check if filename looks like a valid video.

        Args:
            filename: Filename to check

        Returns:
            True if has episode/season info
        """
        result = VideoFilenameParser.parse(filename)
        return result.get("episode") is not None or result.get("season") is not None


# Example usage and testing
if __name__ == "__main__":
    test_filenames = [
        "Breaking.Bad.S01E01.720p.mkv",
        "The.Office.US.2x01.HDTV.x264.avi",
        "Lost.Season.1.Episode.1.Pilot.mkv",
        "game_of_thrones_1x01_winter_is_coming.mp4",
        "friends.s05e07.1080p.web-dl.aac2.0.h.264.mkv",
    ]

    parser = VideoFilenameParser()
    for filename in test_filenames:
        result = parser.parse(filename)
