"""
Filtering API routes for subtitle filtering and vocabulary processing
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.config import settings
from core.config.logging_config import get_logger
from core.dependencies import (
    current_active_user,
    get_subtitle_processor,
    get_task_progress_registry,
)
from database.models import User
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.filterservice.interface import FilteredSubtitle
from services.processing.translation_management_service import (
    TranslationManagementService,
    get_translation_management_service,
)
from utils.srt_parser import SRTParser

from ..models.processing import FilterRequest, ProcessingStatus, SelectiveTranslationRequest

logger = get_logger(__name__)
router = APIRouter(tags=["filtering"])


async def run_subtitle_filtering(
    video_path: str,
    task_id: str,
    task_progress: dict[str, Any],
    subtitle_processor: DirectSubtitleProcessor,
    current_user: User,
) -> None:
    """Run subtitle filtering in background"""
    try:
        logger.info("Starting filtering", task_id=task_id)

        # Initialize progress tracking
        task_progress[task_id] = ProcessingStatus(
            status="processing",
            progress=0.0,
            current_step="Starting filtering...",
            message="Initializing filter chain",
        )

        # Get subtitle file path
        # Normalize Windows backslashes to forward slashes for WSL compatibility
        normalized_path = video_path.replace("\\", "/")
        video_file = (
            Path(normalized_path) if normalized_path.startswith("/") else settings.get_videos_path() / normalized_path
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

        # Apply filtering using the subtitle processor
        filter_result = await subtitle_processor.process_srt_file(
            str(srt_file),
            str(current_user.id),
            user_level="A1",  # Should be fetched from user preferences
            language="de",  # Should be from request
        )

        # Step 3: Generate output (90% progress)
        task_progress[task_id].progress = 90.0
        task_progress[task_id].current_step = "Generating filtered output..."
        task_progress[task_id].message = "Creating filtered subtitle file"

        # Save filtered results
        output_path = str(srt_file).replace(".srt", "_filtered.srt")

        # Save filtered subtitles to file
        if not filter_result or "filtered_subtitles" not in filter_result:
            raise ValueError("No filtered subtitles generated")

        await _save_filtered_subtitles_to_file(filter_result["filtered_subtitles"], output_path)
        logger.debug("Saved filtered subtitles", path=output_path)

        # Complete (100% progress)
        task_progress[task_id].status = "completed"
        task_progress[task_id].progress = 100.0
        task_progress[task_id].current_step = "Filtering completed"
        task_progress[task_id].message = "Subtitles filtered successfully"

        logger.info("Filtering completed", task_id=task_id)

    except Exception as e:
        logger.error("Filtering failed", task_id=task_id, error=str(e), exc_info=True)
        task_progress[task_id] = ProcessingStatus(
            status="error",
            progress=0.0,
            current_step="Filtering failed",
            message=f"Error: {e!s}",
        )


@router.post("/filter-subtitles", name="filter_subtitles")
async def filter_subtitles(
    request: FilterRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    task_progress: dict[str, Any] = Depends(get_task_progress_registry),
    subtitle_processor: DirectSubtitleProcessor = Depends(get_subtitle_processor),
):
    """
    Filter subtitle content based on user's vocabulary knowledge level.

    Initiates background processing to filter subtitles, highlighting unknown words
    and applying vocabulary-based filtering according to user's CEFR level and
    known word list. Generates filtered subtitle file for adaptive learning.

    **Authentication Required**: Yes

    Args:
        request (FilterRequest): Filtering configuration with:
            - video_path (str): Relative or absolute path to video file
        background_tasks (BackgroundTasks): FastAPI background task manager
        current_user (User): Authenticated user
        task_progress (dict): Task progress tracking registry
        subtitle_processor (DirectSubtitleProcessor): Subtitle processing service

    Returns:
        dict: Task initiation response with:
            - task_id: Unique task identifier for progress tracking
            - status: "started"

    Raises:
        HTTPException: 422 if subtitle file not found
        HTTPException: 500 if task initialization fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/processing/filter-subtitles" \
          -H "Authorization: Bearer <token>" \
          -H "Content-Type: application/json" \
          -d '{
            "video_path": "Learn German/S01E01.mp4"
          }'
        ```

        Response:
        ```json
        {
            "task_id": "filter_123_1234567890.123",
            "status": "started"
        }
        ```

    Note:
        Use the returned task_id with /api/processing/progress/{task_id} to monitor
        filtering progress. Completed filtering generates a filtered SRT file with
        vocabulary annotations.
    """
    try:
        # Validate subtitle file exists before starting background task
        # Normalize Windows backslashes to forward slashes for WSL compatibility
        normalized_path = request.video_path.replace("\\", "/")
        video_file = (
            Path(normalized_path) if normalized_path.startswith("/") else settings.get_videos_path() / normalized_path
        )
        srt_file = video_file.with_suffix(".srt")

        if not srt_file.exists():
            raise HTTPException(status_code=422, detail=f"Subtitle file not found: {srt_file}")

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

        logger.info("Filtering task started", task_id=task_id)
        return {"task_id": task_id, "status": "started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start filtering", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Filtering failed: {e!s}") from e


@router.post("/apply-selective-translations", name="apply_selective_translations")
async def apply_selective_translations(
    request: SelectiveTranslationRequest,
    current_user: User = Depends(current_active_user),
    translation_service: TranslationManagementService = Depends(get_translation_management_service),
):
    """
    Apply selective translations based on known words.
    Re-filters subtitles to show only unknown words that need translation.
    """
    try:
        logger.debug("Applying selective translations", known_word_count=len(request.known_words))

        # Get user's target language and level from profile
        target_language = getattr(current_user, "target_language", "de")
        user_level = getattr(current_user, "language_level", "A1")

        # Call the translation management service
        result = await translation_service.apply_selective_translations(
            srt_path=request.srt_path,
            known_words=request.known_words,
            target_language=target_language,
            user_level=user_level,
            user_id=str(current_user.id),
        )

        logger.debug("Selective translations applied", segment_count=result.get("translation_count", 0))

        return {
            "success": True,
            "translation_path": request.srt_path,  # For now, return the same path
            "translation_count": result.get("translation_count", 0),
            "filtering_stats": result.get("filtering_stats", {}),
        }

    except Exception as e:
        logger.error("Selective translation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Selective translation failed: {e!s}") from e


async def _save_filtered_subtitles_to_file(filtered_subtitles: list[FilteredSubtitle], output_path: str) -> None:
    """
    Save filtered subtitles to an SRT file

    Args:
        filtered_subtitles: List of filtered subtitle objects
        output_path: Path where to save the filtered SRT file
    """
    try:
        srt_content = []

        for index, subtitle in enumerate(filtered_subtitles, start=1):
            # Create SRT block for each subtitle
            # FilteredSubtitle has: original_text, start_time, end_time, words
            srt_block = f"{index}\n"
            start_ts = SRTParser.format_timestamp(subtitle.start_time)
            end_ts = SRTParser.format_timestamp(subtitle.end_time)
            srt_block += f"{start_ts} --> {end_ts}\n"
            srt_block += f"{subtitle.original_text}\n\n"
            srt_content.append(srt_block)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(srt_content)

        logger.debug("Saved filtered subtitles", count=len(filtered_subtitles), path=output_path)

    except Exception as e:
        logger.error("Failed to save filtered subtitles", path=output_path, error=str(e))
        raise
