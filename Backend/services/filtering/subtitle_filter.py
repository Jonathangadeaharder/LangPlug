"""
Subtitle Filter - Core filtering logic for subtitle processing
Extracted from filtering_handler.py for better separation of concerns
"""

import logging
from pathlib import Path
from typing import Any

from services.filterservice.interface import FilteredSubtitle
from services.interfaces.base import IService
from utils.srt_parser import SRTParser

logger = logging.getLogger(__name__)


class SubtitleFilter(IService):
    """Service responsible for core subtitle filtering operations"""

    async def load_and_prepare_subtitles(
        self, srt_path: str, task_progress: dict[str, Any], task_id: str
    ) -> list[FilteredSubtitle]:
        """Load and convert SRT to FilteredSubtitle objects"""
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Loading subtitles..."
        task_progress[task_id].message = "Parsing subtitle file"

        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        try:
            # Parse SRT file
            logger.info(f"Parsing SRT file: {srt_path}")
            parser = SRTParser()
            subtitle_entries = parser.parse_file(str(srt_file))

            if not subtitle_entries:
                logger.warning(f"No subtitle entries found in {srt_path}")
                return []

            # Convert to FilteredSubtitle objects
            filtered_subtitles = []
            for entry in subtitle_entries:
                filtered_subtitle = FilteredSubtitle(
                    original_text=entry.text, start_time=entry.start_time, end_time=entry.end_time, words=[]
                )
                filtered_subtitles.append(filtered_subtitle)

            logger.info(f"Loaded {len(filtered_subtitles)} subtitle entries")
            return filtered_subtitles

        except Exception as e:
            logger.error(f"Error loading subtitles from {srt_path}: {e}")
            raise

    def extract_words_from_text(self, text: str) -> list[str]:
        """Extract individual words from subtitle text"""
        if not text:
            return []

        import re

        # Remove speaker labels and formatting
        clean_text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
        clean_text = re.sub(r"\([^)]*\)", "", clean_text)  # Remove parentheses
        clean_text = re.sub(r"\[[^\]]*\]", "", clean_text)  # Remove brackets
        clean_text = re.sub(r"[^\w\s\'-]", " ", clean_text)  # Keep only word chars, spaces, hyphens, apostrophes

        # Extract words (minimum 2 characters)
        words = []
        for word in clean_text.split():
            word = word.strip().lower()
            # Accept words with letters, hyphens, and apostrophes
            if len(word) >= 2 and re.match(r"^[\w'-]+$", word):
                words.append(word)

        return words

    def estimate_duration(self, srt_path: str) -> int:
        """Estimate processing duration based on file size"""
        try:
            file_size = Path(srt_path).stat().st_size
            # Rough estimate: 1 second per 1KB of SRT file
            estimated_seconds = max(5, file_size // 1024)
            return min(estimated_seconds, 300)  # Cap at 5 minutes
        except Exception:
            return 30  # Default estimate

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the subtitle filter service"""
        return {"service": "SubtitleFilter", "status": "healthy", "srt_parser": "available"}

    async def initialize(self) -> None:
        """Initialize subtitle filter service resources"""
        logger.info("SubtitleFilter initialized")

    async def cleanup(self) -> None:
        """Cleanup subtitle filter service resources"""
        logger.info("SubtitleFilter cleanup completed")
