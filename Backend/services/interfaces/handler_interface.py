"""
Handler interfaces for processing pipeline components
Provides standard patterns for background task processing with progress tracking
"""

from abc import abstractmethod
from typing import Any

from .base import IService


class IProcessingHandler(IService):
    """Base interface for processing handlers with progress tracking"""

    @abstractmethod
    async def handle(self, task_id: str, task_progress: dict[str, Any], **kwargs) -> None:
        """
        Handle a processing task with progress tracking

        Args:
            task_id: Unique task identifier for progress tracking
            task_progress: Progress tracking dictionary
            **kwargs: Handler-specific parameters
        """
        pass

    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate input parameters for the handler

        Args:
            **kwargs: Parameters to validate

        Returns:
            True if parameters are valid
        """
        pass


class ITranscriptionHandler(IProcessingHandler):
    """Interface for transcription handling operations"""

    @abstractmethod
    async def run_transcription(
        self, video_path: str, task_id: str, task_progress: dict[str, Any], language: str = "de"
    ) -> None:
        """
        Run transcription with progress tracking

        Args:
            video_path: Path to video file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            language: Target language for transcription
        """
        pass


class ITranslationHandler(IProcessingHandler):
    """Interface for translation handling operations"""

    @abstractmethod
    async def run_translation(
        self, video_path: str, task_id: str, task_progress: dict[str, Any], source_lang: str, target_lang: str
    ) -> None:
        """
        Run translation with progress tracking

        Args:
            video_path: Path to video file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            source_lang: Source language
            target_lang: Target language
        """
        pass


class IFilteringHandler(IProcessingHandler):
    """Interface for filtering handling operations"""

    @abstractmethod
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
        Filter subtitles with progress tracking

        Args:
            srt_path: Path to SRT file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for personalized filtering
            user_level: User's language proficiency level
            target_language: Target language for filtering

        Returns:
            Filtering results dictionary
        """
        pass

    @abstractmethod
    async def refilter_for_translations(
        self, srt_path: str, user_id: str, known_words: list[str], user_level: str, target_language: str
    ) -> dict[str, Any]:
        """
        Re-filter subtitles for translation needs

        Args:
            srt_path: Path to SRT file
            user_id: User ID
            known_words: List of known words to exclude
            user_level: User's language level
            target_language: Target language

        Returns:
            Re-filtering results dictionary
        """
        pass


class IPipelineHandler(IProcessingHandler):
    """Interface for pipeline orchestration handlers"""

    @abstractmethod
    async def run_processing_pipeline(
        self, video_path: str, task_id: str, task_progress: dict[str, Any], user_id: int
    ) -> None:
        """
        Run full processing pipeline with progress tracking

        Args:
            video_path: Path to video file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for processing
        """
        pass


class IChunkHandler(IProcessingHandler):
    """Interface for chunk processing handlers"""

    @abstractmethod
    async def process_chunk(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        task_id: str,
        task_progress: dict[str, Any],
        user_id: int,
        session_token: str | None = None,
    ) -> None:
        """
        Process video chunk with progress tracking

        Args:
            video_path: Path to video file
            start_time: Chunk start time in seconds
            end_time: Chunk end time in seconds
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            user_id: User ID for processing
            session_token: Optional session token
        """
        pass
