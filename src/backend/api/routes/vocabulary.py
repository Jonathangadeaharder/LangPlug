"""Vocabulary management API routes - Clean lemma-based implementation"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.constants import (
    DEFAULT_VOCABULARY_LIMIT,
    MAX_VOCABULARY_LIMIT,
    MIN_SEARCH_LENGTH,
    MAX_SEARCH_LENGTH,
)
from api.error_handlers import (
    handle_api_errors,
    raise_not_found,
    raise_validation_error,
)
from core.config import settings
from core.database import get_async_session
from core.dependencies import current_active_user
from core.enums import CEFRLevel
from core.service_dependencies import get_vocabulary_service
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vocabulary"])


class MarkKnownRequest(BaseModel):
    """Request to mark a word as known by lemma"""

    lemma: str = Field(..., min_length=1, max_length=200, description="The word lemma (base form)")
    language: str = Field(..., pattern=r"^[a-z]{2,3}$", description="Language code (required, e.g. 'de', 'en')")
    known: bool = Field(..., description="Whether to mark as known")


class BulkMarkLevelRequest(BaseModel):
    """Request to mark all words in a level as known"""

    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$")
    target_language: str = Field("de", description="Target language code")
    known: bool = Field(..., description="Whether to mark as known")


class SearchVocabularyRequest(BaseModel):
    """Request to search vocabulary"""

    search_term: str = Field(..., min_length=MIN_SEARCH_LENGTH, max_length=MAX_SEARCH_LENGTH)
    language: str = Field("de", description="Language code")
    limit: int = Field(DEFAULT_VOCABULARY_LIMIT, ge=1, le=MAX_VOCABULARY_LIMIT)


@router.get("/word-info/{word}", name="get_word_info")
@handle_api_errors("retrieving word information")
async def get_word_info(
    word: str,
    language: str = Query("de", description="Language code"),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """
    Retrieve detailed information about a specific vocabulary word.

    Looks up word metadata including lemma, CEFR level, translations, and usage examples
    from the vocabulary database.

    **Authentication Required**: No

    Args:
        word (str): The word to look up
        language (str): Target language code (default: "de")
        db (AsyncSession): Database session dependency

    Returns:
        dict: Word information including:
            - word: The original word
            - lemma: Base form of the word
            - level: CEFR level (A1-C2)
            - translations: List of translations
            - examples: Usage examples

    Raises:
        HTTPException: 404 if word not found in vocabulary database
        HTTPException: 500 if database query fails

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/vocabulary/word-info/Hallo?language=de"
        ```

        Response:
        ```json
        {
            "word": "Hallo",
            "lemma": "hallo",
            "level": "A1",
            "translations": ["Hello", "Hi"],
            "examples": ["Hallo, wie geht es dir?"]
        }
        ```
    """
    info = await vocabulary_service.get_word_info(word, language, db)
    if not info:
        raise_not_found("Word", word)
    return info


@router.post("/mark-known", name="mark_word_known")
@handle_api_errors("marking word as known/unknown")
async def mark_word_known(
    request: MarkKnownRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """
    Mark a vocabulary word as known or unknown for the current user.

    Updates user's vocabulary progress by marking a word as known (mastered)
    or unknown (needs practice) using the lemma (base form) of the word.

    **Authentication Required**: Yes

    Args:
        request (MarkKnownRequest): Request containing:
            - lemma (str): Base form of the word
            - language (str): Language code (default: "de")
            - known (bool): Whether to mark as known
        current_user (User): Authenticated user
        db (AsyncSession): Database session

    Returns:
        dict: Update result with:
            - success: Whether operation succeeded
            - known: The new known status
            - word: The word text
            - lemma: The word lemma
            - level: CEFR level

    Raises:
        HTTPException: 500 if database update fails

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/vocabulary/mark-known" \
          -H "Authorization: Bearer <token>" \
          -H "Content-Type: application/json" \
          -d '{
            "lemma": "hallo",
            "language": "de",
            "known": true
          }'
        ```

        Response:
        ```json
        {
            "success": true,
            "known": true,
            "word": "Hallo",
            "lemma": "hallo",
            "level": "A1"
        }
        ```
    """
    result = await vocabulary_service.mark_word_known(
        user_id=current_user.id,
        word=request.lemma,
        language=request.language,
        is_known=request.known,
        db=db,
    )

    response = {
        "success": result.get("success", True),
        "known": request.known,
        "word": result.get("word"),
        "lemma": result.get("lemma"),
        "level": result.get("level"),
    }
    if result.get("message"):
        response["message"] = result["message"]
    return response


@router.get("/stats", name="get_vocabulary_stats")
@handle_api_errors("retrieving vocabulary statistics")
async def get_vocabulary_stats(
    target_language: str = Query("de", pattern=r"^[a-z]{2,3}$", description="Target language code"),
    translation_language: str = Query("en", pattern=r"^[a-z]{2,3}$", description="Translation language code"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """
    Get comprehensive vocabulary learning statistics for the current user.

    Returns detailed progress metrics including known/unknown word counts by CEFR level,
    learning streaks, and overall proficiency metrics.

    **Authentication Required**: Yes

    Args:
        target_language (str): Target language code (default: "de")
        translation_language (str): Translation language code (default: "en")
        current_user (User): Authenticated user
        db (AsyncSession): Database session

    Returns:
        VocabularyStats: Statistics including:
            - total_words: Total vocabulary size
            - known_words: Number of mastered words
            - by_level: Breakdown by CEFR level (A1-C2)
            - learning_streak: Consecutive days of practice
            - mastery_percentage: Overall proficiency score

    Raises:
        HTTPException: 500 if statistics calculation fails

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/vocabulary/stats?target_language=de&translation_language=en" \
          -H "Authorization: Bearer <token>"
        ```

        Response:
        ```json
        {
            "total_words": 5000,
            "known_words": 450,
            "by_level": {
                "A1": {"total": 600, "known": 200},
                "A2": {"total": 800, "known": 150},
                "B1": {"total": 1000, "known": 100}
            },
            "mastery_percentage": 9.0
        }
        ```
    """
    # Use the comprehensive vocabulary stats method that returns VocabularyStats object
    stats = await vocabulary_service.get_vocabulary_stats(
        db, current_user.id, target_language, translation_language
    )
    return stats


@router.get("/library", name="get_vocabulary_library")
@handle_api_errors("retrieving vocabulary library")
async def get_vocabulary_library(
    language: str = Query("de", description="Language code"),
    level: str | None = Query(None, pattern=r"^(A1|A2|B1|B2|C1|C2)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """
    Retrieve paginated vocabulary library with optional CEFR level filtering.

    Returns a paginated list of vocabulary words, optionally filtered by CEFR level,
    with user-specific progress indicators showing which words are known.

    **Authentication Required**: Yes

    Args:
        language (str): Target language code (default: "de")
        level (str, optional): CEFR level filter (A1, A2, B1, B2, C1, C2)
        limit (int): Maximum words to return (1-1000, default: 100)
        offset (int): Pagination offset (default: 0)
        current_user (User): Authenticated user
        db (AsyncSession): Database session

    Returns:
        dict: Library data with:
            - words: List of vocabulary entries with known status
            - total_count: Total matching words
            - limit: Applied limit
            - offset: Applied offset

    Raises:
        HTTPException: 500 if database query fails

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/vocabulary/library?level=A1&limit=50" \
          -H "Authorization: Bearer <token>"
        ```

        Response:
        ```json
        {
            "words": [
                {
                    "lemma": "hallo",
                    "translation": "hello",
                    "level": "A1",
                    "is_known": true
                }
            ],
            "total_count": 600,
            "limit": 50,
            "offset": 0
        }
        ```
    """
    library = await vocabulary_service.get_vocabulary_library(
        db=db, language=language, level=level, user_id=current_user.id, limit=limit, offset=offset
    )
    return library


@router.get("/library/{level}", name="get_vocabulary_level")
@handle_api_errors("retrieving vocabulary level")
async def get_vocabulary_level(
    level: str,
    target_language: str = Query("de", description="Target language code"),
    translation_language: str = Query("en", description="Translation language code"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Get vocabulary for a specific level"""
    if level.upper() not in CEFRLevel.all_levels():
        raise_validation_error(f"Invalid level. Must be one of {CEFRLevel.all_levels()}", "level")

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


@router.post("/search", name="search_vocabulary")
@handle_api_errors("searching vocabulary")
async def search_vocabulary(
    request: SearchVocabularyRequest,
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Search vocabulary by word or lemma"""
    results = await vocabulary_service.search_vocabulary(
        db=db, search_term=request.search_term, language=request.language, limit=request.limit
    )
    return {"results": results, "count": len(results)}


@router.post("/library/bulk-mark", name="bulk_mark_level")
@handle_api_errors("bulk marking level")
async def bulk_mark_level(
    request: BulkMarkLevelRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Mark all words in a level as known or unknown"""
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


@router.get("/languages", name="get_supported_languages")
@handle_api_errors("retrieving supported languages")
async def get_supported_languages(db: AsyncSession = Depends(get_async_session)):
    """Get list of supported languages"""
    from sqlalchemy import select

    from database.models import Language

    stmt = select(Language).where(Language.is_active)
    result = await db.execute(stmt)
    languages = result.scalars().all()

    return {
        "languages": [
            {"code": lang.code, "name": lang.name, "native_name": lang.native_name, "is_active": lang.is_active}
            for lang in languages
        ]
    }


@router.get("/test-data", name="get_test_data")
@handle_api_errors("retrieving test data")
async def get_test_data(
    current_user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)
):
    """Get test data for frontend testing"""
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


@router.get("/blocking-words", name="get_blocking_words")
@handle_api_errors("retrieving blocking words")
async def get_blocking_words(
    video_path: str = Query(..., description="Video file path"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Get blocking words from SRT file"""
    # Get videos path
    videos_path = settings.get_videos_path()
    srt_file = videos_path / f"{video_path}.srt"

    if not srt_file.exists():
        raise_not_found("Subtitle file", video_path)

    # Read SRT file content
    with open(srt_file, encoding="utf-8") as f:
        srt_content = f.read()

    # Extract blocking words from SRT content
    blocking_words = await vocabulary_service.extract_blocking_words_from_srt(
        db=db, srt_content=srt_content, user_id=current_user.id, video_path=video_path
    )

    return {
        "blocking_words": blocking_words,
        "total_count": len(blocking_words),
        "video_path": video_path,
        "srt_path": str(srt_file),
    }


class CreateVocabularyRequest(BaseModel):
    """Request to create test vocabulary (for E2E tests)"""

    word: str = Field(..., min_length=1, max_length=100, description="The vocabulary word")
    translation: str = Field(..., min_length=1, max_length=200, description="Translation of the word")
    difficulty_level: str = Field("beginner", description="Difficulty level (beginner/intermediate/advanced)")
    language: str = Field("de", description="Language code")


@router.post("", name="create_vocabulary")
@handle_api_errors("creating vocabulary", status_code=400)
async def create_vocabulary(
    request: CreateVocabularyRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create test vocabulary word (primarily for E2E testing).

    Maps difficulty levels to CEFR levels and creates a global vocabulary word.

    Args:
        request: Vocabulary word details
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Created vocabulary with id, word, translation, difficulty_level

    Raises:
        HTTPException: 400 if creation fails
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
        # Return existing word
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


@router.delete("/progress/{lemma}", name="delete_vocabulary_progress")
@handle_api_errors("deleting vocabulary progress")
async def delete_vocabulary_progress(
    lemma: str,
    language: str = Query("de", description="Language code"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete user progress for a specific word (reset to unknown).

    Removes the user's progress entry for a word, effectively resetting it to "unknown" status.
    This is useful for testing and for users who want to re-learn a word.

    **Authentication Required**: Yes

    Args:
        lemma (str): The lemma (base form) of the word
        language (str): Language code (default: "de")
        current_user (User): Authenticated user
        db (AsyncSession): Database session dependency

    Returns:
        dict: Deletion confirmation with:
            - success: True if deleted
            - lemma: The lemma that was removed
            - message: Confirmation message

    Raises:
        HTTPException: 404 if no progress entry exists for this word
        HTTPException: 500 if database operation fails

    Example:
        ```bash
        curl -X DELETE "http://localhost:8000/api/vocabulary/progress/hallo?language=de" \
          -H "Authorization: Bearer <token>"
        ```

        Response:
        ```json
        {
            "success": true,
            "lemma": "hallo",
            "message": "Progress removed for 'hallo'"
        }
        ```

    Note:
        This only removes the user's progress entry. The word itself remains in
        the global vocabulary database. After deletion, the word will appear as
        "unknown" to the user.
    """
    from sqlalchemy import and_, delete, select

    from database.models import UserVocabularyProgress

    # First check if progress entry exists
    stmt = select(UserVocabularyProgress).where(
        and_(
            UserVocabularyProgress.user_id == current_user.id,
            UserVocabularyProgress.lemma == lemma.lower(),
            UserVocabularyProgress.language == language,
        )
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()

    if not progress:
        raise_not_found("Progress entry", f"lemma '{lemma}' in language '{language}'")

    # Delete the progress entry
    delete_stmt = delete(UserVocabularyProgress).where(
        and_(
            UserVocabularyProgress.user_id == current_user.id,
            UserVocabularyProgress.lemma == lemma.lower(),
            UserVocabularyProgress.language == language,
        )
    )
    await db.execute(delete_stmt)
    await db.commit()

    logger.info(f"Deleted vocabulary progress for user {current_user.id}, lemma '{lemma}'")

    return {
        "success": True,
        "lemma": lemma.lower(),
        "message": f"Progress removed for '{lemma}'",
    }
