"""
Subtitle filtering handler service (Facade Pattern)
Delegates to specialized filtering services for better separation of concerns
"""

import logging
from typing import Any

from api.models.processing import VocabularyWord
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.interfaces.handler_interface import IFilteringHandler
from services.processing.filtering import (
    filtering_coordinator_service,
    progress_tracker_service,
    result_processor_service,
    subtitle_loader_service,
    vocabulary_builder_service,
)

logger = logging.getLogger(__name__)


class FilteringHandler(IFilteringHandler):
    """
    Facade for filtering operations - delegates to specialized services

    Architecture:
    - ProgressTrackerService: Manages progress tracking
    - SubtitleLoaderService: Handles file I/O and parsing
    - VocabularyBuilderService: Builds vocabulary words with database lookup
    - ResultProcessorService: Formats and saves results
    - FilteringCoordinatorService: Coordinates filtering workflow
    """

    def __init__(self, subtitle_processor: DirectSubtitleProcessor = None):
        # Initialize with sub-services
        self.subtitle_processor = subtitle_processor or DirectSubtitleProcessor()
        self.progress_tracker = progress_tracker_service
        self.loader = subtitle_loader_service
        self.vocab_builder = vocabulary_builder_service
        self.result_processor = result_processor_service
        self.coordinator = filtering_coordinator_service

        # Set subtitle processor on coordinator
        if subtitle_processor:
            self.coordinator.subtitle_processor = subtitle_processor

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the filtering handler"""
        return {
            "service": "FilteringHandler",
            "status": "healthy",
            "subtitle_processor": "available",
            "sub_services": {
                "progress_tracker": "available",
                "subtitle_loader": "available",
                "vocabulary_builder": "available",
                "result_processor": "available",
                "filtering_coordinator": "available",
            },
        }

    async def handle(self, task_id: str, task_progress: dict[str, Any], **kwargs) -> None:
        """Handle filtering task - delegates to filter_subtitles"""
        await self.filter_subtitles(task_id=task_id, task_progress=task_progress, **kwargs)

    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters for filtering"""
        required_params = ["srt_path", "user_id"]
        return all(param in kwargs for param in required_params)

    async def filter_subtitles(
        self,
        srt_path: str,
        task_id: str,
        task_progress: dict[str, Any],
        user_id: str,
        user_level: str = "A1",
        target_language: str = "de",
    ) -> dict[str, Any]:
        """
        Filter subtitles to extract vocabulary and learning content

        Args:
            srt_path: Path to SRT file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for personalized filtering
            user_level: User's language proficiency level
            target_language: Target language for filtering

        Returns:
            Dictionary containing filtering results
        """
        try:
            logger.info(f"Starting filtering task: {task_id}")

            # Initialize progress tracking
            self.progress_tracker.initialize(task_id, task_progress)

            # Step 1: Load and parse SRT file (0-20%)
            self.progress_tracker.update_progress(
                task_progress, task_id, 10.0, "Loading subtitles...", "Parsing subtitle file"
            )
            subtitles = await self.loader.load_and_parse(srt_path)

            # Step 2: Apply filtering (20-80%)
            self.progress_tracker.update_progress(
                task_progress, task_id, 20.0, "Filtering content...", f"Analyzing {len(subtitles)} subtitles"
            )
            filtering_result = await self.subtitle_processor.process_subtitles(
                subtitles, user_id=str(user_id), user_level=user_level, language=target_language
            )
            task_progress[task_id].progress = 80.0
            task_progress[task_id].message = f"Found {len(filtering_result.blocker_words)} vocabulary words"

            # Step 3: Build vocabulary words (80-85%)
            self.progress_tracker.update_progress(
                task_progress, task_id, 85.0, "Processing results...", "Building vocabulary data"
            )
            vocabulary_words = await self.vocab_builder.build_vocabulary_words(
                filtering_result.blocker_words, target_language, return_dict=True
            )

            # Step 4: Format results (85-95%)
            processed_results = await self.result_processor.process_filtering_results(
                filtering_result, vocabulary_words
            )

            # Step 5: Save filtered results (95-100%)
            self.progress_tracker.update_progress(
                task_progress, task_id, 95.0, "Saving results...", "Creating filtered output files"
            )
            result_path = await self.result_processor.save_to_file(processed_results, srt_path)
            task_progress[task_id].result_path = result_path

            # Mark as complete
            self.progress_tracker.mark_complete(task_progress, task_id, processed_results)

            logger.info(f"Filtering task {task_id} completed successfully")
            return processed_results

        except Exception as e:
            logger.error(f"Filtering task {task_id} failed: {e}")
            self.progress_tracker.mark_failed(task_progress, task_id, e)
            raise

    async def extract_blocking_words(self, srt_path: str, user_id: str, user_level: str = "A1") -> list[VocabularyWord]:
        """
        Extract blocking vocabulary words from subtitles

        Args:
            srt_path: Path to SRT file
            user_id: User ID
            user_level: User's language level

        Returns:
            List of vocabulary words that block comprehension
        """
        return await self.coordinator.extract_blocking_words(srt_path, user_id, user_level)

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
        return await self.coordinator.refilter_for_translations(
            srt_path, user_id, known_words, user_level, target_language
        )

    def estimate_duration(self, srt_path: str) -> int:
        """
        Estimate filtering duration in seconds

        Args:
            srt_path: Path to SRT file

        Returns:
            Estimated duration in seconds
        """
        return self.loader.estimate_duration(srt_path)
