"""Vocabulary management API routes"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_async_session
from core.dependencies import current_active_user
from database.models import User
from utils.srt_parser import SRTParser
from services.vocabulary_preload_service import VocabularyPreloadService, get_vocabulary_preload_service

from ..models.vocabulary import (
    BulkMarkRequest,
    MarkKnownRequest,
    VocabularyLevel,
    VocabularyLibraryWord,
    VocabularyStats,
    VocabularyWord,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vocabulary"])


async def extract_blocking_words_for_segment(
    srt_path: str, start: int, duration: int, user_id: int, db: AsyncSession
) -> list[VocabularyWord]:
    """Extract blocking words from a specific time segment"""
    try:
        # Parse the SRT file
        srt_parser = SRTParser()
        segments = srt_parser.parse_file(srt_path)

        # Filter segments within the time range
        end_time = start + duration
        relevant_segments = [
            seg for seg in segments
            if seg.start_time <= end_time and seg.end_time >= start
        ]

        if not relevant_segments:
            logger.warning(f"No segments found for time range {start}-{end_time}")
            return []

        # Get subtitle processor for processing
        from core.dependencies import get_subtitle_processor

        # Get the actual user from database using user_id
        try:
            # Get user by ID from database
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            current_user = result.scalar_one_or_none()

            if not current_user:
                raise ValueError(f"User with id {user_id} not found in database")
        except Exception as e:
            logger.error(f"Could not get user from database: {e}")
            raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

        # Use subtitle processor for vocabulary extraction
        subtitle_processor = get_subtitle_processor(db)

        # Process segments through subtitle processor to get blocking words
        # Use A1 level as default for blocking words detection
        result = await subtitle_processor.process_srt_file(srt_path, user_id, "A1", "de")

        # Check for processing errors first
        if "error" in result.get("statistics", {}):
            error_msg = result["statistics"]["error"]
            logger.error(f"[VOCABULARY ERROR] Subtitle processing failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Vocabulary extraction failed: {error_msg}")

        # Extract blocking words from the result
        blocking_words = result.get("blocking_words", [])

        logger.info(f"Found {len(blocking_words)} blocking words for user {user_id} in segment {start}-{end_time}")

        # Filter words that fall within our time segment
        # Note: This is a simplified approach - in a more sophisticated implementation,
        # you'd track word timing more precisely
        segment_words = []
        for word in blocking_words:
            # For now, include all blocking words from relevant segments
            # This could be enhanced to check actual word timing
            segment_words.append(word)

        return segment_words[:10]  # Limit to 10 words for UI performance

    except Exception as e:
        logger.error(f"Error in extract_blocking_words_for_segment: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Vocabulary extraction failed: {e!s}")


@router.get("/stats", response_model=VocabularyStats, name="get_vocabulary_stats")
async def get_vocabulary_stats_endpoint(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    service: VocabularyPreloadService = Depends(get_vocabulary_preload_service)
):
    """Get vocabulary statistics for the current user"""
    try:
        # Get basic stats from database
        db_stats = await service.get_vocabulary_stats(db)

        # Initialize default stats with CEFR levels
        stats = VocabularyStats(
            levels={
                "A1": {"total_words": 0, "user_known": 0},
                "A2": {"total_words": 0, "user_known": 0},
                "B1": {"total_words": 0, "user_known": 0},
                "B2": {"total_words": 0, "user_known": 0},
                "C1": {"total_words": 0, "user_known": 0},
                "C2": {"total_words": 0, "user_known": 0}
            },
            total_words=0,
            total_known=0
        )

        # Process each level
        total_words = 0
        total_known = 0

        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            # Get known words for this user and level
            known_words = await service.get_user_known_words(current_user.id, level, db)

            # Get total words for this level from database stats
            level_total = 0
            if level in db_stats:
                level_total = db_stats[level].get("total_words", 0)

            # Update level stats
            stats.levels[level] = {
                "total_words": level_total,
                "user_known": len(known_words)
            }

            total_words += level_total
            total_known += len(known_words)

        stats.total_words = total_words
        stats.total_known = total_known

        logger.info(f"Retrieved vocabulary stats for user {current_user.id}: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting vocabulary stats for user {current_user.id}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving vocabulary stats: {e!s}")


@router.get("/blocking-words", name="get_blocking_words")
async def get_blocking_words(
    video_path: str,
    segment_start: int = 0,
    segment_duration: int = 300,  # 5 minutes default
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get top blocking words for a video segment"""
    try:
        logger.info(f"Getting blocking words for user {current_user.id}, video: {video_path}")

        # Get subtitle file path - handle both relative and full paths
        if video_path.startswith('/'):
            video_file = Path(video_path)
        else:
            video_file = settings.get_videos_path() / video_path

        srt_file = video_file.with_suffix(".srt")

        # If subtitle file doesn't exist, raise error
        if not srt_file.exists():
            logger.error(f"Subtitle file not found: {srt_file}")
            raise HTTPException(status_code=404, detail="Subtitle file not found")

        # Extract blocking words for the specific segment
        blocking_words = await extract_blocking_words_for_segment(
            str(srt_file), segment_start, segment_duration, current_user.id, db
        )

        logger.info(f"Found {len(blocking_words)} blocking words for segment")
        return {"blocking_words": blocking_words[:10]}  # Return top 10

    except Exception as e:
        logger.error(f"Error in get_blocking_words: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get blocking words: {e!s}")


@router.post("/mark-known", name="mark_word_known")
async def mark_word_as_known(
    request: MarkKnownRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Mark a word as known or unknown"""
    try:
        logger.info(f"Marking word '{request.word}' as {'known' if request.known else 'unknown'} for user {current_user.id}")

        # Use the underlying SQLiteUserVocabularyService directly for simplicity
        from services.dataservice.user_vocabulary_service import (
            SQLiteUserVocabularyService,
        )
        vocab_service = SQLiteUserVocabularyService()

        if request.known:
            success = await vocab_service.mark_word_learned(str(current_user.id), request.word, "de")
        else:
            success = await vocab_service.remove_word(str(current_user.id), request.word, "de")

        logger.info(f"Successfully updated word status: {request.word} -> {request.known}")
        return {"success": success, "word": request.word, "known": request.known}

    except Exception as e:
        logger.error(f"Failed to update word: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update word: {e!s}")


@router.post("/preload", name="preload_vocabulary")
async def preload_vocabulary(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Preload vocabulary data from text files into database (Admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        service = VocabularyPreloadService()
        results = await service.load_vocabulary_files()

        total_loaded = sum(results.values())
        logger.info(f"Preloaded vocabulary: {results}")

        return {
            "success": True,
            "message": f"Loaded {total_loaded} words across all levels",
            "levels": results
        }

    except Exception as e:
        logger.error(f"Failed to preload vocabulary: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to preload vocabulary: {e!s}")


@router.get("/library/stats", name="get_library_stats")
async def get_vocabulary_stats(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    service: VocabularyPreloadService = Depends(get_vocabulary_preload_service)
):
    """Get vocabulary statistics for all levels"""
    try:
        # Get basic stats using the injected database session
        stats = await service.get_vocabulary_stats(db)

        # Add user-specific known word counts
        total_words = 0
        total_known = 0

        for level in ["A1", "A2", "B1", "B2"]:
            known_words = await service.get_user_known_words(current_user.id, level, db)
            if level in stats:
                stats[level]["user_known"] = len(known_words)
                total_words += stats[level]["total_words"]
                total_known += len(known_words)
            else:
                stats[level] = {"total_words": 0, "user_known": 0}

        return VocabularyStats(
            levels=stats,
            total_words=total_words,
            total_known=total_known
        )

    except Exception as e:
        logger.error(f"Failed to get vocabulary stats: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vocabulary stats: {e!s}")


@router.get("/library/{level}", name="get_vocabulary_level")
async def get_vocabulary_level(
    level: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all vocabulary words for a specific level with user's known status"""
    try:
        if level.upper() not in ["A1", "A2", "B1", "B2"]:
            raise HTTPException(status_code=422, detail="Invalid level. Must be A1, A2, B1, or B2")

        service = VocabularyPreloadService()

        # Get words for level
        level_words = await service.get_level_words(level.upper(), db)

        # Get user's known words for this level
        known_words = await service.get_user_known_words(current_user.id, level.upper(), db)

        # Combine data
        vocabulary_words = []
        known_count = 0

        for word_data in level_words:
            is_known = word_data.get("word", "") in known_words
            if is_known:
                known_count += 1

            vocabulary_words.append(VocabularyLibraryWord(
                id=word_data.get("id"),
                word=word_data.get("word", ""),
                difficulty_level=word_data.get("difficulty_level", level.upper()),
                part_of_speech=word_data.get("part_of_speech") or word_data.get("word_type", "noun"),
                definition=word_data.get("definition", ""),
                known=is_known
            ))

        return VocabularyLevel(
            level=level.upper(),
            words=vocabulary_words,
            total_count=len(vocabulary_words),
            known_count=known_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vocabulary level {level}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vocabulary level: {e!s}")


@router.post("/library/bulk-mark", name="bulk_mark_level")
async def bulk_mark_level_known(
    request: BulkMarkRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    service: VocabularyPreloadService = Depends(get_vocabulary_preload_service)
):
    """Mark all words in a level as known or unknown"""
    try:
        if request.level.upper() not in ["A1", "A2", "B1", "B2"]:
            raise HTTPException(status_code=400, detail="Invalid level. Must be A1, A2, B1, or B2")

        success_count = await service.bulk_mark_level_known(current_user.id, request.level.upper(), request.known, db)

        action = "marked as known" if request.known else "unmarked"
        return {
            "success": True,
            "message": f"Successfully {action} {success_count} words in {request.level.upper()}",
            "level": request.level.upper(),
            "known": request.known,
            "word_count": success_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk mark {request.level}: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to bulk mark words: {e!s}")
