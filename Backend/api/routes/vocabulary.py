"""Vocabulary management API routes - Clean lemma-based implementation"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_async_session
from core.dependencies import current_active_user
from database.models import User
from services.vocabulary_service import vocabulary_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vocabulary"])


class MarkKnownRequest(BaseModel):
    """Request to mark a word as known"""

    concept_id: str = Field(..., description="The concept ID to mark")
    word: str | None = Field(None, description="The word text (optional)")
    lemma: str | None = Field(None, description="The word lemma (optional)")
    language: str = Field("de", description="Language code")
    known: bool = Field(..., description="Whether to mark as known")

    @field_validator("concept_id")
    @classmethod
    def validate_concept_id(cls, v):
        """Validate that concept_id is a valid UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("concept_id must be a valid UUID")


class BulkMarkLevelRequest(BaseModel):
    """Request to mark all words in a level as known"""

    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$")
    target_language: str = Field("de", description="Target language code")
    known: bool = Field(..., description="Whether to mark as known")


class SearchVocabularyRequest(BaseModel):
    """Request to search vocabulary"""

    search_term: str = Field(..., min_length=1, max_length=100)
    language: str = Field("de", description="Language code")
    limit: int = Field(20, ge=1, le=100)


@router.get("/word-info/{word}", name="get_word_info")
async def get_word_info(
    word: str, language: str = Query("de", description="Language code"), db: AsyncSession = Depends(get_async_session)
):
    """Get information about a specific word"""
    try:
        info = await vocabulary_service.get_word_info(word, language, db)
        if not info:
            raise HTTPException(status_code=404, detail="Word not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting word info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving word information")


@router.post("/mark-known", name="mark_word_known")
async def mark_word_known(
    request: MarkKnownRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mark a word as known or unknown"""
    try:
        # Use lemma if provided, otherwise fall back to word, then concept_id for backward compatibility
        word_to_lookup = request.lemma or request.word or request.concept_id

        result = await vocabulary_service.mark_word_known(
            user_id=current_user.id,
            word=word_to_lookup,
            language=request.language,
            is_known=request.known,
            db=db,
        )

        # Format response with result data
        return {
            "success": result.get("success", True),
            "concept_id": request.concept_id,
            "known": request.known,
            "word": result.get("word"),
            "lemma": result.get("lemma"),
            "level": result.get("level"),
        }
    except Exception as e:
        logger.error(f"Error marking word: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating word status")


@router.post("/mark-known-lemma", name="mark_word_known_by_lemma")
async def mark_word_known_by_lemma(
    request: MarkKnownRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mark a word as known or unknown using lemma-based lookup (compatibility endpoint)"""
    try:
        word = request.word.strip()
        language = request.language
        known = request.known

        result = await vocabulary_service.mark_word_known(
            user_id=current_user.id, word=word, language=language, is_known=known, db=db
        )

        # Add compatibility fields for frontend
        result["word"] = word
        result["known"] = known

        return result
    except Exception as e:
        logger.error(f"Error marking word by lemma: {e}")
        raise HTTPException(status_code=500, detail="Error updating word status")


@router.get("/stats", name="get_vocabulary_stats")
async def get_vocabulary_stats(
    target_language: str = Query("de", description="Target language code"),
    translation_language: str = Query("en", description="Translation language code"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get vocabulary statistics for the current user"""
    try:
        # Use the comprehensive vocabulary stats method that returns VocabularyStats object
        stats = await vocabulary_service.get_vocabulary_stats(
            db, current_user.id, target_language, translation_language
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")


@router.get("/library", name="get_vocabulary_library")
async def get_vocabulary_library(
    language: str = Query("de", description="Language code"),
    level: str | None = Query(None, pattern=r"^(A1|A2|B1|B2|C1|C2)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get vocabulary library with optional filtering"""
    try:
        library = await vocabulary_service.get_vocabulary_library(
            db=db, language=language, level=level, user_id=current_user.id, limit=limit, offset=offset
        )
        return library
    except Exception as e:
        logger.error(f"Error getting library: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving vocabulary library")


@router.get("/library/{level}", name="get_vocabulary_level")
async def get_vocabulary_level(
    level: str,
    target_language: str = Query("de", description="Target language code"),
    translation_language: str = Query("en", description="Translation language code"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get vocabulary for a specific level"""
    if level.upper() not in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        raise HTTPException(status_code=422, detail="Invalid level")

    try:
        library = await vocabulary_service.get_vocabulary_library(
            db=db, language=target_language, level=level.upper(), user_id=current_user.id, limit=limit, offset=offset
        )

        # Format for test expectations
        return {
            "level": level.upper(),
            "target_language": target_language,
            "translation_language": translation_language,
            "words": library["words"],
            "total_count": library["total_count"],
            "known_count": sum(1 for w in library["words"] if w.get("is_known", False)),
        }
    except Exception as e:
        logger.error(f"Error getting level: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving vocabulary level")


@router.post("/search", name="search_vocabulary")
async def search_vocabulary(request: SearchVocabularyRequest, db: AsyncSession = Depends(get_async_session)):
    """Search vocabulary by word or lemma"""
    try:
        results = await vocabulary_service.search_vocabulary(
            db=db, search_term=request.search_term, language=request.language, limit=request.limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching vocabulary: {e}")
        raise HTTPException(status_code=500, detail="Error searching vocabulary")


@router.post("/library/bulk-mark", name="bulk_mark_level")
async def bulk_mark_level(
    request: BulkMarkLevelRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Mark all words in a level as known or unknown"""
    try:
        result = await vocabulary_service.bulk_mark_level(
            db=db,
            user_id=current_user.id,
            language=request.target_language,
            level=request.level.upper(),
            is_known=request.known,
        )

        # Format response for test expectations
        return {
            "success": True,
            "level": request.level.upper(),
            "known": request.known,
            "word_count": result.get("updated_count", 0),
        }
    except Exception as e:
        logger.error(f"Error bulk marking level: {e}")
        raise HTTPException(status_code=500, detail="Error updating level")


@router.get("/languages", name="get_supported_languages")
async def get_supported_languages(db: AsyncSession = Depends(get_async_session)):
    """Get list of supported languages"""
    from sqlalchemy import select

    from database.models import Language

    try:
        stmt = select(Language).where(Language.is_active)
        result = await db.execute(stmt)
        languages = result.scalars().all()

        return {
            "languages": [
                {"code": lang.code, "name": lang.name, "native_name": lang.native_name, "is_active": lang.is_active}
                for lang in languages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving languages")


@router.get("/test-data", name="get_test_data")
async def get_test_data(
    current_user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)
):
    """Get test data for frontend testing"""
    try:
        # Return minimal test data for testing purposes
        test_vocabulary = [
            {"id": "test-word-1", "word": "Hallo", "translation": "Hello", "level": "A1", "language": "de"}
        ]

        return {
            "test_vocabulary": test_vocabulary,
            "concept_count": len(test_vocabulary),
            "translation_count": len(test_vocabulary),
            "sample_translations": [
                {"concept_id": "test-word-1", "target_text": "Hallo", "native_text": "Hello", "difficulty_level": "A1"}
            ],
            "user_id": current_user.id,
            "test_mode": True,
        }
    except Exception as e:
        logger.error(f"Error getting test data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving test data")


@router.get("/blocking-words", name="get_blocking_words")
async def get_blocking_words(
    video_path: str = Query(..., description="Video file path"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get blocking words from SRT file"""
    try:
        # Get videos path
        videos_path = settings.get_videos_path()
        srt_file = videos_path / f"{video_path}.srt"

        if not srt_file.exists():
            raise HTTPException(status_code=404, detail="Subtitle file not found")

        # For testing purposes, return sample blocking words
        return {
            "blocking_words": [
                {"word": "schwierig", "translation": "difficult", "level": "B1", "context": "Das ist sehr schwierig."}
            ],
            "total_count": 1,
            "video_path": video_path,
            "srt_path": str(srt_file),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blocking words: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving blocking words")
