"""
Chunk processing service interfaces for abstraction and dependency inversion
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from database.models import User

from .base import IAsyncService


class IChunkProcessingService(IAsyncService):
    """Interface for chunk processing orchestration"""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass


class IChunkUtilities(ABC):
    """Interface for chunk processing utilities"""

    @abstractmethod
    def resolve_video_path(self, video_path: str) -> Path:
        """
        Resolve video path to absolute path

        Args:
            video_path: Video path (absolute or relative)

        Returns:
            Absolute Path to video file
        """
        pass

    @abstractmethod
    async def get_authenticated_user(self, user_identifier: Any, session_token: str | None = None) -> User:
        """
        Get authenticated user from database

        Args:
            user_identifier: User ID (int, str, or UUID)
            session_token: Optional session token for validation

        Returns:
            User object from database
        """
        pass

    @abstractmethod
    def load_user_language_preferences(self, user: User) -> dict[str, Any]:
        """
        Load user's language preferences

        Args:
            user: User object

        Returns:
            Dictionary containing language preferences
        """
        pass

    @abstractmethod
    def initialize_progress(
        self, task_id: str, task_progress: dict[str, Any], video_file: Path, start_time: float, end_time: float
    ) -> None:
        """
        Initialize progress tracking for chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            video_file: Path to video file
            start_time: Chunk start time
            end_time: Chunk end time
        """
        pass

    @abstractmethod
    def complete_processing(
        self, task_id: str, task_progress: dict[str, Any], vocabulary: list[Any] | None = None
    ) -> None:
        """
        Mark chunk processing as completed

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            vocabulary: Optional vocabulary results
        """
        pass

    @abstractmethod
    def handle_error(self, task_id: str, task_progress: dict[str, Any], error: Exception) -> None:
        """
        Handle error in chunk processing

        Args:
            task_id: Processing task ID
            task_progress: Progress tracking dictionary
            error: Exception that occurred
        """
        pass

    @abstractmethod
    def cleanup_old_chunk_files(self, video_file: Path, start_time: float, end_time: float) -> None:
        """
        Clean up old chunk-related files

        Args:
            video_file: Path to the video file
            start_time: Chunk start time
            end_time: Chunk end time
        """
        pass
