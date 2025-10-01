"""
Processing service interfaces for video, subtitle, and translation operations.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any

from .base import IAsyncService


class ITranscriptionService(IAsyncService):
    """Interface for video transcription operations"""

    @abstractmethod
    async def transcribe_video(
        self, video_path: Path, language: str = "de", model: str | None = None
    ) -> dict[str, Any]:
        """Transcribe video to text with timestamps"""
        pass

    @abstractmethod
    async def transcribe_audio(
        self, audio_path: Path, language: str = "de", model: str | None = None
    ) -> dict[str, Any]:
        """Transcribe audio file to text"""
        pass

    @abstractmethod
    async def get_supported_languages(self) -> list[str]:
        """Get list of supported transcription languages"""
        pass

    @abstractmethod
    async def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available transcription models"""
        pass


class ITranslationService(IAsyncService):
    """Interface for text translation operations"""

    @abstractmethod
    async def translate_text(
        self, text: str, source_language: str, target_language: str, model: str | None = None
    ) -> str:
        """Translate text from source to target language"""
        pass

    @abstractmethod
    async def translate_batch(
        self, texts: list[str], source_language: str, target_language: str, model: str | None = None
    ) -> list[str]:
        """Translate multiple texts in batch"""
        pass

    @abstractmethod
    async def get_supported_language_pairs(self) -> list[dict[str, str]]:
        """Get supported source-target language pairs"""
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """Detect language of given text"""
        pass


class ISubtitleProcessor(IAsyncService):
    """Interface for subtitle processing and filtering operations"""

    @abstractmethod
    async def process_subtitles(
        self, srt_content: str, user_id: int, language: str = "de", difficulty_filter: str | None = None
    ) -> dict[str, Any]:
        """Process subtitles with vocabulary filtering"""
        pass

    @abstractmethod
    async def extract_vocabulary(self, srt_content: str, language: str = "de") -> list[dict[str, Any]]:
        """Extract vocabulary words from subtitles"""
        pass

    @abstractmethod
    async def filter_known_words(self, words: list[str], user_id: int, language: str = "de") -> list[str]:
        """Filter out words known by user"""
        pass

    @abstractmethod
    async def generate_learning_subtitles(
        self, srt_content: str, user_id: int, target_language: str = "es", source_language: str = "de"
    ) -> str:
        """Generate subtitles with translations for unknown words"""
        pass


class IVideoProcessingService(IAsyncService):
    """Interface for video processing operations"""

    @abstractmethod
    async def extract_audio(self, video_path: Path, output_path: Path | None = None) -> Path:
        """Extract audio from video file"""
        pass

    @abstractmethod
    async def create_video_chunk(
        self, video_path: Path, start_time: float, end_time: float, output_path: Path | None = None
    ) -> Path:
        """Create video chunk for specified time range"""
        pass

    @abstractmethod
    async def get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video metadata information"""
        pass

    @abstractmethod
    async def validate_video_file(self, video_path: Path) -> bool:
        """Validate video file format and accessibility"""
        pass


class IProcessingPipelineService(IAsyncService):
    """Interface for orchestrating complete processing pipelines"""

    @abstractmethod
    async def run_full_pipeline(
        self,
        video_path: Path,
        user_id: int,
        source_language: str = "de",
        target_language: str = "es",
        user_level: str | None = None,
    ) -> dict[str, Any]:
        """Run complete video processing pipeline"""
        pass

    @abstractmethod
    async def run_chunk_pipeline(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        user_id: int,
        source_language: str = "de",
        target_language: str = "es",
    ) -> dict[str, Any]:
        """Run processing pipeline for video chunk"""
        pass

    @abstractmethod
    async def get_pipeline_status(self, task_id: str) -> dict[str, Any]:
        """Get status of running pipeline"""
        pass

    @abstractmethod
    async def cancel_pipeline(self, task_id: str) -> bool:
        """Cancel running pipeline"""
        pass


class ITaskProgressService(IAsyncService):
    """Interface for tracking task progress"""

    @abstractmethod
    async def create_task(self, task_type: str, user_id: int, metadata: dict[str, Any] | None = None) -> str:
        """Create new task and return task ID"""
        pass

    @abstractmethod
    async def update_progress(self, task_id: str, progress: float, status: str, message: str | None = None) -> bool:
        """Update task progress"""
        pass

    @abstractmethod
    async def complete_task(self, task_id: str, result: dict[str, Any]) -> bool:
        """Mark task as completed with result"""
        pass

    @abstractmethod
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed with error"""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get current task status"""
        pass
