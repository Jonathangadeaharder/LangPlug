"""
Translation Management Service
Handles selective translation analysis and segment building
"""

from typing import Any

from core.config.logging_config import get_logger
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.vocabulary import (
    get_vocabulary_progress_service,
    get_vocabulary_query_service,
    get_vocabulary_service,
    get_vocabulary_stats_service,
)

logger = get_logger(__name__)


class TranslationManagementService:
    """Service for managing selective translations based on known words"""

    def __init__(self):
        # Initialize vocabulary service for DirectSubtitleProcessor
        query_service = get_vocabulary_query_service()
        progress_service = get_vocabulary_progress_service()
        stats_service = get_vocabulary_stats_service()
        vocab_service = get_vocabulary_service(query_service, progress_service, stats_service)

        self.subtitle_processor = DirectSubtitleProcessor(vocab_service=vocab_service)

    async def apply_selective_translations(
        self,
        srt_path: str,
        known_words: list[str],
        target_language: str,
        user_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Apply selective translations based on known words

        Args:
            srt_path: Path to SRT file
            known_words: List of words user already knows
            target_language: Target language code
            user_level: User's language level
            user_id: User identifier

        Returns:
            Translation analysis results
        """
        logger.debug("Applying selective translations", known_word_count=len(known_words))

        # Re-filter the subtitles excluding known words
        refilter_result = await self.refilter_for_translations(
            srt_path, user_id, known_words, user_level, target_language
        )

        # Build translation segments for remaining unknown words
        translation_segments = await self.build_translation_segments(
            srt_path, user_id, known_words, user_level, target_language, refilter_result
        )

        logger.debug("Generated translation segments", count=len(translation_segments))

        return self.create_translation_response(refilter_result, translation_segments, known_words)

    async def refilter_for_translations(
        self, srt_path: str, user_id: str, known_words: list[str], user_level: str, target_language: str
    ) -> dict[str, Any]:
        """
        Re-filter subtitles excluding known words

        Args:
            srt_path: Path to SRT file
            user_id: User identifier
            known_words: List of known words
            user_level: User's language level
            target_language: Target language code

        Returns:
            Re-filtering result dictionary
        """
        # Use DirectSubtitleProcessor directly - no need for wrapper layer
        result = await self.subtitle_processor.process_srt_file(srt_path, user_id, user_level, target_language)

        # Filter out known words from blocking words
        blocking_words = result.get("blocking_words", [])
        known_words_lower = {w.lower() for w in known_words}

        unknown_blockers = [word for word in blocking_words if word.get("word", "").lower() not in known_words_lower]
        known_blockers = [word for word in blocking_words if word.get("word", "").lower() in known_words_lower]

        return {
            "total_subtitles": len(result.get("learning_subtitles", [])),
            "original_blockers": len(blocking_words),
            "unknown_blockers": len(unknown_blockers),
            "known_blockers": len(known_blockers),
            "filtering_stats": {
                "total_blockers": len(blocking_words),
                "known_blockers": len(known_blockers),
                "unknown_blockers": len(unknown_blockers),
                "translation_reduction": round((len(known_blockers) / len(blocking_words)) * 100, 1)
                if blocking_words
                else 0,
            },
        }

    async def build_translation_segments(
        self,
        srt_path: str,
        user_id: str,
        known_words: list[str],
        user_level: str,
        target_language: str,
        refilter_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Build translation segments for unknown words

        Args:
            srt_path: Path to SRT file
            user_id: User identifier
            known_words: List of known words
            user_level: User's language level
            target_language: Target language code
            refilter_result: Result from re-filtering

        Returns:
            List of translation segment dictionaries
        """
        translation_segments = []

        # Only build segments if there are unknown blockers
        if refilter_result.get("unknown_blockers", 0) > 0:
            # Get detailed filtering result
            detailed_result = await self.subtitle_processor.process_srt_file(
                srt_path, user_id, user_level, target_language
            )

            if detailed_result and detailed_result.get("filtered_subtitles"):
                # Filter out known words
                unknown_word_set = self.filter_unknown_words(detailed_result.get("blocking_words", []), known_words)

                # Build segments that need translation
                translation_segments = self.create_translation_segments(
                    detailed_result.get("filtered_subtitles", []), unknown_word_set
                )

        return translation_segments

    def filter_unknown_words(self, blocker_words: list[Any], known_words: list[str]) -> set[str]:
        """
        Filter out known words from blocker words

        Args:
            blocker_words: List of blocker word objects
            known_words: List of known words

        Returns:
            Set of unknown words (lowercase)
        """
        unknown_word_set = set()
        known_words_lower = {w.lower() for w in known_words}

        for blocker in blocker_words:
            if hasattr(blocker, "word"):
                word = blocker.word.lower()
                if word not in known_words_lower:
                    unknown_word_set.add(word)

        return unknown_word_set

    def create_translation_segments(
        self, filtered_subtitles: list[Any], unknown_word_set: set[str]
    ) -> list[dict[str, Any]]:
        """
        Create translation segments from filtered subtitles

        Args:
            filtered_subtitles: List of filtered subtitle objects
            unknown_word_set: Set of unknown words

        Returns:
            List of translation segment dictionaries
        """
        translation_segments = []

        for subtitle in filtered_subtitles:
            if hasattr(subtitle, "filtered_words") and subtitle.filtered_words:
                # Find unknown words in this subtitle
                subtitle_unknown_words = [
                    fw for fw in subtitle.filtered_words if hasattr(fw, "word") and fw.word.lower() in unknown_word_set
                ]

                if subtitle_unknown_words:
                    # This subtitle contains unknown words
                    segment = self.create_translation_segment(subtitle, subtitle_unknown_words)
                    translation_segments.append(segment)

        return translation_segments

    def create_translation_segment(self, subtitle: Any, unknown_words: list[Any]) -> dict[str, Any]:
        """
        Create a single translation segment dictionary

        Args:
            subtitle: Subtitle object
            unknown_words: List of unknown word objects

        Returns:
            Translation segment dictionary
        """
        return {
            "subtitle_index": getattr(subtitle, "index", 0),
            "text": getattr(subtitle, "text", ""),
            "start_time": getattr(subtitle, "start_time", ""),
            "end_time": getattr(subtitle, "end_time", ""),
            "unknown_words": [
                {
                    "word": fw.word,
                    "difficulty": getattr(fw, "difficulty", "unknown"),
                    "pos": getattr(fw, "pos", "unknown"),
                }
                for fw in unknown_words
            ],
        }

    def create_translation_response(
        self, refilter_result: dict[str, Any], translation_segments: list[dict[str, Any]], known_words: list[str]
    ) -> dict[str, Any]:
        """
        Create final translation response dictionary

        Args:
            refilter_result: Result from re-filtering
            translation_segments: List of translation segments
            known_words: List of known words

        Returns:
            Translation response dictionary
        """
        return {
            "total_subtitles": refilter_result.get("total_subtitles", 0),
            "translation_count": len(translation_segments),
            "needs_translation": translation_segments,
            "filtering_stats": {
                "total_blockers": refilter_result.get("original_blockers", 0),
                "known_blockers": len(known_words),
                "unknown_blockers": refilter_result.get("unknown_blockers", 0),
                "translation_reduction": refilter_result.get("filtering_stats", {}).get("translation_reduction", 0),
            },
        }

    def create_fallback_response(self, known_words: list[str], error: Exception) -> dict[str, Any]:
        """
        Create fallback response when translation fails

        Args:
            known_words: List of known words
            error: Exception that occurred

        Returns:
            Fallback response dictionary
        """
        return {
            "total_subtitles": 0,
            "translation_count": 0,
            "needs_translation": [],
            "filtering_stats": {
                "total_blockers": 0,
                "known_blockers": len(known_words),
                "unknown_blockers": 0,
                "translation_reduction": 0,
            },
            "error": str(error),
        }


def get_translation_management_service() -> TranslationManagementService:
    """Returns fresh instance to avoid global state"""
    return TranslationManagementService()
