"""
Filtering coordination service
"""

import logging
from typing import Any

from api.models.processing import VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle

from .result_processor import result_processor_service
from .subtitle_loader import subtitle_loader_service
from .vocabulary_builder import vocabulary_builder_service

logger = logging.getLogger(__name__)


class FilteringCoordinatorService:
    """Coordinates filtering operations across sub-services"""

    def __init__(self, subtitle_processor: DirectSubtitleProcessor = None):
        self.subtitle_processor = subtitle_processor or DirectSubtitleProcessor()
        self.loader = subtitle_loader_service
        self.vocab_builder = vocabulary_builder_service
        self.result_processor = result_processor_service

    async def extract_blocking_words(
        self, srt_path: str, user_id: str, user_level: str = "A1", target_language: str = "de"
    ) -> list[VocabularyWord]:
        """
        Extract blocking vocabulary words from subtitles

        Args:
            srt_path: Path to SRT file
            user_id: User ID
            user_level: User's language level
            target_language: Target language

        Returns:
            List of vocabulary words that block comprehension
        """
        # Load and parse subtitles
        subtitles = await self.loader.load_and_parse(srt_path)

        # Apply filtering
        filtering_result = await self.subtitle_processor.process_subtitles(
            subtitles, user_id=str(user_id), user_level=user_level, language=target_language
        )

        # Build vocabulary words
        return await self.vocab_builder.build_vocabulary_words(
            filtering_result.blocker_words, target_language, return_dict=False
        )

    async def refilter_for_translations(
        self, srt_path: str, user_id: str, known_words: list[str], user_level: str = "A1", target_language: str = "de"
    ) -> dict[str, Any]:
        """
        Second-pass filtering to determine which subtitles still need translations
        after vocabulary words have been marked as known

        Args:
            srt_path: Path to SRT file
            user_id: User ID
            known_words: List of words now marked as known
            user_level: User's language level
            target_language: Target language

        Returns:
            Dictionary with subtitle indices that still need translations
        """
        logger.info(f"Refiltering subtitles for user {user_id} with {len(known_words)} known words")

        # Load and parse subtitles
        subtitles = await self.loader.load_and_parse(srt_path)

        # Get initial filtering result to identify blockers
        filtering_result = await self.subtitle_processor.process_subtitles(
            subtitles, user_id=str(user_id), user_level=user_level, language=target_language
        )

        # Create a set of known words for fast lookup
        known_words_set = {word.lower() for word in known_words}

        # Determine which subtitle indices still need translations
        needs_translation = self._find_subtitles_needing_translation(
            subtitles, filtering_result.blocker_words, known_words_set
        )

        # Build result
        result = {
            "total_subtitles": len(subtitles),
            "needs_translation": needs_translation,
            "translation_count": len(needs_translation),
            "known_words_applied": list(known_words),
            "filtering_stats": {
                "total_blockers": len(filtering_result.blocker_words),
                "known_blockers": len([w for w in filtering_result.blocker_words if w.text.lower() in known_words_set]),
                "unknown_blockers": len(
                    [w for w in filtering_result.blocker_words if w.text.lower() not in known_words_set]
                ),
            },
        }

        logger.info(
            f"Refiltering complete: {result['translation_count']}/{result['total_subtitles']} "
            f"subtitles still need translation"
        )

        return result

    def _find_subtitles_needing_translation(
        self, subtitles: list[FilteredSubtitle], blocker_words: list, known_words_set: set
    ) -> list[int]:
        """
        Find subtitle indices that still need translation

        Args:
            subtitles: List of parsed subtitles
            blocker_words: List of identified blocker words
            known_words_set: Set of known words (lowercase)

        Returns:
            List of subtitle indices needing translation
        """
        needs_translation = []

        for idx, subtitle in enumerate(subtitles):
            # Extract words from subtitle text
            subtitle_words = self.loader.extract_words_from_text(
                subtitle.original_text, subtitle.start_time, subtitle.end_time
            )

            # Check if this subtitle has unknown blockers
            has_unknown_blockers = False
            for word_obj in subtitle_words:
                word_text = word_obj["text"].lower()

                # Check if this word is a blocker
                is_blocker = any(blocker.text.lower() == word_text for blocker in blocker_words)

                # If it's a blocker and NOT known, subtitle needs translation
                if is_blocker and word_text not in known_words_set:
                    has_unknown_blockers = True
                    break

            if has_unknown_blockers:
                needs_translation.append(idx)

        return needs_translation


# Global instance
filtering_coordinator_service = FilteringCoordinatorService()


def get_filtering_coordinator_service() -> FilteringCoordinatorService:
    """Get the global filtering coordinator service instance"""
    return filtering_coordinator_service
