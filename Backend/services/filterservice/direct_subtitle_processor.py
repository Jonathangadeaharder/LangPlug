"""
Direct Subtitle Processing - Facade for subtitle processing services
Delegates to focused services while maintaining backward compatibility
"""

import logging
from typing import Any

from .interface import FilteredSubtitle, FilteringResult
from .subtitle_processing import srt_file_handler, subtitle_processor, user_data_loader, word_filter, word_validator

logger = logging.getLogger(__name__)


class DirectSubtitleProcessor:
    """
    Facade for subtitle processing services
    Maintains backward compatibility while delegating to focused sub-services
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
