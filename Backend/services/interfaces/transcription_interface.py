"""
Transcription service interfaces for abstraction and dependency inversion
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .base import IAsyncService


class ITranscriptionService(IAsyncService):
    """Interface for transcription services"""

    @abstractmethod
    async def transcribe_video(self, video_path: str, output_path: str, language: str | None = None) -> dict[str, Any]:
        """
        Transcribe a video file to text

        Args:
            video_path: Path to video file
            output_path: Path where transcription should be saved
            language: Optional language hint for transcription

        Returns:
            Transcription result with success status and metadata
        """
        pass

    @abstractmethod
    async def transcribe_audio(self, audio_path: str, output_path: str, language: str | None = None) -> dict[str, Any]:
        """
        Transcribe an audio file to text

        Args:
            audio_path: Path to audio file
            output_path: Path where transcription should be saved
            language: Optional language hint for transcription

        Returns:
            Transcription result with success status and metadata
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if transcription service is properly initialized"""
        pass


class IChunkTranscriptionService(ABC):
    """Interface for chunk-specific transcription operations"""

    @abstractmethod
    async def extract_audio_chunk(
        self, task_id: str, task_progress: dict[str, Any], video_file: Path, start_time: float, end_time: float
    ) -> None:
        """
        Extract audio chunk from video for transcription

        Args:
            task_id: Processing task identifier
            task_progress: Progress tracking dictionary
            video_file: Path to source video file
            start_time: Start time of chunk in seconds
            end_time: End time of chunk in seconds
        """
        pass

    @abstractmethod
    async def transcribe_chunk(
        self,
        task_id: str,
        task_progress: dict[str, Any],
        video_file: Path,
        language_preferences: dict[str, Any] | None = None,
    ) -> None:
        """
        Transcribe audio chunk to text

        Args:
            task_id: Processing task identifier
            task_progress: Progress tracking dictionary
            video_file: Path to source video file
            language_preferences: User language preferences
        """
        pass

    @abstractmethod
    def find_matching_srt_file(self, video_file: Path) -> str:
        """
        Find existing SRT file for video or return target path

        Args:
            video_file: Path to video file

        Returns:
            Path to existing or target SRT file
        """
        pass
