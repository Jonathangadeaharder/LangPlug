"""
Episode Processing API routes for chunk processing and episode preparation
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
)
from database.models import User

from ..models.processing import (
    ChunkProcessingRequest,
    ProcessingStatus,
    TranscribeRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["episode-processing"])


async def run_chunk_processing(
    video_path: str,
    start_time: float,
    end_time: float,
    task_id: str,
    task_progress: dict[str, Any],
    user_id: int,
    session_token: str | None = None,
) -> None:
    """Process a specific chunk of video for vocabulary learning"""
    from core.database import get_async_session
    from services.processing.chunk_processor import ChunkProcessingService

    try:
        # Get database session and create service instance
        async for db_session in get_async_session():
            chunk_processor = ChunkProcessingService(db_session)
            await chunk_processor.process_chunk(
                video_path=video_path,
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                task_id=task_id,
                task_progress=task_progress,
                session_token=session_token,
            )
            break  # Only use the first (and only) session

    except Exception as e:
        logger.error(f"Chunk processing failed for task {task_id}: {e}", exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Chunk processing failed",
            message=f"Error: {e!s}",
        )


async def run_processing_pipeline(
    video_path_str: str, task_id: str, task_progress: dict[str, Any], user_id: int
) -> None:
    """
    Run the full processing pipeline: transcription → filtering → vocabulary preparation
    """
    try:
        logger.info(f"Starting processing pipeline for task: {task_id}")

        # Initialize progress tracking
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting pipeline...",
            message="Initializing processing pipeline",
        )

        video_path = Path(video_path_str)
        if not video_path.exists():
            raise Exception(f"Video file not found: {video_path}")

        # Step 1: Transcription (0-40% progress)
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Transcribing video..."
        task_progress[task_id].message = "Generating subtitles from audio"

        # Import and use transcription service
        from core.dependencies import get_transcription_service

        transcription_service = get_transcription_service()
        if not transcription_service:
            raise Exception("Transcription service not available")

        srt_path = video_path.with_suffix(".srt")
        transcription_result = await transcription_service.transcribe_video(
            video_path=str(video_path), output_path=str(srt_path)
        )

        if not transcription_result.get("success", False):
            raise Exception(f"Transcription failed: {transcription_result.get('error')}")

        task_progress[task_id].progress = 40.0
        task_progress[task_id].current_step = "Transcription completed"
        task_progress[task_id].message = "Subtitles generated successfully"

        # Step 2: Filtering and analysis (40-80% progress)
        task_progress[task_id].progress = 50.0
        task_progress[task_id].current_step = "Analyzing subtitle content..."
        task_progress[task_id].message = "Extracting vocabulary and difficulty assessment"

        from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
        from services.processing.filtering_handler import FilteringHandler

        subtitle_processor = DirectSubtitleProcessor()
        filtering_handler = FilteringHandler(subtitle_processor)

        # Extract blocking words for vocabulary preparation
        vocabulary_words = await filtering_handler.extract_blocking_words(
            srt_path=str(srt_path),
            user_id=str(user_id),
            user_level="A1",  # Default level, should be fetched from user preferences
        )

        task_progress[task_id].progress = 80.0
        task_progress[task_id].current_step = "Content analysis completed"
        task_progress[task_id].message = f"Found {len(vocabulary_words)} vocabulary words for learning"

        # Step 3: Finalization (80-100% progress)
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Finalizing episode preparation..."
        task_progress[task_id].message = "Preparing learning materials"

        # Complete pipeline
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Episode ready for learning"
        task_progress[task_id].message = "Episode successfully prepared for vocabulary learning"

        logger.info(f"Processing pipeline completed for task {task_id}")

    except Exception as e:
        logger.error(f"Processing pipeline failed for task {task_id}: {e}", exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Pipeline failed",
            message=f"Error: {e!s}",
        )


@router.post("/chunk", name="process_chunk")
async def process_chunk(
    request: ChunkProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Process a specific chunk of video for vocabulary learning"""
    try:
        full_path = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else settings.get_videos_path() / request.video_path
        )
        # Validate chunk timing first
        if request.start_time < 0 or request.end_time <= request.start_time:
            raise HTTPException(status_code=400, detail="Invalid chunk timing")

        if not full_path.exists():
            logger.error(f"Video file not found: {full_path}")
            raise HTTPException(status_code=404, detail="Video file not found")

        # Start chunk processing in background
        task_id = (
            f"chunk_{current_user.id}_{int(request.start_time)}_{int(request.end_time)}_{datetime.now().timestamp()}"
        )
        background_tasks.add_task(
            run_chunk_processing,
            str(full_path),
            request.start_time,
            request.end_time,
            task_id,
            task_progress,
            current_user.id,
        )

        logger.info(f"Started chunk processing task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chunk processing: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chunk processing failed: {e!s}")


@router.post("/prepare-episode", name="prepare_episode")
async def prepare_episode_for_learning(
    request: TranscribeRequest,  # We can reuse the same request model
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Starts the full pipeline to prepare an episode for learning"""
    try:
        full_path = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else settings.get_videos_path() / request.video_path
        )
        if not full_path.exists():
            logger.error(f"Video file not found: {full_path}")
            raise HTTPException(status_code=404, detail="Video file not found")

        # Create a unique task ID
        task_id = f"prepare_{current_user.id}_{datetime.now().timestamp()}"

        # Add the full pipeline to background tasks
        background_tasks.add_task(
            run_processing_pipeline,
            str(full_path),
            task_id,
            task_progress,
            current_user.id,
        )

        logger.info(f"Started episode preparation task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        # Preserve intended HTTP errors (e.g., 404 for missing file)
        raise
    except Exception as e:
        logger.error(f"Failed to start episode preparation: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {e!s}")
