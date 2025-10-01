"""
ChunkProcessingService - Facade for video chunk processing
Delegates to focused component services for better separation of concerns
"""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.interfaces.chunk_interface import IChunkProcessingService
from services.interfaces.handler_interface import IChunkHandler

from .chunk_services import subtitle_generation_service, translation_management_service, vocabulary_filter_service
from .chunk_transcription_service import ChunkTranscriptionService
from .chunk_translation_service import ChunkTranslationService
from .chunk_utilities import ChunkUtilities

logger = logging.getLogger(__name__)


class ChunkProcessingError(Exception):
    """Base exception for chunk processing errors"""

    pass


class ChunkProcessingService(IChunkProcessingService, IChunkHandler):
    """
    Facade for processing video chunks for vocabulary learning
    Coordinates transcription, filtering, and subtitle generation using focused services
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.transcription_service = ChunkTranscriptionService()
        self.translation_service = ChunkTranslationService()
        self.utilities = ChunkUtilities(db_session)

        # New focused services
        self.vocabulary_filter = vocabulary_filter_service
        self.subtitle_generator = subtitle_generation_service
        self.translation_manager = translation_management_service

    async def process_chunk(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        user_id: int,
        task_id: str,
        task_progress: dict[str, Any],
        session_token: str | None = None,
    ) -> None:
        """
        Process a specific chunk of video for vocabulary learning

        Args:
            video_path: Path to video file
            start_time: Start time of chunk in seconds
            end_time: End time of chunk in seconds
            user_id: User ID requesting processing
            task_id: Unique task identifier for progress tracking
            task_progress: Progress tracking dictionary
            session_token: Optional session token for authentication
        """
        try:
            # Resolve video path and initialize progress
            video_file = self.utilities.resolve_video_path(video_path)
            self.utilities.initialize_progress(task_id, task_progress, video_file, start_time, end_time)

            # Authenticate user
            user = await self.utilities.get_authenticated_user(user_id, session_token)
            language_preferences = self.utilities.load_user_language_preferences(user)

            # Step 1: Extract audio chunk (0-20% progress)
            audio_file = await self.transcription_service.extract_audio_chunk(
                task_id, task_progress, video_file, start_time, end_time
            )

            # Step 2: Transcribe chunk (20-50% progress)
            srt_file = await self.transcription_service.transcribe_chunk(
                task_id, task_progress, video_file, audio_file, language_preferences
            )

            # Step 3: Filter vocabulary (50-85% progress)
            vocabulary = await self._filter_vocabulary(task_id, task_progress, video_file, user, language_preferences)

            # Step 4: Generate filtered subtitles (85-95% progress)
            filtered_srt = await self._generate_filtered_subtitles(
                task_id, task_progress, video_file, vocabulary, language_preferences
            )

            # Step 5: Build translation segments (95-100% progress)
            translation_segments = await self.translation_service.build_translation_segments(
                task_id,
                task_progress,
                self.transcription_service.find_matching_srt_file(video_file),
                vocabulary,
                language_preferences,
            )

            # Complete processing
            self.utilities.complete_processing(task_id, task_progress, vocabulary)

            # Cleanup temporary audio file if it was created
            self.transcription_service.cleanup_temp_audio_file(audio_file, video_file)

            # Cleanup old chunk files
            self.utilities.cleanup_old_chunk_files(video_file, start_time, end_time)

        except Exception as e:
            logger.error(f"Chunk processing failed for task {task_id}: {e}", exc_info=True)
            # Cleanup temporary audio file on error
            if "audio_file" in locals():
                self.transcription_service.cleanup_temp_audio_file(audio_file, video_file)
            self.utilities.handle_error(task_id, task_progress, e)
            raise

    async def _filter_vocabulary(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        user,
        language_preferences: dict[str, Any],
    ) -> list:
        """
        Filter vocabulary from subtitles - delegates to VocabularyFilterService

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            video_file: Path to video file
            user: Authenticated user object
            language_preferences: User language preferences

        Returns:
            List of vocabulary words for learning
        """
        task_progress[task_id].progress = 70.0
        task_progress[task_id].current_step = "Filtering vocabulary..."
        task_progress[task_id].message = "Analyzing subtitles for learning words"

        # Find matching SRT file
        srt_file_path = self.transcription_service.find_matching_srt_file(video_file)

        # Delegate to vocabulary filter service
        vocabulary = await self.vocabulary_filter.filter_vocabulary_from_srt(srt_file_path, user, language_preferences)

        logger.info(f"[CHUNK DEBUG] Filtered {len(vocabulary)} vocabulary words")
        return vocabulary

    async def _generate_filtered_subtitles(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        vocabulary: list,
        language_preferences: dict[str, Any],
    ) -> str:
        """
        Generate filtered subtitle files - delegates to SubtitleGenerationService

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            video_file: Path to video file
            vocabulary: List of vocabulary words
            language_preferences: User language preferences

        Returns:
            Path to the generated filtered subtitle file
        """
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Generating filtered subtitles..."
        task_progress[task_id].message = "Creating learning-optimized subtitle files"

        # Find the source SRT file
        source_srt = self.transcription_service.find_matching_srt_file(video_file)

        # Delegate to subtitle generation service
        filtered_srt = await self.subtitle_generator.generate_filtered_subtitles(video_file, vocabulary, source_srt)

        return filtered_srt

    async def apply_selective_translations(
        self,
        srt_path: str,
        known_words: list[str],
        target_language: str,
        user_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Apply selective translations - delegates to TranslationManagementService

        Args:
            srt_path: Path to SRT file
            known_words: List of words user already knows
            target_language: Target language code
            user_level: User's language level
            user_id: User identifier

        Returns:
            Translation analysis results
        """
        return await self.translation_manager.apply_selective_translations(
            srt_path, known_words, target_language, user_level, user_id
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the chunk processing service"""
        return {
            "service": "ChunkProcessingService",
            "status": "healthy",
            "components": {"transcription": "available", "translation": "available", "utilities": "available"},
        }

    async def initialize(self) -> None:
        """Initialize chunk processing service resources"""
        logger.info("ChunkProcessingService initialized")

    async def cleanup(self) -> None:
        """Cleanup chunk processing service resources"""
        logger.info("ChunkProcessingService cleanup completed")

    async def handle(self, task_id: str, task_progress: dict[str, Any], **kwargs) -> None:
        """Handle chunk processing task - delegates to process_chunk"""
        await self.process_chunk(task_id=task_id, task_progress=task_progress, **kwargs)

    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters for chunk processing"""
        required_params = ["video_path", "start_time", "end_time", "user_id"]
        return all(param in kwargs for param in required_params)
