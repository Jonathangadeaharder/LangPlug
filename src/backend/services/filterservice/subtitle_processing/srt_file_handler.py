"""
SRT File Handler Service
Handles SRT file I/O, parsing, and conversion operations
"""

import re
from typing import Any

from core.config.logging_config import get_logger
from utils.srt_parser import SRTParser

from ..interface import FilteredSubtitle, FilteredWord, FilteringResult, WordStatus

logger = get_logger(__name__)


class SRTFileHandler:
    """Service for handling SRT file operations"""

    def __init__(self):
        self._word_pattern = re.compile(r"\b\w+\b")

    async def parse_srt_file(self, srt_file_path: str) -> list[FilteredSubtitle]:
        """
        Parse an SRT file and convert to FilteredSubtitle objects

        Args:
            srt_file_path: Path to SRT file

        Returns:
            List of FilteredSubtitle objects
        """
        logger.debug("Parsing SRT file", path=srt_file_path)

        # Parse SRT file
        srt_segments = SRTParser.parse_file(srt_file_path)
        logger.debug("Parsed subtitle segments", count=len(srt_segments))

        # Convert to FilteredSubtitle objects
        filtered_subtitles = []
        for segment in srt_segments:
            words = self.extract_words_from_text(segment.text, segment.start_time, segment.end_time)

            filtered_subtitle = FilteredSubtitle(
                original_text=segment.text, start_time=segment.start_time, end_time=segment.end_time, words=words
            )
            filtered_subtitles.append(filtered_subtitle)

        return filtered_subtitles

    def extract_words_from_text(self, text: str, start_time: float, end_time: float) -> list[FilteredWord]:
        """
        Extract words from subtitle text and create FilteredWord objects

        Args:
            text: Subtitle text
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            List of FilteredWord objects
        """
        word_matches = list(self._word_pattern.finditer(text.lower()))
        words = []

        # Estimate timing for each word
        duration = end_time - start_time
        word_duration = duration / max(len(word_matches), 1)

        for i, match in enumerate(word_matches):
            word_text = match.group()
            word_start = start_time + (i * word_duration)
            word_end = word_start + word_duration

            filtered_word = FilteredWord(
                text=word_text,
                start_time=word_start,
                end_time=word_end,
                status=WordStatus.ACTIVE,
                filter_reason=None,
                confidence=None,
                metadata={},
            )
            words.append(filtered_word)

        return words

    def format_processing_result(self, filtering_result: FilteringResult, srt_file_path: str) -> dict[str, Any]:
        """
        Format FilteringResult into expected output format

        Args:
            filtering_result: Result from subtitle processing
            srt_file_path: Original SRT file path

        Returns:
            Dictionary with formatted results
        """
        # Convert blocker words to VocabularyWord format
        from api.models.processing import VocabularyWord

        blocking_words = []
        for word in filtering_result.blocker_words:
            vocab_word = VocabularyWord(
                concept_id=None,
                word=word.text,
                lemma=word.metadata.get("lemma", word.text.lower()),
                translation="",
                difficulty_level=word.metadata.get("difficulty_level", "C2"),
                known=False,
            )
            blocking_words.append(vocab_word)

        return {
            "blocking_words": blocking_words,
            "learning_subtitles": filtering_result.learning_subtitles,
            "empty_subtitles": filtering_result.empty_subtitles,
            "filtered_subtitles": (
                filtering_result.learning_subtitles
                + [
                    FilteredSubtitle(original_text="", start_time=0, end_time=0, words=[w])
                    for w in filtering_result.blocker_words
                ]
                + filtering_result.empty_subtitles
            ),
            "statistics": {**filtering_result.statistics, "file_processed": srt_file_path},
        }


# Singleton instance
srt_file_handler = SRTFileHandler()
