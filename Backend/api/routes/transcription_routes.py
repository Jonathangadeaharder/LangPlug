"""
Transcription API routes for video transcription functionality
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.config import settings
from core.dependencies import (
    current_active_user,
    get_task_progress_registry,
    get_transcription_service,
)
from database.models import User
from utils.media_validator import is_valid_video_file

from ..models.processing import TranscribeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["transcription"])


async def run_transcription(video_path: str, task_id: str, task_progress: dict[str, Any]) -> None:
    """Run transcription in background"""
    try:
        logger.info(f"Starting transcription task: {task_id}")

        task_progress[task_id] = {
            "status": "running",
            "progress": 0,
            "message": "Starting transcription",
            "started_at": datetime.now().isoformat(),
        }

        transcription_service = get_transcription_service()
        if transcription_service is None:
            logger.error("Transcription service not available")
            task_progress[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Transcription service not available",
                "error": "Service configuration error",
            }
            return

        video_file = Path(video_path)
        if not video_file.exists():
            logger.error(f"Video file not found: {video_path}")
            task_progress[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Video file not found",
                "error": f"File not found: {video_path}",
            }
            return

        if not is_valid_video_file(str(video_file)):
            logger.error(f"Invalid video file: {video_path}")
            task_progress[task_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Invalid video file format",
                "error": f"Unsupported format: {video_file.suffix}",
            }
            return

        task_progress[task_id]["progress"] = 25
        task_progress[task_id]["message"] = "Starting transcription engine"

        # Generate output path for SRT file
        srt_path = video_file.with_suffix(".srt")

        # Run transcription
        logger.info(f"Transcribing video: {video_file} -> {srt_path}")
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
            logger.info(f"Transcription completed successfully: {task_id}")
        else:
            task_progress[task_id] = {
                "status": "failed",
                "progress": 50,
                "message": "Transcription failed",
                "error": result.get("error", "Unknown transcription error"),
            }
            logger.error(f"Transcription failed: {task_id} - {result.get('error')}")

    except Exception as e:
        logger.error(f"Transcription task failed: {task_id} - {e!s}", exc_info=True)
        task_progress[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": "Internal transcription error",
            "error": str(e),
        }


@router.post("/transcribe", name="transcribe_video")
async def transcribe_video(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Transcribe video to generate subtitles"""
    try:
        logger.info(f"Transcribe request received: {request.video_path}")

        # Check if transcription service is available
        transcription_service = get_transcription_service()
        if transcription_service is None:
            logger.warning("Transcription service not available")
            raise HTTPException(
                status_code=422, detail="Transcription service is not available. Please check server configuration."
            )

        logger.info("Transcription service is available, checking video path")

        try:
            videos_path = settings.get_videos_path()
            logger.info(f"Videos path: {videos_path}")
        except Exception as e:
            logger.error(f"Error getting videos path: {e}")
            raise HTTPException(status_code=500, detail="Configuration error")

        full_path = Path(request.video_path) if request.video_path.startswith("/") else videos_path / request.video_path

        logger.info(f"Full video path: {full_path}")

        if not full_path.exists():
            logger.error(f"Video file not found: {full_path}")
            raise HTTPException(status_code=404, detail="Video file not found")

        if not is_valid_video_file(str(full_path)):
            logger.error(f"Invalid video format: {full_path}")
            raise HTTPException(status_code=422, detail="Unsupported video format")

        # Start transcription in background
        task_id = f"transcribe_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_transcription,
            str(full_path),
            task_id,
            task_progress,
        )

        logger.info(f"Started transcription task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start transcription: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e!s}")
