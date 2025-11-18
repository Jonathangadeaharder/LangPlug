"""
Repository Dependency Injection

Provides FastAPI dependency functions for repository interfaces following
the Dependency Inversion Principle. High-level services depend on repository
abstractions rather than concrete implementations.

Usage Example:
    ```python
    from fastapi import APIRouter, Depends
    from database.repositories.interfaces import UserRepositoryInterface
    from core.repository_dependencies import get_user_repository

    @router.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        user_repo: UserRepositoryInterface = Depends(get_user_repository)
    ):
        user = await user_repo.get_by_id(user_id)
        return user
    ```

Architecture Benefits:
    - Services depend on interfaces, not concrete implementations
    - Easy to swap implementations (e.g., for testing or different data sources)
    - Clear separation between domain logic and data access
    - Better testability with mock repositories
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.interfaces import (
    ProcessingSessionRepositoryInterface,
    UserRepositoryInterface,
    UserVocabularyProgressRepositoryInterface,
    VocabularyRepositoryInterface,
)
from database.repositories.processing_session_repository import ProcessingSessionRepository
from database.repositories.user_repository import UserRepository
from database.repositories.user_vocabulary_progress_repository import UserVocabularyProgressRepository
from database.repositories.vocabulary_repository import VocabularyRepository

from .database import get_async_session


def get_user_repository(db: Annotated[AsyncSession, Depends(get_async_session)]) -> UserRepositoryInterface:
    """
    Get user repository instance

    Args:
        db: Database session from dependency injection

    Returns:
        UserRepositoryInterface: User repository implementation

    Example:
        ```python
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            user_repo: UserRepositoryInterface = Depends(get_user_repository)
        ):
            return await user_repo.get_by_id(user_id)
        ```
    """
    return UserRepository(db)  # type: ignore[return-value]


def get_vocabulary_repository(db: Annotated[AsyncSession, Depends(get_async_session)]) -> VocabularyRepositoryInterface:
    """
    Get vocabulary repository instance

    Args:
        db: Database session from dependency injection

    Returns:
        VocabularyRepositoryInterface: Vocabulary repository implementation

    Example:
        ```python
        @router.get("/vocabulary/level/{level}")
        async def get_vocabulary_level(
            level: str,
            vocab_repo: VocabularyRepositoryInterface = Depends(get_vocabulary_repository)
        ):
            return await vocab_repo.get_by_difficulty_level(level)
        ```
    """
    return VocabularyRepository(db)  # type: ignore[abstract]


def get_user_vocabulary_progress_repository(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserVocabularyProgressRepositoryInterface:
    """
    Get user vocabulary progress repository instance

    Args:
        db: Database session from dependency injection

    Returns:
        UserVocabularyProgressRepositoryInterface: Progress repository implementation

    Example:
        ```python
        @router.get("/progress/{user_id}")
        async def get_progress(
            user_id: int,
            progress_repo: UserVocabularyProgressRepositoryInterface = Depends(get_user_vocabulary_progress_repository)
        ):
            return await progress_repo.get_user_progress(user_id)
        ```
    """
    return UserVocabularyProgressRepository(db)  # type: ignore[call-arg]


def get_processing_session_repository(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProcessingSessionRepositoryInterface:
    """
    Get processing session repository instance

    Args:
        db: Database session from dependency injection

    Returns:
        ProcessingSessionRepositoryInterface: Processing session repository implementation

    Example:
        ```python
        @router.get("/sessions/{session_id}")
        async def get_session(
            session_id: str,
            session_repo: ProcessingSessionRepositoryInterface = Depends(get_processing_session_repository)
        ):
            return await session_repo.get_by_session_id(session_id)
        ```
    """
    return ProcessingSessionRepository(db)  # type: ignore[call-arg]


__all__ = [
    "get_processing_session_repository",
    "get_user_repository",
    "get_user_vocabulary_progress_repository",
    "get_vocabulary_repository",
]
