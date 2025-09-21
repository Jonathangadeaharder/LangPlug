"""
Processing API routes (transcription, filtering, translation)
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from utils.media_validator import is_valid_video_file
from utils.transcription import WhisperTranscription
from utils.video_downloader import download_video
from utils.srt_parser import SRTParser
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.config import settings
from core.dependencies import (
    current_active_user,
    get_subtitle_processor,
    get_task_progress_registry,
    get_transcription_service,
    get_translation_service,
)
from database.models import User
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

from ..models.processing import (
    ChunkProcessingRequest,
    FilterRequest,
    FullPipelineRequest,
    ProcessingStatus,
    TranscribeRequest,
    TranslateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["processing"])


# Note: _format_srt_timestamp function removed - using SRTParser.format_timestamp instead
# to eliminate code duplication (DRY principle)


async def run_transcription(
    video_path: str, task_id: str, task_progress: dict[str, Any]
) -> None:
    """Run transcription in background"""
    try:
        logger.info(f"Starting transcription task: {task_id}")

        # Initialize progress tracking
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting transcription...",
            message="Initializing Whisper model",
            started_at=int(time.time()),
        )

        logger.info(f"Initialized task progress for background task: {task_id}")

        # Step 1: Load model (10% progress)
        task_progress[task_id].progress = 10.0
        task_progress[task_id].current_step = "Loading AI model..."
        task_progress[task_id].message = "Preparing Whisper for German audio"
        await asyncio.sleep(2)  # Simulate model loading time

        # Step 2: Extract audio from video if needed (30% progress)
        task_progress[task_id].progress = 30.0
        task_progress[task_id].current_step = "Processing audio..."
        task_progress[task_id].message = "Extracting audio track from video"
        await asyncio.sleep(3)  # Simulate audio extraction

        # Step 3: Run transcription (70% progress)
        task_progress[task_id].progress = 70.0
        task_progress[task_id].current_step = "Transcribing audio..."
        task_progress[task_id].message = "Converting German speech to text"

        # Get transcription service
        logger.info("Getting transcription service...")
        transcription_service = get_transcription_service()
        logger.info(f"Transcription service result: {transcription_service}")

        if transcription_service is None:
            task_progress[task_id].status = "error"
            task_progress[task_id].current_step = "Service unavailable"
            task_progress[task_id].message = "Transcription service is not available. Please check server configuration."
            logger.error("Transcription service is None - service failed to initialize")
            return

        logger.info(f"Running transcription with service: {type(transcription_service)}")
        result = transcription_service.transcribe(
            video_path, language=settings.default_language
        )

        # Step 4: Save results (90% progress)
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Saving subtitles..."
        task_progress[task_id].message = "Creating subtitle file"
        await asyncio.sleep(1)  # Simulate file saving

        # Save result to SRT file
        video_path_obj = Path(video_path)
        srt_path = video_path_obj.with_suffix(".srt")

        # Create SRT content from transcription segments
        srt_content = []
        for i, segment in enumerate(result.segments, 1):
            # Format timestamps in SRT format (HH:MM:SS,mmm)
            start_time = SRTParser.format_timestamp(segment.start_time)
            end_time = SRTParser.format_timestamp(segment.end_time)

            # Build SRT entry
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment.text)
            srt_content.append("")  # Empty line between entries

        # Write SRT file
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))

        # Complete (100% progress)
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Transcription completed"
        task_progress[task_id].message = "Subtitles are ready for learning!"

        logger.info(f"Transcription completed for task {task_id}")

    except Exception as e:
        error_msg = str(e) if str(e) else f"Unknown error: {type(e).__name__}"
        logger.error(f"Transcription failed for task {task_id}: {error_msg}", exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Transcription failed",
            message=f"Error: {error_msg}",
        )


async def run_subtitle_filtering(
    video_path: str,
    task_id: str,
    task_progress: dict[str, Any],
    subtitle_processor,
    current_user: User,
) -> None:
    """Run subtitle filtering in background"""
    try:
        logger.info(f"Starting filtering task: {task_id}")

        # Initialize progress tracking
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting filtering...",
            message="Initializing filter chain",
        )

        # Get subtitle file path
        video_file = (
            Path(video_path)
            if video_path.startswith("/")
            else settings.get_videos_path() / video_path
        )
        srt_file = video_file.with_suffix(".srt")

        if not srt_file.exists():
            raise Exception(f"Subtitle file not found: {srt_file}")

        # Step 1: Load subtitles (20% progress)
        task_progress[task_id].progress = 20.0
        task_progress[task_id].current_step = "Loading subtitles..."
        task_progress[task_id].message = "Reading subtitle file"
        await asyncio.sleep(1)  # Simulate file loading

        # Step 2: Process with filter chain (70% progress)
        task_progress[task_id].progress = 70.0
        task_progress[task_id].current_step = "Filtering subtitles..."
        task_progress[task_id].message = "Applying vocabulary filters"
        # Process with simplified subtitle processor
        user_level = getattr(current_user, 'language_level', 'A1')  # Default to A1
        filtered_subtitles = await subtitle_processor.process_srt_file(
            str(srt_file), current_user.id, user_level, "de"
        )
        await asyncio.sleep(2)  # Simulate filtering process

        # Complete (100% progress)
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Filtering completed"
        task_progress[task_id].message = "Subtitles filtered successfully"
        # Result is not stored in ProcessingStatus model - data is persisted through other means

        logger.info(f"Filtering completed for task {task_id}")

    except Exception as e:
        logger.error(f"Filtering failed for task {task_id}: {e}", exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Filtering failed",
            message=f"Error: {e!s}",
        )


async def run_translation(
    video_path: str,
    task_id: str,
    task_progress: dict[str, Any],
    source_lang: str,
    target_lang: str,
) -> None:
    """Run subtitle translation in background"""
    try:
        logger.info(f"Starting translation task: {task_id}")

        # Initialize progress tracking
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting translation...",
            message="Initializing translation service",
        )

        # Get subtitle file path
        video_file = (
            Path(video_path)
            if video_path.startswith("/")
            else settings.get_videos_path() / video_path
        )
        srt_file = video_file.with_suffix(".srt")

        if not srt_file.exists():
            raise Exception(f"Subtitle file not found: {srt_file}")

        # Step 1: Load subtitles (20% progress)
        task_progress[task_id].progress = 20.0
        task_progress[task_id].current_step = "Loading subtitles..."
        task_progress[task_id].message = "Reading subtitle file"
        await asyncio.sleep(1)  # Simulate file loading

        # Step 2: Initialize translation service (40% progress)
        task_progress[task_id].progress = 40.0
        task_progress[task_id].current_step = "Initializing translation service..."
        task_progress[task_id].message = "Loading translation model"

        translation_service = get_translation_service()
        if not translation_service.is_initialized:
            translation_service.initialize()

        # Step 3: Translate subtitles (80% progress)
        task_progress[task_id].progress = 80.0
        task_progress[task_id].current_step = "Translating subtitles..."
        task_progress[task_id].message = (
            f"Translating from {source_lang} to {target_lang}"
        )

        # Read and parse the SRT file
        from utils.srt_parser import SRTParser

        srt_parser = SRTParser()
        segments = srt_parser.parse_file(str(srt_file))

        # Extract text for translation
        texts_to_translate = [segment.text for segment in segments]

        # Translate in batches for efficiency
        translated_results = translation_service.translate_batch(
            texts_to_translate,
            source_lang,
            target_lang
        )

        # Update segments with translated text
        for segment, translation_result in zip(segments, translated_results, strict=False):
            segment.text = translation_result.translated_text

        # Save translated subtitles to new file
        output_path = str(srt_file).replace('.srt', f'_{target_lang}.srt')
        srt_parser.save_segments(segments, output_path)

        # Complete (100% progress)
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Translation completed"
        task_progress[task_id].message = "Subtitles translated successfully"

        logger.info(f"Translation completed for task {task_id}")

    except Exception as e:
        logger.error(f"Translation failed for task {task_id}: {e}", exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Translation failed",
            message=f"Error: {e!s}",
        )


async def run_processing_pipeline(
    video_path_str: str, task_id: str, task_progress: dict[str, Any], user_id: int
) -> None:
    """Run a full processing pipeline: Transcribe -> Filter -> Translate"""
    try:
        logger.info(
            f"Starting full processing pipeline task: {task_id} for user {user_id}"
        )
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Initializing...",
            message="Preparing to process video.",
        )
        video_path = Path(video_path_str)
        srt_path = video_path.with_suffix(".srt")

        # === 1. Transcription (0% -> 50%) ===
        task_progress[task_id].progress = 5.0
        task_progress[task_id].current_step = "Step 1: Transcription"
        task_progress[task_id].message = "Loading transcription model..."

        transcription_service = get_transcription_service()
        if not transcription_service:
            task_progress[task_id].status = "error"
            task_progress[task_id].current_step = "Service unavailable"
            task_progress[task_id].message = "Transcription service is not available. Please check server configuration."
            logger.error("Transcription service not available - check Whisper installation")
            return

        task_progress[task_id].progress = 25.0
        task_progress[task_id].message = (
            "AI is converting speech to text. This may take a while..."
        )

        # This is a blocking call, but it runs in the background task thread
        result = transcription_service.transcribe(
            video_path_str, language=settings.default_language
        )

        # Save result to SRT file
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result.segments):
                start = segment.start_time
                end = segment.end_time
                text = segment.text

                # Basic SRT formatting
                f.write(f"{i+1}\n")
                f.write(
                    f"{str(timedelta(seconds=start)).replace('.', ',')} --> {str(timedelta(seconds=end)).replace('.', ',')}\n"
                )
                f.write(f"{text}\n\n")

        task_progress[task_id].progress = 50.0
        logger.info(f"Task {task_id}: Transcription complete.")

        # === 2. Filtering (50% -> 80%) ===
        task_progress[task_id].current_step = "Step 2: Filtering Subtitles"
        task_progress[task_id].message = "Analyzing vocabulary..."

        subtitle_processor = DirectSubtitleProcessor()
        # Process subtitles with simplified processor
        user_level = "A1"  # Default level - should be configurable per user
        filtered_subtitles = subtitle_processor.process_srt_file(str(srt_path), user_id, user_level, "de")

        task_progress[task_id].progress = 80.0
        task_progress[task_id].message = (
            f"Found {len(filtered_subtitles.get('blocking_words', []))} new words to learn."
        )
        logger.info(f"Task {task_id}: Filtering complete.")

        # === 3. Translation (80% -> 100%) ===
        task_progress[task_id].current_step = "Step 3: Translating Vocabulary"
        task_progress[task_id].message = "Generating definitions for new words..."

        # (This part is a placeholder for actual translation logic if you add it)
        # For now, we'll just simulate the work
        await asyncio.sleep(2)  # Simulate translation API calls

        task_progress[task_id].progress = 100.0
        logger.info(f"Task {task_id}: Translation complete.")

        # === 4. Completion ===
        task_progress[task_id].status = "completed"
        task_progress[task_id].current_step = "Processing Complete"
        task_progress[task_id].message = "Episode is ready for learning!"
        logger.info(f"Pipeline completed for task {task_id}")

    except Exception as e:
        current_step = task_progress.get(task_id, {}).current_step or "Unknown Step"
        logger.error(
            f"Processing pipeline failed for task {task_id} at {current_step}: {e}",
            exc_info=True,
        )
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=task_progress.get(task_id, {}).progress or 0.0,
            current_step="Processing Failed",
            message=f"An error occurred during {current_step}.",
        )


async def run_chunk_processing(
    video_path: str,
    start_time: float,
    end_time: float,
    task_id: str,
    task_progress: dict[str, Any],
    user_id: int,
    session_token: str = None,
) -> None:
    """Process a specific chunk of video for vocabulary learning - REFACTORED"""
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
                session_token=session_token
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
        task_id = f"chunk_{current_user.id}_{int(request.start_time)}_{int(request.end_time)}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_chunk_processing,
            str(full_path),
            request.start_time,
            request.end_time,
            task_id,
            task_progress,
            current_user.id,
            None,  # session_token - will generate fallback token in function
        )

        logger.info(f"Started chunk processing task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chunk processing: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Chunk processing failed: {e!s}"
        )


@router.post("/transcribe", name="transcribe_video")
async def transcribe_video(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Transcribe video to generate subtitles"""
    try:
        print(f"DEBUG: Transcribe request received: {request.video_path}")
        logger.info(f"Transcribe request received: {request.video_path}")

        # Check if transcription service is available
        transcription_service = get_transcription_service()
        if transcription_service is None:
            logger.warning("Transcription service not available")
            raise HTTPException(
                status_code=422,
                detail="Transcription service is not available. Please check server configuration."
            )

        logger.info("Transcription service is available, checking video path")

        try:
            videos_path = settings.get_videos_path()
            logger.info(f"Videos path: {videos_path}")
        except Exception as e:
            logger.error(f"Error getting videos path: {e}")
            raise HTTPException(status_code=500, detail="Configuration error")

        full_path = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else videos_path / request.video_path
        )

        logger.info(f"Full video path: {full_path}")

        if not full_path.exists():
            logger.error(f"Video file not found: {full_path}")
            raise HTTPException(status_code=404, detail="Video file not found")

        # Start transcription in background
        task_id = f"transcribe_{current_user.id}_{datetime.now().timestamp()}"

        # Initialize task progress before starting background task
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Initializing transcription",
            message="Preparing to start transcription"
        )

        logger.info(f"Initialized task progress for: {task_id}")
        logger.info(f"Video path: {full_path}")
        logger.info(f"Task progress dict id: {id(task_progress)}")

        # Test transcription service before starting background task
        test_service = get_transcription_service()
        logger.info(f"Pre-flight transcription service check: {test_service}")

        background_tasks.add_task(
            run_transcription, str(full_path), task_id, task_progress
        )

        logger.info(f"Started transcription task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start transcription: {e!s}", exc_info=True)
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception repr: {e!r}")
        logger.error(f"Exception args: {e.args}")
        error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
        raise HTTPException(status_code=500, detail=f"Transcription failed: {error_msg}")


@router.post("/filter-subtitles", name="filter_subtitles")
async def filter_subtitles(
    request: FilterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
    subtitle_processor: DirectSubtitleProcessor = Depends(get_subtitle_processor),
):
    """Filter subtitles based on user's vocabulary knowledge"""
    try:
        # Validate subtitle file exists before starting background task
        video_file = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else settings.get_videos_path() / request.video_path
        )
        srt_file = video_file.with_suffix(".srt")

        if not srt_file.exists():
            raise HTTPException(
                status_code=422, 
                detail=f"Subtitle file not found: {srt_file}"
            )

        # Start filtering in background
        task_id = f"filter_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_subtitle_filtering,
            request.video_path,
            task_id,
            task_progress,
            subtitle_processor,
            current_user,
        )

        logger.info(f"Started filtering task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        # Re-raise HTTP exceptions (like 422)
        raise
    except Exception as e:
        logger.error(f"Failed to start filtering: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Filtering failed: {e!s}")


@router.post("/translate-subtitles", name="translate_subtitles")
async def translate_subtitles(
    request: TranslateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Translate subtitles from one language to another"""
    try:
        # Start translation in background
        task_id = f"translate_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_translation,
            request.video_path,
            task_id,
            task_progress,
            request.source_lang,
            request.target_lang,
        )

        logger.info(f"Started translation task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except Exception as e:
        logger.error(f"Failed to start translation: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {e!s}")


@router.post("/prepare-episode", name="prepare_episode")
async def prepare_episode_for_learning(
    request: TranscribeRequest,  # We can reuse the same request model
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Starts the full pipeline to prepare an episode for learning."""
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
        raise HTTPException(
            status_code=500, detail=f"Failed to start processing: {e!s}"
        )


@router.post("/full-pipeline", name="full_pipeline")
async def full_pipeline(
    request: FullPipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Run a full processing pipeline: Transcribe -> Filter -> Translate"""
    try:
        # Start full pipeline in background
        task_id = f"pipeline_{current_user.id}_{datetime.now().timestamp()}"
        background_tasks.add_task(
            run_processing_pipeline, request.video_path, task_id, task_progress, current_user.id
        )

        logger.info(f"Started full processing pipeline task: {task_id}")
        return {"task_id": task_id, "status": "started"}

    except Exception as e:
        logger.error(f"Failed to start processing pipeline: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Processing pipeline failed: {e!s}"
        )


@router.get("/progress/{task_id}", name="get_task_progress")
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
):
    """Get progress of a background task"""
    logger.info(f"[PROGRESS CHECK] Task ID: {task_id}")
    logger.info(f"[PROGRESS CHECK] Available tasks: {list(task_progress.keys())}")

    if task_id not in task_progress:
        logger.warning(f"[PROGRESS CHECK] ❌ Task {task_id} NOT FOUND in registry")
        raise HTTPException(status_code=404, detail="Task not found")

    progress_data = task_progress[task_id]
    logger.info(f"[PROGRESS CHECK] ✅ Task {task_id} found - Status: {progress_data.status}, Progress: {progress_data.progress}%")
    logger.info(f"[PROGRESS CHECK] Current step: {progress_data.current_step}")
    logger.info(f"[PROGRESS CHECK] Message: {progress_data.message}")

    if progress_data.status == "completed":
        logger.info(f"[PROGRESS CHECK] 🎉 Task {task_id} is COMPLETED!")
        if hasattr(progress_data, 'vocabulary'):
            logger.info(f"[PROGRESS CHECK] Vocabulary items: {len(progress_data.vocabulary) if progress_data.vocabulary else 0}")
        if hasattr(progress_data, 'subtitle_path'):
            logger.info(f"[PROGRESS CHECK] Subtitle path: {progress_data.subtitle_path}")
        if hasattr(progress_data, 'translation_path'):
            logger.info(f"[PROGRESS CHECK] Translation path: {getattr(progress_data, 'translation_path', None)}")

    return progress_data
