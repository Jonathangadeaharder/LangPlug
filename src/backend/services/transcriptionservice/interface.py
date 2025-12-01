"""
Transcription Service Interface
Defines the contract that all transcription services must implement
"""

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from services.base_service import IAIService

# Type alias for progress callback: (fraction: float, message: str) -> None
ProgressCallback = Callable[[float, str], Awaitable[None]]


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing"""

    start_time: float
    end_time: float
    text: str
    confidence: float | None = None
    speaker: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionResult:
    """Result of a transcription operation"""

    full_text: str
    segments: list[TranscriptionSegment]
    language: str | None = None
    duration: float | None = None
    metadata: dict[str, Any] | None = None


class ITranscriptionService(IAIService):
    """
    Interface for transcription services
    All transcription implementations must implement these methods
    """

    @abstractmethod
    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """
        Transcribe an audio file

        Args:
            audio_path: Path to the audio file
            language: Optional language hint (e.g., 'en', 'de')

        Returns:
            TranscriptionResult with transcription details
        """
        pass

    @abstractmethod
    def transcribe_with_timestamps(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """
        Transcribe with detailed timestamps for each segment

        Args:
            audio_path: Path to the audio file
            language: Optional language hint

        Returns:
            TranscriptionResult with timed segments
        """
        pass

    @abstractmethod
    async def transcribe_with_progress(
        self,
        audio_path: str,
        language: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with real-time progress updates.

        This is the preferred method for long-running transcriptions as it
        provides actual progress based on transcription completion, not estimates.

        Args:
            audio_path: Path to the audio file
            language: Optional language hint (e.g., 'en', 'de')
            progress_callback: Async callback receiving (fraction: 0-1, message: str)

        Returns:
            TranscriptionResult with transcription details

        Example:
            ```python
            async def on_progress(fraction: float, message: str):
                print(f"Progress: {fraction*100:.1f}% - {message}")

            result = await service.transcribe_with_progress(
                "audio.wav",
                language="de",
                progress_callback=on_progress
            )
            ```
        """
        pass

    @abstractmethod
    def transcribe_batch(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        """
        Transcribe multiple audio files in batch

        Args:
            audio_paths: List of paths to audio files
            language: Optional language hint

        Returns:
            List of TranscriptionResult objects
        """
        pass

    @abstractmethod
    def supports_video(self) -> bool:
        """
        Check if the service supports direct video transcription

        Returns:
            True if video files are supported, False otherwise
        """
        pass

    @abstractmethod
    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        """
        Extract audio from video file

        Args:
            video_path: Path to video file
            output_path: Optional path for extracted audio

        Returns:
            Path to extracted audio file
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes

        Returns:
            List of language codes (e.g., ['en', 'de', 'es'])
        """
        pass

    @property
    @abstractmethod
    def model_info(self) -> dict[str, Any]:
        """Get information about the loaded model"""
        pass
