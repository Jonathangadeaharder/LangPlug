"""
Database session management for dependency injection

DEPRECATED: This module uses synchronous SessionLocal which no longer exists.
Use core.database.get_async_session() instead for async database operations.
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal

if TYPE_CHECKING:
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with automatic cleanup

    DEPRECATED: Use core.database.get_async_session() directly instead.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database session

    DEPRECATED: Use core.database.get_async_session() directly instead.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
