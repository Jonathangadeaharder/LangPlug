"""
Base Repository Pattern for Standardized Database Access
Addresses standardization of database access patterns across services
"""

import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select, text

from core.database import get_async_session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository for standardized database operations
    Provides common CRUD operations and transaction management
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the primary table name for this repository"""
        pass

    @property
    @abstractmethod
    def model_class(self):
        """Return the SQLAlchemy model class for this repository"""
        pass

    @asynccontextmanager
    async def get_session(self):
        """Get async database session with proper error handling"""
        async for session in get_async_session():
            try:
                yield session
            except Exception as e:
                self.logger.error(f"Database session error: {e}")
                await session.rollback()
                raise
            break

    @asynccontextmanager
    async def transaction(self):
        """Execute operations within a transaction"""
        async for session in get_async_session():
            try:
                yield session
                await session.commit()
            except Exception as e:
                self.logger.error(f"Transaction error: {e}")
                await session.rollback()
                raise
            break

    async def find_by_id(self, id_value: int | str) -> T | None:
        """Find entity by primary key"""
        try:
            async with self.get_session() as session:
                stmt = select(self.model_class).where(self.model_class.id == id_value)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                return row
        except Exception as e:
            self.logger.error(f"Error finding {self.table_name} by id {id_value}: {e}")
            raise

    async def find_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """Find all entities with optional pagination"""
        try:
            async with self.get_session() as session:
                stmt = select(self.model_class)

                if limit is not None:
                    stmt = stmt.limit(limit)

                if offset is not None:
                    stmt = stmt.offset(offset)

                result = await session.execute(stmt)
                rows = result.scalars().all()
                return list(rows)
        except Exception as e:
            self.logger.error(f"Error finding all {self.table_name}: {e}")
            raise

    async def find_by_criteria(self, criteria: dict[str, Any]) -> list[T]:
        """Find entities by custom criteria"""
        try:
            if not criteria:
                return await self.find_all()

            async with self.get_session() as session:
                stmt = select(self.model_class)

                # Build WHERE clause
                for key, value in criteria.items():
                    if hasattr(self.model_class, key):
                        stmt = stmt.where(getattr(self.model_class, key) == value)

                result = await session.execute(stmt)
                rows = result.scalars().all()
                return list(rows)
        except Exception as e:
            self.logger.error(f"Error finding {self.table_name} by criteria {criteria}: {e}")
            raise

    async def save(self, entity: T) -> T:
        """Save entity (insert or update)"""
        try:
            async with self.transaction() as session:
                # Check if entity has an ID (update vs insert)
                if hasattr(entity, "id") and entity.id is not None:
                    # Update existing entity
                    session.merge(entity)
                else:
                    # Insert new entity
                    session.add(entity)

                await session.flush()  # Get the ID if it's a new entity
                return entity
        except Exception as e:
            self.logger.error(f"Error saving {self.table_name}: {e}")
            raise

    async def delete_by_id(self, id_value: int | str) -> bool:
        """Delete entity by primary key"""
        try:
            async with self.transaction() as session:
                stmt = delete(self.model_class).where(self.model_class.id == id_value)
                result = await session.execute(stmt)
                return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting {self.table_name} with id {id_value}: {e}")
            raise

    async def count(self, criteria: dict[str, Any] | None = None) -> int:
        """Count entities matching criteria"""
        try:
            async with self.get_session() as session:
                stmt = select(func.count()).select_from(self.model_class)

                if criteria:
                    for key, value in criteria.items():
                        if hasattr(self.model_class, key):
                            stmt = stmt.where(getattr(self.model_class, key) == value)

                result = await session.execute(stmt)
                return result.scalar()
        except Exception as e:
            self.logger.error(f"Error counting {self.table_name}: {e}")
            raise

    async def execute_raw_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute raw SQL query - use sparingly and with caution"""
        self.logger.warning(f"Executing raw query: {query}")
        try:
            async with self.get_session() as session:
                stmt = text(query)
                if params:
                    result = await session.execute(stmt, params)
                else:
                    result = await session.execute(stmt)

                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            self.logger.error(f"Error executing raw query: {e}")
            raise
