"""
Vocabulary management API routes
"""
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..models.vocabulary import (
    VocabularyWord, MarkKnownRequest, VocabularyLibraryWord, 
    VocabularyLevel, BulkMarkRequest, VocabularyStats
)
from core.dependencies import get_current_user, get_database_manager
from core.config import settings
from services.authservice.auth_service import AuthUser
from services.vocabulary_preload_service import VocabularyPreloadService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


async def extract_blocking_words_for_segment(
    srt_path: str, start: int, duration: int, user_id: int
) -> List[VocabularyWord]:
    """Extract blocking words from a specific time segment"""
    try:
        # This is a simplified implementation
        # In practice, you'd parse the SRT file, extract text for the time range,
        # and analyze vocabulary difficulty
        
        # Mock implementation - replace with actual SRT parsing
        # Different mock words based on segment for variety
        mock_word_sets = [
            [
                VocabularyWord(word="schwierig", difficulty_level="B2", known=False),
                VocabularyWord(word="verstehen", difficulty_level="A2", known=False),
                VocabularyWord(word="kompliziert", difficulty_level="B1", known=False),
            ],
            [
                VocabularyWord(word="aufregend", difficulty_level="B1", known=False),
                VocabularyWord(word="beeindruckend", difficulty_level="B2", known=False),
                VocabularyWord(word="überraschen", difficulty_level="A2", known=False),
            ],
            [
                VocabularyWord(word="entwickeln", difficulty_level="B1", known=False),
                VocabularyWord(word="entscheiden", difficulty_level="A2", known=False),
                VocabularyWord(word="gesellschaft", difficulty_level="B2", known=False),
            ]
        ]
        
        # Use start time to select different word sets
        word_set_index = (start // 300) % len(mock_word_sets)
        return mock_word_sets[word_set_index]
        
    except Exception as e:
        logger.error(f"Error in extract_blocking_words_for_segment: {str(e)}", exc_info=True)
        # Return basic fallback words if there's any error
        return [
            VocabularyWord(word="deutsch", difficulty_level="A1", known=False),
            VocabularyWord(word="lernen", difficulty_level="A1", known=False),
            VocabularyWord(word="sprache", difficulty_level="A2", known=False),
        ]


@router.get("/blocking-words")
async def get_blocking_words(
    video_path: str,
    segment_start: int = 0,
    segment_duration: int = 300,  # 5 minutes default
    current_user: AuthUser = Depends(get_current_user)
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
        
        # If subtitle file doesn't exist, return mock data for now
        if not srt_file.exists():
            logger.warning(f"Subtitle file not found: {srt_file}, returning mock data")
            # Return mock blocking words when subtitles aren't ready
            blocking_words = await extract_blocking_words_for_segment(
                "", segment_start, segment_duration, current_user.id
            )
            return {"blocking_words": blocking_words[:10]}
        
        # Extract blocking words for the specific segment
        blocking_words = await extract_blocking_words_for_segment(
            str(srt_file), segment_start, segment_duration, current_user.id
        )
        
        logger.info(f"Found {len(blocking_words)} blocking words for segment")
        return {"blocking_words": blocking_words[:10]}  # Return top 10
        
    except Exception as e:
        logger.error(f"Error in get_blocking_words: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get blocking words: {str(e)}")


@router.post("/mark-known")
async def mark_word_as_known(
    request: MarkKnownRequest,
    current_user: AuthUser = Depends(get_current_user),
    db_manager = Depends(get_database_manager)
):
    """Mark a word as known or unknown"""
    try:
        logger.info(f"Marking word '{request.word}' as {'known' if request.known else 'unknown'} for user {current_user.id}")
        
        # Use the underlying SQLiteUserVocabularyService directly for simplicity
        from services.dataservice.user_vocabulary_service import SQLiteUserVocabularyService
        vocab_service = SQLiteUserVocabularyService(db_manager)
        
        if request.known:
            success = vocab_service.mark_word_learned(str(current_user.id), request.word, "de")
        else:
            success = vocab_service.remove_word(str(current_user.id), request.word, "de")
        
        logger.info(f"Successfully updated word status: {request.word} -> {request.known}")
        return {"success": success, "word": request.word, "known": request.known}
        
    except Exception as e:
        logger.error(f"Failed to update word: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update word: {str(e)}")


@router.post("/preload")
async def preload_vocabulary(
    current_user: AuthUser = Depends(get_current_user),
    db_manager = Depends(get_database_manager)
):
    """Preload vocabulary data from text files into database (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        service = VocabularyPreloadService(db_manager)
        results = service.load_vocabulary_files()
        
        total_loaded = sum(results.values())
        logger.info(f"Preloaded vocabulary: {results}")
        
        return {
            "success": True,
            "message": f"Loaded {total_loaded} words across all levels",
            "levels": results
        }
        
    except Exception as e:
        logger.error(f"Failed to preload vocabulary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to preload vocabulary: {str(e)}")


@router.get("/library/stats")
async def get_vocabulary_stats(
    current_user: AuthUser = Depends(get_current_user),
    db_manager = Depends(get_database_manager)
):
    """Get vocabulary statistics for all levels"""
    try:
        service = VocabularyPreloadService(db_manager)
        
        # Get basic stats
        stats = service.get_vocabulary_stats()
        
        # Add user-specific known word counts
        total_words = 0
        total_known = 0
        
        for level in ["A1", "A2", "B1", "B2"]:
            known_words = service.get_user_known_words(current_user.id, level)
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
        logger.error(f"Failed to get vocabulary stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vocabulary stats: {str(e)}")


@router.get("/library/{level}")
async def get_vocabulary_level(
    level: str,
    current_user: AuthUser = Depends(get_current_user),
    db_manager = Depends(get_database_manager)
):
    """Get all vocabulary words for a specific level with user's known status"""
    try:
        if level.upper() not in ["A1", "A2", "B1", "B2"]:
            raise HTTPException(status_code=400, detail="Invalid level. Must be A1, A2, B1, or B2")
        
        service = VocabularyPreloadService(db_manager)
        
        # Get words for level
        level_words = service.get_level_words(level.upper())
        
        # Get user's known words for this level
        known_words = service.get_user_known_words(current_user.id, level.upper())
        
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
        logger.error(f"Failed to get vocabulary level {level}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vocabulary level: {str(e)}")


@router.post("/library/bulk-mark")
async def bulk_mark_level_known(
    request: BulkMarkRequest,
    current_user: AuthUser = Depends(get_current_user),
    db_manager = Depends(get_database_manager)
):
    """Mark all words in a level as known or unknown"""
    try:
        if request.level.upper() not in ["A1", "A2", "B1", "B2"]:
            raise HTTPException(status_code=400, detail="Invalid level. Must be A1, A2, B1, or B2")
        
        service = VocabularyPreloadService(db_manager)
        success_count = service.bulk_mark_level_known(current_user.id, request.level.upper(), request.known)
        
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
        logger.error(f"Failed to bulk mark {request.level}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to bulk mark words: {str(e)}")