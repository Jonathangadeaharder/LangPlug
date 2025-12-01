"""
Transcription handling service
Extracted from api/routes/processing.py for better separation of concerns
"""

import asyncio
import time
from pathlib import Path
from typing import Any

from api.models.processing import ProcessingStatus
from core.config.logging_config import get_logger
from services.transcriptionservice.interface import ITranscriptionService
from utils.media_validator import is_valid_video_file

logger = get_logger(__name__)


class TranscriptionHandler:
    """Handles transcription operations for video processing"""

    def __init__(self, transcription_service: ITranscriptionService):
        self.transcription_service = transcription_service

    async def run_transcription(
        self, video_path: str, task_id: str, task_progress: dict[str, Any], language: str = "de"
    ) -> None:
        """
        Run transcription in background with progress tracking

        Args:
            video_path: Path to video file
            task_id: Unique task identifier
            task_progress: Progress tracking dictionary
            language: Target language for transcription
        """
        try:
            logger.info("Starting transcription task", task_id=task_id)

            # Initialize progress tracking
            task_progress[task_id] = ProcessingStatus(
                status="processing",
                progress=0.0,
                current_step="Starting transcription...",
                message="Initializing transcription model",
                started_at=int(time.time()),
            )

            # Step 1: Validate video file
            await self._validate_video(video_path, task_progress, task_id)

            # Step 2: Load model (10% progress)
            await self._load_model(task_progress, task_id, language)

            # Step 3: Extract audio (30% progress)
            audio_path = await self._extract_audio(video_path, task_progress, task_id)

            # Step 4: Run transcription (70% progress)
            result = await self._transcribe_audio(audio_path, task_progress, task_id, language)

            # Step 5: Save results (90% progress)
            await self._save_results(result, video_path, task_progress, task_id)

            # Mark as complete
            task_progress[task_id].status = "completed"
            task_progress[task_id].progress = 100.0
            task_progress[task_id].message = "Transcription completed successfully"
            task_progress[task_id].completed_at = int(time.time())

            logger.info("Transcription task completed", task_id=task_id)

        except Exception as e:
            logger.error("Transcription task failed", task_id=task_id, error=str(e))
            task_progress[task_id].status = "failed"
            task_progress[task_id].error = str(e)
            task_progress[task_id].message = f"Transcription failed: {e!s}"
            raise

    async def _validate_video(self, video_path: str, task_progress: dict[str, Any], task_id: str) -> None:
        """Validate video file exists and is valid"""
        task_progress[task_id].progress = 5.0
        task_progress[task_id].current_step = "Validating video..."
        task_progress[task_id].message = "Checking video file"

        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not is_valid_video_file(str(video_file)):
            raise ValueError(f"Invalid video file format: {video_path}")

    async def _load_model(self, task_progress: dict[str, Any], task_id: str, language: str) -> None:
        """Load transcription model"""
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Loading AI model..."
        task_progress[task_id].message = f"Preparing model for {language} audio"

        # Simulate model loading or actual loading
        await asyncio.sleep(2)

    async def _extract_audio(self, video_path: str, task_progress: dict[str, Any], task_id: str) -> str:
        """Extract audio from video file"""
        task_progress[task_id].progress = 30.0
        task_progress[task_id].current_step = "Processing audio..."
        task_progress[task_id].message = "Extracting audio track from video"

        # Here you would implement actual audio extraction
        # For now, simulating the process
        await asyncio.sleep(3)

        # Return audio file path
        audio_path = str(Path(video_path).with_suffix(".wav"))
        return audio_path

    async def _transcribe_audio(
        self, audio_path: str, task_progress: dict[str, Any], task_id: str, language: str
    ) -> dict[str, Any]:
        """Run actual transcription"""
        task_progress[task_id].progress = 70.0
        task_progress[task_id].current_step = "Transcribing audio..."
        task_progress[task_id].message = f"Converting {language} speech to text"

        # Use the injected transcription service
        result = await self.transcription_service.transcribe(audio_path, language=language, task_id=task_id)

        return result

    async def _save_results(
        self, result: dict[str, Any], video_path: str, task_progress: dict[str, Any], task_id: str
    ) -> None:
        """Save transcription results to SRT file"""
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Saving results..."
        task_progress[task_id].message = "Creating subtitle file"

        # Save to SRT file
        srt_path = Path(video_path).with_suffix(".srt")

        # Here you would implement SRT file creation
        # Using the transcription segments from result

        task_progress[task_id].result_path = str(srt_path)

    def estimate_duration(self, video_path: str) -> int:
        """
        Estimate transcription duration in seconds

        Args:
            video_path: Path to video file

        Returns:
            Estimated duration in seconds
        """
        # Basic estimation: 1 minute of video = 10 seconds of processing
        # In real implementation, would check actual video duration
        return 60  # Default estimate
