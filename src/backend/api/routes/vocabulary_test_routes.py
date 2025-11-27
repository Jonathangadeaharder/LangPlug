"""Vocabulary test API routes - Endpoints for E2E testing.

This module handles:
- Get test data for frontend testing
- Create test vocabulary entries
- Get blocking words from SRT files

Note: These endpoints are primarily for E2E testing purposes.
In production, consider restricting access or removing these endpoints.
"""

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.error_handlers import handle_api_errors, raise_not_found
from core.config import settings
from core.database import get_async_session
from core.dependencies import current_active_user, get_vocabulary_service
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vocabulary-test"])


class CreateVocabularyRequest(BaseModel):
    """Request to create test vocabulary (for E2E tests)"""

    word: str = Field(..., min_length=1, max_length=100, description="The vocabulary word")
    translation: str = Field(..., min_length=1, max_length=200, description="Translation of the word")
    difficulty_level: str = Field("beginner", description="Difficulty level (beginner/intermediate/advanced)")
    language: str = Field("de", description="Language code")


@router.get("/test-data", name="get_test_data")
@handle_api_errors("retrieving test data")
async def get_test_data(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get test data for frontend testing.

    **Authentication Required**: Yes
    """
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


@router.get("/blocking-words", name="get_blocking_words")
@handle_api_errors("retrieving blocking words")
async def get_blocking_words(
    video_path: str = Query(..., description="Video file path"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Get blocking words from SRT file.

    **Authentication Required**: Yes
    """
    videos_path = settings.get_videos_path()
    srt_file = videos_path / f"{video_path}.srt"

    if not srt_file.exists():
        raise_not_found("Subtitle file", video_path)

    with open(srt_file, encoding="utf-8") as f:
        srt_content = f.read()

    blocking_words = await vocabulary_service.extract_blocking_words_from_srt(
        db=db, srt_content=srt_content, user_id=current_user.id, video_path=video_path
    )

    return {
        "blocking_words": blocking_words,
        "total_count": len(blocking_words),
        "video_path": video_path,
        "srt_path": str(srt_file),
    }


@router.post("/create", name="create_vocabulary")
@handle_api_errors("creating vocabulary", status_code=400)
async def create_vocabulary(
    request: CreateVocabularyRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create test vocabulary word (primarily for E2E testing).

    Maps difficulty levels to CEFR levels and creates a global vocabulary word.

    **Authentication Required**: Yes
    """
    from sqlalchemy import select

    from database.models import VocabularyWord

    # Map difficulty level to CEFR level for storage
    difficulty_to_level = {"beginner": "A1", "intermediate": "B1", "advanced": "C1"}
    cefr_level = difficulty_to_level.get(request.difficulty_level.lower(), "A1")

    # Check if word already exists
    result = await db.execute(
        select(VocabularyWord).where(
            VocabularyWord.word == request.word, VocabularyWord.language == request.language
        )
    )
    existing_word = result.scalar_one_or_none()

    if existing_word:
        return {
            "id": existing_word.id,
            "word": existing_word.word,
            "translation": request.translation,
            "difficulty_level": request.difficulty_level,
            "language": existing_word.language,
        }

    # Create new global vocabulary word (no user_id - shared vocabulary)
    new_word = VocabularyWord(
        word=request.word,
        lemma=request.word.lower(),
        language=request.language,
        difficulty_level=cefr_level,
        translation_en=request.translation,
        translation_native=request.translation,
        notes=f"E2E test vocabulary - {cefr_level}",
    )

    db.add(new_word)
    await db.commit()

    logger.info(f"Created test vocabulary for E2E: {request.word} ({cefr_level})")
    return {
        "id": new_word.id,
        "word": new_word.word,
        "translation": request.translation,
        "difficulty_level": request.difficulty_level,
        "language": new_word.language,
    }
