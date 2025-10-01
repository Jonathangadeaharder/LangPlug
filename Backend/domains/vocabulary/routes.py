"""
Vocabulary domain routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from core.database_session import get_db
from core.exceptions import ValidationError
from core.service_container import get_auth_service, get_vocabulary_service
from domains.auth.services import AuthenticationService

from .models import (
    BulkMarkWordsRequest,
    MarkWordRequest,
    UserVocabularyProgressResponse,
    VocabularyStatsResponse,
    VocabularyWordResponse,
)
from .services import VocabularyService

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])
security = HTTPBearer()


async def get_current_user_id(
    db: Session = Depends(get_db),
    auth_service: AuthenticationService = Depends(get_auth_service),
    token: str = Depends(security),
):
    """Dependency to get current user ID"""
    user = await auth_service.get_current_user(db, token.credentials)
    return user.id


@router.get("/search", response_model=list[VocabularyWordResponse])
async def search_vocabulary(
    query: str = Query(..., min_length=1),
    language: str = Query("de", regex="^[a-z]{2}$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Search vocabulary words"""
    try:
        return await vocab_service.search_words(db, query, language, limit)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed")


@router.get("/level/{level}", response_model=list[VocabularyWordResponse])
async def get_words_by_level(
    level: str,
    language: str = Query("de", regex="^[a-z]{2}$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Get vocabulary words by difficulty level"""
    try:
        return await vocab_service.get_words_by_level(db, level, language, skip, limit)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch words")


@router.get("/random", response_model=list[VocabularyWordResponse])
async def get_random_words(
    language: str = Query("de", regex="^[a-z]{2}$"),
    levels: list[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Get random vocabulary words"""
    try:
        return await vocab_service.get_random_words(db, language, levels, limit)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch random words")


@router.post("/mark", response_model=UserVocabularyProgressResponse)
async def mark_word_known(
    request: MarkWordRequest,
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Mark word as known/unknown for current user"""
    try:
        return await vocab_service.mark_word_known(db, user_id, request)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark word")


@router.post("/mark-bulk", response_model=list[UserVocabularyProgressResponse])
async def bulk_mark_words(
    request: BulkMarkWordsRequest,
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Bulk mark multiple words as known/unknown"""
    try:
        return await vocab_service.bulk_mark_words(db, user_id, request)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to bulk mark words")


@router.get("/progress", response_model=list[UserVocabularyProgressResponse])
async def get_user_progress(
    language: str = Query("de", regex="^[a-z]{2}$"),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Get user's vocabulary progress"""
    try:
        return await vocab_service.get_user_progress(db, user_id, language)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch progress")


@router.get("/known", response_model=list[UserVocabularyProgressResponse])
async def get_known_words(
    language: str = Query("de", regex="^[a-z]{2}$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Get user's known words"""
    try:
        return await vocab_service.get_user_known_words(db, user_id, language, skip, limit)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch known words")


@router.get("/stats", response_model=VocabularyStatsResponse)
async def get_vocabulary_stats(
    language: str = Query("de", regex="^[a-z]{2}$"),
    db: Session = Depends(get_db),
    vocab_service: VocabularyService = Depends(get_vocabulary_service),
    user_id: int = Depends(get_current_user_id),
):
    """Get vocabulary statistics for user"""
    try:
        return await vocab_service.get_vocabulary_stats(db, user_id, language)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch statistics")
