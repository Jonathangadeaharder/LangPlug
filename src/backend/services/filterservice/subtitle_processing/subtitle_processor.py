"""
Subtitle Processor Service
Handles processing of subtitles through filtering pipeline
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.config.logging_config import get_logger

from ..interface import FilteredSubtitle, FilteredWord, FilteringResult, WordStatus
from .word_filter import WordFilter
from .word_validator import WordValidator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class SubtitleProcessor:
    """Service for processing subtitles with filtering logic"""

    def __init__(self, validator: WordValidator | None = None, word_filter: WordFilter | None = None):
        self.validator = validator or WordValidator()
        self.word_filter = word_filter or WordFilter()

    async def process_subtitles(
        self,
        subtitles: list[FilteredSubtitle],
        user_known_words: set[str],
        user_level: str,
        language: str,
        vocab_service: Any,
        db: "AsyncSession",
    ) -> FilteringResult:
        """
        Process subtitles with filtering logic

        Args:
            subtitles: List of subtitle objects to process
            user_known_words: Set of lemmas user knows
            user_level: User's language level (A1-C2)
            language: Target language code
            vocab_service: Vocabulary service for word info
            db: Database session (passed once, not created per word)

        Returns:
            FilteringResult with categorized content
        """
        logger.debug("Processing subtitles", count=len(subtitles))

        # Initialize processing state
        processing_state = self._initialize_processing_state()

        # Process each subtitle
        for subtitle in subtitles:
            await self._process_single_subtitle(
                subtitle, user_known_words, user_level, language, vocab_service, db, processing_state
            )

        # Create and return result
        return self._create_filtering_result(processing_state, len(subtitles), user_level, language)

    def _initialize_processing_state(self) -> dict:
        """Initialize state tracking for subtitle processing"""
        return {
            "learning_subtitles": [],
            "blocker_words": [],
            "empty_subtitles": [],
            "total_words": 0,
            "active_words": 0,
            "filtered_words": 0,
        }

    async def _process_single_subtitle(
        self,
        subtitle: FilteredSubtitle,
        user_known_words: set[str],
        user_level: str,
        language: str,
        vocab_service: Any,
        db: "AsyncSession",
        processing_state: dict,
    ) -> None:
        """Process a single subtitle and update processing state"""
        processed_words = []
        subtitle_active_words = []

        for word in subtitle.words:
            processing_state["total_words"] += 1

            processed_word = await self._process_and_filter_word(
                word, user_known_words, user_level, language, vocab_service, db
            )
            processed_words.append(processed_word)

            if processed_word.status == WordStatus.ACTIVE:
                subtitle_active_words.append(processed_word)
                processing_state["active_words"] += 1
            else:
                processing_state["filtered_words"] += 1

        # Update subtitle with processed words
        subtitle.words = processed_words

        # Categorize subtitle
        self._categorize_subtitle(subtitle, subtitle_active_words, processing_state)

    async def _process_and_filter_word(
        self,
        word: FilteredWord,
        user_known_words: set[str],
        user_level: str,
        language: str,
        vocab_service: Any,
        db: "AsyncSession",
    ) -> FilteredWord:
        """Process and filter a single word"""
        word_text = word.text.lower().strip()

        # Step 1: Basic validation
        if not self.validator.is_valid_vocabulary_word(word_text, language):
            word.status = WordStatus.FILTERED_INVALID
            reason = self.validator.get_validation_reason(word_text, language)
            word.filter_reason = f"Non-vocabulary word ({reason})"
            return word

        # Step 2: Get word info from vocabulary service (using passed session, not creating new one)
        try:
            word_info = await vocab_service.get_word_info(word_text, language, db)
        except Exception as exc:
            logger.error("Failed to load word info", word=word_text, error=str(exc))
            word_info = None

        # Step 3: Apply filtering logic
        return self.word_filter.filter_word(word, user_known_words, user_level, language, word_info=word_info)

    def _categorize_subtitle(
        self, subtitle: FilteredSubtitle, subtitle_active_words: list[FilteredWord], processing_state: dict
    ) -> None:
        """
        Categorize subtitle based on difficulty level

        FILTERING LOGIC (Language Learning):
        - User level = what they've mastered (e.g., A2 = mastered A1-A2)
        - If ALL words at/below level → FILTER OUT (user understands, no subtitle needed)
        - If ANY word above level → KEEP (show for translation/learning)

        Purpose: Hide subtitles user understands, show subtitles with words above their level
        """
        # Check if subtitle has words above user level (needs learning)
        if subtitle.has_active_words:
            # Subtitle has words above user level - KEEP for learning/translation
            processing_state["learning_subtitles"].append(subtitle)
            logger.debug(
                f"[SUBTITLE FILTER] KEPT: '{subtitle.original_text[:50]}...' - Contains words above user level"
            )
        elif subtitle.all_words_understood:
            # All words at/below level or known - user understands, FILTER OUT
            processing_state["empty_subtitles"].append(subtitle)
            logger.debug(
                f"[SUBTITLE FILTER] FILTERED OUT: '{subtitle.original_text[:50]}...' - All words at/below user level"
            )
        else:
            # No vocabulary content
            processing_state["empty_subtitles"].append(subtitle)
            logger.debug("Filtered out subtitle - no vocabulary content")

    def _create_filtering_result(
        self, processing_state: dict, total_subtitles: int, user_level: str, language: str
    ) -> FilteringResult:
        """Create FilteringResult with statistics"""
        statistics = self._compile_statistics(processing_state, total_subtitles, user_level, language)

        logger.info(
            f"Processing complete: {len(processing_state['learning_subtitles'])} learning subtitles, "
            f"{len(processing_state['blocker_words'])} blocker words, "
            f"{len(processing_state['empty_subtitles'])} empty subtitles"
        )

        return FilteringResult(
            learning_subtitles=processing_state["learning_subtitles"],
            blocker_words=processing_state["blocker_words"],
            empty_subtitles=processing_state["empty_subtitles"],
            statistics=statistics,
        )

    def _compile_statistics(self, processing_state: dict, total_subtitles: int, user_level: str, language: str) -> dict:
        """Compile processing statistics"""
        total_words = processing_state["total_words"]
        filtered_words = processing_state["filtered_words"]

        return {
            "total_subtitles": total_subtitles,
            "learning_subtitles": len(processing_state["learning_subtitles"]),
            "blocker_words": len(processing_state["blocker_words"]),
            "empty_subtitles": len(processing_state["empty_subtitles"]),
            "total_words": total_words,
            "active_words": processing_state["active_words"],
            "filtered_words": filtered_words,
            "filter_rate": filtered_words / max(total_words, 1),
            "learning_rate": len(processing_state["learning_subtitles"]) / max(total_subtitles, 1),
            "processing_time": datetime.now().isoformat(),
            "user_level": user_level,
            "language": language,
        }


# Singleton instance
subtitle_processor = SubtitleProcessor()
