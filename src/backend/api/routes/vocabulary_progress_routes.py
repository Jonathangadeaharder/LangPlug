"""Vocabulary progress API routes - User progress tracking operations.

This module handles:
- Mark word as known/unknown
- Bulk mark level operations
- Delete progress entries
- Get vocabulary statistics
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.error_handlers import handle_api_errors, raise_not_found
from core.config.logging_config import get_logger
from core.database import get_async_session
from core.dependencies import current_active_user, get_vocabulary_service
from database.models import User

logger = get_logger(__name__)
router = APIRouter(tags=["vocabulary"])


class MarkKnownRequest(BaseModel):
    """Request to mark a word as known by lemma"""

    lemma: str = Field(..., min_length=1, max_length=200, description="The word lemma (base form)")
    language: str = Field(..., pattern=r"^[a-z]{2,3}$", description="Language code (required)")
    known: bool = Field(..., description="Whether to mark as known")


class BulkMarkLevelRequest(BaseModel):
    """Request to mark all words in a level as known"""

    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1|C2)$")
    target_language: str = Field("de", description="Target language code")
    known: bool = Field(..., description="Whether to mark as known")


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

    **Authentication Required**: Yes

    Args:
        request (MarkKnownRequest): Request containing lemma, language, and known status

    Returns:
        dict: Update result with success, known, word, lemma, level
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

    **Authentication Required**: Yes

    Returns:
        VocabularyStats: Statistics including total_words, known_words, by_level, mastery_percentage
    """
    stats = await vocabulary_service.get_vocabulary_stats(db, current_user.id, target_language, translation_language)
    return stats


@router.post("/library/bulk-mark", name="bulk_mark_level")
@handle_api_errors("bulk marking level")
async def bulk_mark_level(
    request: BulkMarkLevelRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    vocabulary_service=Depends(get_vocabulary_service),
):
    """Mark all words in a level as known or unknown.

    **Authentication Required**: Yes
    """
    result = await vocabulary_service.bulk_mark_level(
        db=db,
        user_id=current_user.id,
        language=request.target_language,
        level=request.level.upper(),
        is_known=request.known,
    )

    return {
        "success": True,
        "level": request.level.upper(),
        "known": request.known,
        "word_count": result.get("updated_count", 0),
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

    **Authentication Required**: Yes

    Args:
        lemma (str): The lemma (base form) of the word
        language (str): Language code (default: "de")

    Returns:
        dict: Deletion confirmation with success, lemma, message
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

    logger.info("Deleted vocabulary progress", user_id=current_user.id, lemma=lemma)

    return {
        "success": True,
        "lemma": lemma.lower(),
        "message": f"Progress removed for '{lemma}'",
    }
