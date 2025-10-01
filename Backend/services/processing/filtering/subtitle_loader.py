"""
Subtitle loading and parsing service
"""

import re
from pathlib import Path

from services.filterservice.interface import FilteredSubtitle
from utils.srt_parser import SRTParser


class SubtitleLoaderService:
    """Handles subtitle loading, parsing, and word extraction"""

    async def load_and_parse(self, srt_path: str) -> list[FilteredSubtitle]:
        """
        Load and parse SRT file into FilteredSubtitle objects

        Args:
            srt_path: Path to SRT file

        Returns:
            List of FilteredSubtitle objects

        Raises:
            FileNotFoundError: If SRT file doesn't exist
            ValueError: If no subtitle segments found
        """
        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")

        # Parse SRT file
        segments = SRTParser.parse_file(str(srt_file))
        if not segments:
            raise ValueError("No subtitle segments found")

        # Convert to FilteredSubtitle objects
        subtitles = []
        for segment in segments:
            words = self.extract_words_from_text(segment.text, segment.start_time, segment.end_time)

            subtitle = FilteredSubtitle(
                original_text=segment.text, start_time=segment.start_time, end_time=segment.end_time, words=words
            )
            subtitles.append(subtitle)

        return subtitles

    def extract_words_from_text(self, text: str, start_time: float, end_time: float) -> list[dict]:
        """
        Extract words from subtitle text with timing

        Args:
            text: Subtitle text
            start_time: Subtitle start time
            end_time: Subtitle end time

        Returns:
            List of word dictionaries with text and timing
        """
        # Extract words using regex pattern
        word_pattern = re.compile(r"\b\w+\b")
        words = word_pattern.findall(text.lower())

        # Distribute timing evenly among words
        duration = end_time - start_time
        word_duration = duration / max(len(words), 1)

        word_objects = []
        for i, word in enumerate(words):
            word_start = start_time + (i * word_duration)
            word_end = word_start + word_duration
            word_objects.append({"text": word, "start_time": word_start, "end_time": word_end})

        return word_objects

    def estimate_duration(self, srt_path: str) -> int:
        """
        Estimate filtering duration in seconds

        Args:
            srt_path: Path to SRT file

        Returns:
            Estimated duration in seconds
        """
        try:
            segments = SRTParser.parse_file(srt_path)
            # Estimate: 0.5 seconds per segment
            return max(20, len(segments) // 2)
        except:
            return 30  # Default estimate


# Global instance
subtitle_loader_service = SubtitleLoaderService()


def get_subtitle_loader_service() -> SubtitleLoaderService:
    """Get the global subtitle loader service instance"""
    return subtitle_loader_service
