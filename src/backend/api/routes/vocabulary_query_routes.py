"""Vocabulary query API routes - Read operations for vocabulary data.

This module handles:
- Word info lookup
- Vocabulary library browsing
- Vocabulary search
- Supported languages listing
"""

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.constants import (
    DEFAULT_VOCABULARY_LIMIT,
    MAX_SEARCH_LENGTH,
    MAX_VOCABULARY_LIMIT,
    MIN_SEARCH_LENGTH,
)
from api.error_handlers import handle_api_errors, raise_not_found, raise_validation_error
from core.database import get_async_session
from core.dependencies import current_active_user, get_vocabulary_service
from core.enums import CEFRLevel
from database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["vocabulary"])


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
        dict: Word information including word, lemma, level, translations, examples

    Raises:
        HTTPException: 404 if word not found in vocabulary database
    """
    info = await vocabulary_service.get_word_info(word, language, db)
    if not info:
        raise_not_found("Word", word)
    return info


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

    **Authentication Required**: Yes

    Args:
        language (str): Target language code (default: "de")
        level (str, optional): CEFR level filter (A1, A2, B1, B2, C1, C2)
        limit (int): Maximum words to return (1-1000, default: 100)
        offset (int): Pagination offset (default: 0)

    Returns:
        dict: Library data with words, total_count, limit, offset
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
    """Get vocabulary for a specific CEFR level.

    **Authentication Required**: Yes
    """
    if level.upper() not in CEFRLevel.all_levels():
        raise_validation_error(f"Invalid level. Must be one of {CEFRLevel.all_levels()}", "level")

    library = await vocabulary_service.get_vocabulary_library(
        db=db, language=target_language, level=level.upper(), user_id=current_user.id, limit=limit, offset=offset
    )

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
    """Search vocabulary by word or lemma.

    **Authentication Required**: No
    """
    results = await vocabulary_service.search_vocabulary(
        db=db, search_term=request.search_term, language=request.language, limit=request.limit
    )
    return {"results": results, "count": len(results)}


@router.get("/languages", name="get_supported_languages")
@handle_api_errors("retrieving supported languages")
async def get_supported_languages(db: AsyncSession = Depends(get_async_session)):
    """Get list of supported languages.

    **Authentication Required**: No
    """
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
