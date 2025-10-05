"""
Chunk Processing Service

Facade for processing video chunks for vocabulary learning with transcription and translation.
Coordinates audio extraction, transcription, vocabulary filtering, and subtitle generation.

Key Components:
    - ChunkProcessingService: Main orchestration facade
    - ChunkTranscriptionService: Audio extraction and speech-to-text
    - ChunkTranslationService: Translation segment building
    - ChunkUtilities: Helper utilities for path resolution and progress tracking

Processing Pipeline:
    1. Extract audio chunk (0-20% progress)
    2. Transcribe audio to text (5-35%)
    3. Filter vocabulary for learning (35-65%)
    4. Generate filtered subtitles (85-95%)
    5. Build translation segments (95-100%)

Usage Example:
    ```python
    service = ChunkProcessingService(db_session)

    await service.process_chunk(
        video_path="/videos/series/episode.mp4",
        start_time=0.0,
        end_time=30.0,
        user_id=123,
        task_id="chunk_abc123",
        task_progress=progress_dict,
        session_token="session_token_here"
    )
    ```

Dependencies:
    - sqlalchemy: Database session for user/vocabulary queries
    - ChunkTranscriptionService: Audio and transcription handling
    - ChunkTranslationService: Translation service management
    - FFmpeg: External tool for audio extraction (required)

Thread Safety:
    No. Each request should have its own service instance with dedicated db_session.

Performance Notes:
    - Audio extraction: ~2-5 seconds per 30s chunk
    - Transcription: ~5-10 seconds per 30s chunk (depends on model)
    - Translation: ~2-5 seconds for 10-20 segments
    - Total: ~10-20 seconds per 30s chunk

Architecture Notes:
    - Database operations are handled by delegated services using their own sessions
    - Orchestration layer coordinates file I/O and ML inference without transaction overhead
    - Each service manages its own transactional boundaries for atomicity
"""

import logging
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.interfaces.handler_interface import IChunkHandler

from .chunk_transcription_service import ChunkTranscriptionService
from .chunk_translation_service import ChunkTranslationService
from .chunk_utilities import ChunkUtilities
from .subtitle_generation_service import subtitle_generation_service
from .translation_management_service import translation_management_service
from .vocabulary_filter_service import vocabulary_filter_service

logger = logging.getLogger(__name__)


class ChunkProcessingError(Exception):
    """Base exception for chunk processing errors"""

    pass


class ChunkProcessingService(IChunkHandler):
    """
    Orchestration facade for video chunk processing pipeline.

    Coordinates multiple services to extract audio, transcribe speech, filter vocabulary,
    and generate learning-optimized subtitles. Implements the handler interface.

    Attributes:
        db_session (AsyncSession): Database session for user and vocabulary queries
        transcription_service (ChunkTranscriptionService): Handles audio extraction and transcription
        translation_service (ChunkTranslationService): Manages translation services
        utilities (ChunkUtilities): Path resolution and progress tracking helpers
        vocabulary_filter: Service for filtering vocabulary from subtitles
        subtitle_generator: Service for generating filtered subtitle files
        translation_manager: Service for managing translations

    Example:
        ```python
        async with get_db_session() as db:
            service = ChunkProcessingService(db)

            await service.process_chunk(
                video_path="/videos/german_series/s01e01.mp4",
                start_time=0.0,
                end_time=30.0,
                user_id=123,
                task_id="task_xyz",
                task_progress=progress_tracker,
                session_token="token"
            )
            # Creates: video.srt, video_filtered.srt, video_translation.srt
        ```

    Note:
        Progress tracking updates task_progress dictionary in-place.
        Automatically cleans up temporary audio files.
        Delegated services handle their own database transactions.
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

        Note:
            Database operations are handled by delegated services using their own sessions.
            This orchestration layer coordinates file I/O and ML inference without transaction overhead.
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

            # Step 2: Transcribe chunk (5-35% progress)
            srt_file = await self.transcription_service.transcribe_chunk(
                task_id, task_progress, video_file, audio_file, language_preferences, start_time, end_time
            )

            # Step 3: Filter vocabulary (35-65% progress)
            vocabulary = await self._filter_vocabulary(task_id, task_progress, srt_file, user, language_preferences)

            # Step 4: Generate filtered subtitles (85-95% progress)
            filtered_srt = await self._generate_filtered_subtitles(
                task_id, task_progress, srt_file, vocabulary, language_preferences
            )

            # Step 5: Build translation segments (95-100% progress)
            translation_segments = await self.translation_service.build_translation_segments(
                task_id,
                task_progress,
                srt_file,
                vocabulary,
                language_preferences,
            )

            # Step 6: Write translation segments to file
            translation_srt_path = None
            if translation_segments:
                from pathlib import Path as PathLib

                from utils.srt_parser import SRTParser

                # Generate translation file path
                srt_file_str = str(srt_file) if srt_file else str(video_file).replace(".mp4", ".srt")
                translation_srt_path = srt_file_str.replace(".srt", "_translation.srt")

                # Write translation SRT file
                translation_content = SRTParser.segments_to_srt(translation_segments)
                PathLib(translation_srt_path).write_text(translation_content, encoding="utf-8")

                logger.info(
                    f"[CHUNK DEBUG] Wrote {len(translation_segments)} translation segments to {translation_srt_path}"
                )

            # Complete processing with subtitle paths
            self.utilities.complete_processing(
                task_id,
                task_progress,
                vocabulary,
                subtitle_path=str(srt_file) if srt_file else None,
                translation_path=translation_srt_path,
            )

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
        srt_file: str,
        user,
        language_preferences: dict[str, Any],
    ) -> list:
        """
        Filter vocabulary from subtitles - delegates to VocabularyFilterService

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            srt_file: Path to chunk SRT file
            user: Authenticated user object
            language_preferences: User language preferences

        Returns:
            List of vocabulary words for learning
        """
        # Start filtering at 35%
        task_progress[task_id].progress = 35
        task_progress[task_id].current_step = "Filtering vocabulary..."
        task_progress[task_id].message = "Loading subtitle file"

        # Use the chunk SRT file passed as parameter
        srt_file_path = srt_file

        # Delegate to vocabulary filter service with progress tracking
        # Service will update progress from 35% -> 65% internally
        vocabulary = await self.vocabulary_filter.filter_vocabulary_from_srt(
            srt_file_path, user, language_preferences, task_id, task_progress
        )

        logger.info(f"[CHUNK DEBUG] Filtered {len(vocabulary)} vocabulary words")
        return vocabulary

    async def _generate_filtered_subtitles(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        srt_file: str,
        vocabulary: list,
        language_preferences: dict[str, Any],
    ) -> str:
        """
        Generate filtered subtitle files - delegates to SubtitleGenerationService

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            srt_file: Path to chunk SRT file
            vocabulary: List of vocabulary words
            language_preferences: User language preferences

        Returns:
            Path to the generated filtered subtitle file
        """
        task_progress[task_id].progress = 90
        task_progress[task_id].current_step = "Generating filtered subtitles..."
        task_progress[task_id].message = "Creating learning-optimized subtitle files"

        # Use the chunk SRT file directly (no need to search for it)

        video_file = Path(srt_file).with_suffix(".mp4")  # Derive video path from SRT

        # Delegate to subtitle generation service
        filtered_srt = await self.subtitle_generator.generate_filtered_subtitles(video_file, vocabulary, srt_file)

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
