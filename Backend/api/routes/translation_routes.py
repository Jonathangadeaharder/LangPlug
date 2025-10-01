"""
Translation API routes for subtitle translation and selective translation functionality
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_async_session
from core.dependencies import (
    current_active_user,
    get_translation_service,
)
from database.models import User
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.processing.filtering_handler import FilteringHandler

from ..models.processing import ProcessingStatus, TranslateRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["translation"])


class SelectiveTranslationRequest(BaseModel):
    """Request for selective translation processing"""

    srt_path: str = Field(..., description="Path to SRT file")
    known_words: list[str] = Field(default=[], description="List of known words")
    target_language: str = Field("de", description="Target language code")
    user_level: str = Field("A1", description="User language level")


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
        video_file = Path(video_path) if video_path.startswith("/") else settings.get_videos_path() / video_path
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
        task_progress[task_id].message = f"Translating from {source_lang} to {target_lang}"

        # Read and parse the SRT file
        from utils.srt_parser import SRTParser

        srt_parser = SRTParser()
        segments = srt_parser.parse_file(str(srt_file))

        # Extract text for translation
        texts_to_translate = [segment.text for segment in segments]

        # Translate in batches for efficiency
        translated_results = translation_service.translate_batch(texts_to_translate, source_lang, target_lang)

        # Update segments with translated text
        for segment, translation_result in zip(segments, translated_results, strict=False):
            segment.text = translation_result.translated_text

        # Save translated subtitles to new file
        output_path = str(srt_file).replace(".srt", f"_{target_lang}.srt")
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


@router.post("/translate-subtitles", name="translate_subtitles")
async def translate_subtitles(
    request: TranslateRequest,
    current_user: User = Depends(current_active_user),
):
    """Translate subtitles from one language to another"""
    try:
        # Note: Currently using synchronous translation for simplicity
        # Background task support can be added in the future if needed

        translation_service = get_translation_service()
        if not translation_service:
            raise HTTPException(status_code=422, detail="Translation service is not available")

        # Get subtitle file path
        video_file = (
            Path(request.video_path)
            if request.video_path.startswith("/")
            else settings.get_videos_path() / request.video_path
        )
        srt_file = video_file.with_suffix(".srt")

        if not srt_file.exists():
            raise HTTPException(status_code=404, detail=f"Subtitle file not found: {srt_file}")

        # Quick translation for immediate return
        from utils.srt_parser import SRTParser

        srt_parser = SRTParser()
        segments = srt_parser.parse_file(str(srt_file))

        # Extract and translate text
        texts_to_translate = [segment.text for segment in segments]
        translated_results = translation_service.translate_batch(
            texts_to_translate, request.source_lang, request.target_lang
        )

        # Update segments with translated text
        for segment, translation_result in zip(segments, translated_results, strict=False):
            segment.text = translation_result.translated_text

        # Save translated subtitles
        output_path = str(srt_file).replace(".srt", f"_{request.target_lang}.srt")
        srt_parser.save_segments(segments, output_path)

        logger.info(f"Translation completed: {srt_file} -> {output_path}")
        return {"status": "completed", "output_path": output_path, "segments_translated": len(segments)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to translate subtitles: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {e!s}")


@router.post("/apply-selective-translations", name="apply_selective_translations")
async def apply_selective_translations(
    request: SelectiveTranslationRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Re-process chunk after vocabulary game to get updated translations.
    Since user has learned new words, the subtitle processor will now
    filter them out and only translate what's still needed.
    """
    try:
        srt_path = request.srt_path
        known_words_payload = request.known_words
        target_language = request.target_language
        user_level = request.user_level or getattr(current_user, "language_level", "A1")

        if not srt_path:
            raise HTTPException(status_code=400, detail="srt_path is required")

        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise HTTPException(status_code=404, detail=f"SRT file not found: {srt_path}")

        logger.info(
            "Selective translation requested for user %s (known words payload: %s)",
            current_user.id,
            len(known_words_payload),
        )

        # Normalise known words coming from the client
        payload_known_words = {str(word).lower() for word in known_words_payload if isinstance(word, str)}

        # Prepare filtering handler with a fresh subtitle processor
        subtitle_processor = DirectSubtitleProcessor()
        filtering_handler = FilteringHandler(subtitle_processor)

        # Fetch the authoritative known words from the database and merge with payload
        db_known_words = await subtitle_processor._get_user_known_words(
            str(current_user.id),
            target_language,
        )
        combined_known_words = sorted({*db_known_words, *payload_known_words})

        refilter_result = await filtering_handler.refilter_for_translations(
            srt_path=str(srt_file),
            user_id=str(current_user.id),
            known_words=combined_known_words,
            user_level=user_level,
            target_language=target_language,
        )

        logger.info(
            "Selective translation analysis complete for user %s: %s",
            current_user.id,
            refilter_result,
        )

        return {
            "success": True,
            "refilter_analysis": refilter_result,
            "known_words_count": len(combined_known_words),
            "subtitles_needing_translation": refilter_result["translation_count"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selective translation failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Selective translation processing failed: {e!s}")
