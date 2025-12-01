"""
Transcription API routes for video transcription functionality
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.config import settings
from core.config.logging_config import get_logger
from core.dependencies import (
    current_active_user,
    get_task_progress_registry,
    get_transcription_service,
)
from database.models import User
from services.transcriptionservice.interface import ITranscriptionService
from utils.media_validator import is_valid_video_file

from ..models.processing import TaskResponse, TranscribeRequest

logger = get_logger(__name__)
router = APIRouter(tags=["transcription"])


async def run_transcription(
    video_path: str, task_id: str, task_progress: dict[str, Any], transcription_service: ITranscriptionService
) -> None:
    """Run transcription in background"""
    try:
        logger.info("Starting transcription", task_id=task_id)

        task_progress[task_id] = {
            "status": "running",
            "progress": 0,
            "message": "Starting transcription",
            "started_at": datetime.now().isoformat(),
        }

        # Service is already injected and validated

        video_file = Path(video_path)
        if not video_file.exists():
            logger.error("Video not found", path=video_path)
            task_progress[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Video file not found",
                "error": f"File not found: {video_path}",
            }
            return

        if not is_valid_video_file(str(video_file)):
            logger.error("Invalid video file", path=video_path)
            task_progress[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Invalid video file format",
                "error": f"Unsupported format: {video_file.suffix}",
            }
            return

        task_progress[task_id]["progress"] = 25
        task_progress[task_id]["message"] = "Starting transcription engine"

        srt_path = video_file.with_suffix(".srt")

        logger.info("Transcribing video", video=str(video_file))
        result = await transcription_service.transcribe_video(video_path=str(video_file), output_path=str(srt_path))

        if result.get("success", False):
            task_progress[task_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Transcription completed successfully",
                "result": {
                    "srt_path": str(srt_path),
                    "video_path": str(video_file),
                    "duration": result.get("duration"),
                    "segments_count": result.get("segments_count"),
                },
                "completed_at": datetime.now().isoformat(),
            }
            logger.info("Transcription completed", task_id=task_id)
        else:
            task_progress[task_id] = {
                "status": "failed",
                "progress": 50,
                "message": "Transcription failed",
                "error": result.get("error", "Unknown transcription error"),
            }
            logger.error("Transcription failed", task_id=task_id, error=result.get("error"))

    except Exception as e:
        logger.error("Transcription task failed", task_id=task_id, error=str(e), exc_info=True)
        task_progress[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": "Internal transcription error",
            "error": str(e),
        }


@router.post("/transcribe", name="transcribe_video", response_model=TaskResponse)
async def transcribe_video(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
    transcription_service: ITranscriptionService = Depends(get_transcription_service),
):
    """
    Transcribe video audio to generate SRT subtitles using speech recognition.

    Initiates background transcription task using Whisper or configured transcription
    service. Validates video file format and existence before starting processing.

    **Authentication Required**: Yes

    Args:
        request (TranscribeRequest): Transcription request with:
            - video_path (str): Relative or absolute path to video file
        background_tasks (BackgroundTasks): FastAPI background task manager
        current_user (User): Authenticated user
        task_progress (dict): Task progress tracking registry
        transcription_service (ITranscriptionService): Injected transcription service

    Returns:
        TaskResponse: Task initiation response with task_id and status

    Raises:
        HTTPException: 404 if video file not found
        HTTPException: 422 if invalid video format
        HTTPException: 500 if task initialization fails
    """
    try:
        logger.info("Transcribe request", video_path=request.video_path)

        # Service availability check handled by dependency injection (would raise 500 if fails instantiation)
        # But we can check if it's None (though Depends usually implies success or error)
        if transcription_service is None:
            # This shouldn't happen with proper DI unless factory returns None
            logger.warning("Transcription service not available")
            raise HTTPException(
                status_code=422, detail="Transcription service is not available. Please check server configuration."
            )

        logger.info("Transcription service is available, checking video path")

        try:
            videos_path = settings.get_videos_path()
            logger.debug("Videos path", path=str(videos_path))
        except Exception as e:
            logger.error("Error getting videos path", error=str(e))
            raise HTTPException(status_code=500, detail="Configuration error") from e

        # Normalize Windows backslashes to forward slashes for WSL compatibility
        normalized_path = request.video_path.replace("\\", "/")
        full_path = Path(normalized_path) if normalized_path.startswith("/") else videos_path / normalized_path

        logger.debug("Full video path", path=str(full_path))

        if not full_path.exists():
            logger.error("Video not found", path=str(full_path))
            raise HTTPException(status_code=404, detail="Video file not found")

        if not is_valid_video_file(str(full_path)):
            logger.error("Invalid video format", path=str(full_path))
            raise HTTPException(status_code=422, detail="Unsupported video format")

        task_id = f"transcribe_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_transcription,
            str(full_path),
            task_id,
            task_progress,
            transcription_service,
        )

        logger.info("Transcription started", task_id=task_id)
        return TaskResponse(task_id=task_id, status="started")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start transcription", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e!s}") from e
