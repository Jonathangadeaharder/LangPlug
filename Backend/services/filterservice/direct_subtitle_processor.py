"""
Direct Subtitle Processor

Facade for subtitle processing and vocabulary filtering services.
This module provides a unified interface for processing subtitles with user-specific vocabulary filtering.

Key Components:
    - DirectSubtitleProcessor: Main facade for subtitle processing
    - Delegates to: user_data_loader, word_validator, word_filter, subtitle_processor, srt_file_handler
    - FilteringResult: Result structure with categorized content
    - FilteredSubtitle: Subtitle data structure

Usage Example:
    ```python
    processor = DirectSubtitleProcessor()

    # Process subtitle list
    result = await processor.process_subtitles(
        subtitles=[...],
        user_id=123,
        user_level="A1",
        language="de"
    )
    # result: FilteringResult with blocking_words, learning_subtitles, etc.

    # Process SRT file
    result = await processor.process_srt_file(
        srt_file_path="/path/to/video.srt",
        user_id=123,
        user_level="A1",
        language="de"
    )
    # result: Dict with processing results and statistics
    ```

Dependencies:
    - subtitle_processing: Focused sub-services (loader, validator, filter, processor, handler)
    - vocabulary_service: Word difficulty and user progress data

Thread Safety:
    Yes. Facade is stateless, delegates to services which manage their own state.

Performance Notes:
    - Pre-loads user known words and word difficulties
    - Processing: O(n) where n = number of subtitle segments
    - Uses vocabulary service for efficient database queries
"""

import logging
from typing import Any

from .interface import FilteredSubtitle, FilteringResult
from .subtitle_processing import srt_file_handler, subtitle_processor, user_data_loader, word_filter, word_validator

logger = logging.getLogger(__name__)


class DirectSubtitleProcessor:
    """
    Facade coordinating subtitle processing and vocabulary filtering.

    Provides high-level API for processing subtitles with user-specific filtering,
    delegating to specialized sub-services for data loading, validation, and filtering.

    Attributes:
        vocab_service: Vocabulary service for word lookups
        data_loader: Loads user known words and word difficulties
        validator: Validates word difficulty and learning status
        filter: Filters words based on user level and knowledge
        processor: Processes subtitles into categorized results
        file_handler: Handles SRT file parsing and result formatting

    Example:
        ```python
        processor = DirectSubtitleProcessor()

        # Process subtitles with automatic user data loading
        result = await processor.process_subtitles(
            subtitles=subtitle_list,
            user_id="123",
            user_level="B1",
            language="de"
        )

        print(f"Blocking words: {len(result.blocking_words)}")
        print(f"Learning subtitles: {len(result.learning_subtitles)}")
        ```

    Note:
        Maintains backward compatibility with legacy API.
        Automatically pre-loads user data for efficient processing.
    """

    def __init__(self):
        # Import the vocabulary service
        from services.vocabulary_service import VocabularyService

        self.vocab_service = VocabularyService()

        # Initialize focused services
        self.data_loader = user_data_loader
        self.validator = word_validator
        self.filter = word_filter
        self.processor = subtitle_processor
        self.file_handler = srt_file_handler

    async def process_subtitles(
        self, subtitles: list[FilteredSubtitle], user_id: int | str, user_level: str = "A1", language: str = "de"
    ) -> FilteringResult:
        """
        Process subtitles - delegates to SubtitleProcessor service

        Args:
            subtitles: List of subtitle objects to process
            user_id: User ID for personalized filtering
            user_level: User's language level (A1, A2, B1, B2, C1, C2)
            language: Target language code

        Returns:
            FilteringResult with categorized content
        """
        user_id_str = str(user_id)
        logger.info(f"Processing {len(subtitles)} subtitles for user {user_id_str}")

        # Pre-load user data
        user_known_words = await self.data_loader.get_user_known_words(user_id_str, language)
        await self.data_loader.load_word_difficulties(language)

        # Delegate to SubtitleProcessor
        result = await self.processor.process_subtitles(
            subtitles, user_known_words, user_level, language, self.vocab_service
        )

        # Add user_id to statistics for backward compatibility
        result.statistics["user_id"] = user_id_str

        return result

    async def process_srt_file(
        self, srt_file_path: str, user_id: int | str, user_level: str = "A1", language: str = "de"
    ) -> dict[str, Any]:
        """
        Process an SRT file - delegates to SRTFileHandler and SubtitleProcessor

        Args:
            srt_file_path: Path to SRT file
            user_id: User ID
            user_level: User's language level
            language: Language code

        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing SRT file: {srt_file_path}")

            # Parse SRT file using file handler
            filtered_subtitles = await self.file_handler.parse_srt_file(srt_file_path)

            # Process through filtering pipeline
            filtering_result = await self.process_subtitles(filtered_subtitles, str(user_id), user_level, language)

            # Format result using file handler
            result = self.file_handler.format_processing_result(filtering_result, srt_file_path)

            # Add segments_parsed for backward compatibility
            result["statistics"]["segments_parsed"] = len(filtered_subtitles)

            return result

        except Exception as e:
            logger.error(f"Error processing file {srt_file_path}: {e}", exc_info=True)
            return {
                "blocking_words": [],
                "learning_subtitles": [],
                "empty_subtitles": [],
                "filtered_subtitles": [],
                "statistics": {"error": str(e)},
            }
