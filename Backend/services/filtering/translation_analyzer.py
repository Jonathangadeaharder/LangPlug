"""
Translation Analyzer - Handles translation needs analysis and re-filtering
Extracted from filtering_handler.py for better separation of concerns
"""

import logging
from typing import Any

from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.interfaces.base import IService

logger = logging.getLogger(__name__)


class TranslationAnalyzer(IService):
    """Service responsible for analyzing translation needs and re-filtering"""

    def __init__(self, subtitle_processor: DirectSubtitleProcessor = None):
        self.subtitle_processor = subtitle_processor or DirectSubtitleProcessor()

    async def refilter_for_translations(
        self, srt_path: str, user_id: str, known_words: list[str], user_level: str, target_language: str
    ) -> dict[str, Any]:
        """
        Re-filter subtitles for translation needs based on known words

        Args:
            srt_path: Path to SRT file
            user_id: User ID
            known_words: List of words user already knows
            user_level: User's language level
            target_language: Target language

        Returns:
            Dictionary containing re-filtering results and translation analysis
        """
        try:
            logger.info(f"Re-filtering for translations: {len(known_words)} known words")

            # Step 1: Get original filtering results
            original_result = await self.subtitle_processor.process_subtitles(
                srt_path, user_id, user_level=user_level, target_language=target_language
            )

            if not original_result or not original_result.blocker_words:
                logger.warning("No original filtering results found")
                return self._create_empty_refilter_result()

            # Step 2: Filter out known words from blockers
            unknown_blockers = []
            known_blockers = []

            for blocker_word in original_result.blocker_words:
                word_text = blocker_word.word.lower()
                if word_text in [kw.lower() for kw in known_words]:
                    known_blockers.append(blocker_word)
                else:
                    unknown_blockers.append(blocker_word)

            # Step 3: Analyze translation requirements
            translation_stats = self._analyze_translation_needs(
                original_result.filtered_subtitles, unknown_blockers, known_blockers
            )

            # Step 4: Build translation segments
            translation_segments = self._build_translation_segments(
                original_result.filtered_subtitles, unknown_blockers
            )

            result = {
                "total_subtitles": len(original_result.filtered_subtitles),
                "original_blockers": len(original_result.blocker_words),
                "known_blockers": len(known_blockers),
                "unknown_blockers": len(unknown_blockers),
                "translation_count": len(translation_segments),
                "needs_translation": translation_segments,
                "filtering_stats": {
                    "total_blockers": len(original_result.blocker_words),
                    "known_blockers": len(known_blockers),
                    "unknown_blockers": len(unknown_blockers),
                    "translation_reduction": round((len(known_blockers) / len(original_result.blocker_words)) * 100, 1)
                    if original_result.blocker_words
                    else 0,
                },
                "translation_stats": translation_stats,
            }

            logger.info(
                f"Re-filtering complete: {len(unknown_blockers)}/{len(original_result.blocker_words)} "
                f"blockers still need translation"
            )
            return result

        except Exception as e:
            logger.error(f"Error during re-filtering: {e}")
            return self._create_empty_refilter_result()

    def _analyze_translation_needs(
        self, filtered_subtitles: list, unknown_blockers: list, known_blockers: list
    ) -> dict[str, Any]:
        """Analyze which subtitles need translation"""
        unknown_words = {blocker.word.lower() for blocker in unknown_blockers}

        subtitles_needing_translation = 0
        total_translation_words = 0

        for subtitle in filtered_subtitles:
            subtitle_has_unknown = False
            subtitle_unknown_count = 0

            for filtered_word in subtitle.filtered_words:
                if filtered_word.word.lower() in unknown_words:
                    subtitle_has_unknown = True
                    subtitle_unknown_count += 1

            if subtitle_has_unknown:
                subtitles_needing_translation += 1
                total_translation_words += subtitle_unknown_count

        return {
            "subtitles_needing_translation": subtitles_needing_translation,
            "total_subtitles": len(filtered_subtitles),
            "translation_percentage": round((subtitles_needing_translation / len(filtered_subtitles)) * 100, 1)
            if filtered_subtitles
            else 0,
            "average_unknown_words_per_subtitle": round(total_translation_words / subtitles_needing_translation, 1)
            if subtitles_needing_translation > 0
            else 0,
            "total_unknown_word_instances": total_translation_words,
        }

    def _build_translation_segments(self, filtered_subtitles: list, unknown_blockers: list) -> list[dict[str, Any]]:
        """Build segments that need translation"""
        unknown_words = {blocker.word.lower() for blocker in unknown_blockers}
        translation_segments = []

        for subtitle in filtered_subtitles:
            unknown_words_in_subtitle = []

            for filtered_word in subtitle.filtered_words:
                if filtered_word.word.lower() in unknown_words:
                    unknown_words_in_subtitle.append(
                        {
                            "word": filtered_word.word,
                            "lemma": getattr(filtered_word, "lemma", ""),
                            "pos": getattr(filtered_word, "pos", ""),
                            "difficulty": getattr(filtered_word, "difficulty", "unknown"),
                        }
                    )

            if unknown_words_in_subtitle:
                segment = {
                    "subtitle_index": subtitle.index,
                    "start_time": subtitle.start_time,
                    "end_time": subtitle.end_time,
                    "text": subtitle.text,
                    "unknown_words": unknown_words_in_subtitle,
                    "word_count": len(unknown_words_in_subtitle),
                }
                translation_segments.append(segment)

        return translation_segments

    def _create_empty_refilter_result(self) -> dict[str, Any]:
        """Create empty result structure for failed re-filtering"""
        return {
            "total_subtitles": 0,
            "original_blockers": 0,
            "known_blockers": 0,
            "unknown_blockers": 0,
            "translation_count": 0,
            "needs_translation": [],
            "filtering_stats": {
                "total_blockers": 0,
                "known_blockers": 0,
                "unknown_blockers": 0,
                "translation_reduction": 0,
            },
            "translation_stats": {
                "subtitles_needing_translation": 0,
                "total_subtitles": 0,
                "translation_percentage": 0,
                "average_unknown_words_per_subtitle": 0,
                "total_unknown_word_instances": 0,
            },
        }

    async def analyze_translation_complexity(
        self, srt_path: str, user_level: str, target_language: str
    ) -> dict[str, Any]:
        """Analyze overall translation complexity of content"""
        try:
            # This would analyze vocabulary density, difficulty distribution, etc.
            # For now, return a basic analysis structure
            return {
                "overall_difficulty": "intermediate",
                "vocabulary_density": "medium",
                "recommended_level": user_level,
                "complexity_score": 0.5,
                "content_type": "educational",
            }
        except Exception as e:
            logger.error(f"Error analyzing translation complexity: {e}")
            return {
                "overall_difficulty": "unknown",
                "vocabulary_density": "unknown",
                "recommended_level": user_level,
                "complexity_score": 0.0,
                "content_type": "unknown",
            }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the translation analyzer service"""
        return {"service": "TranslationAnalyzer", "status": "healthy", "subtitle_processor": "available"}

    async def initialize(self) -> None:
        """Initialize translation analyzer service resources"""
        logger.info("TranslationAnalyzer initialized")

    async def cleanup(self) -> None:
        """Cleanup translation analyzer service resources"""
        logger.info("TranslationAnalyzer cleanup completed")
