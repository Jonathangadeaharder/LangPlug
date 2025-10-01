"""
Synchronous base repository implementation for clean architecture
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.repositories.interfaces import BaseRepositoryInterface

T = TypeVar("T")
ID = TypeVar("ID", int, str)


class BaseSyncRepository(BaseRepositoryInterface[T, ID], Generic[T, ID]):
    """Base synchronous repository implementation"""

    def __init__(self, model: type[T]):
        self.model = model

    async def create(self, db: Session, **kwargs) -> T:
        """Create a new entity"""
        instance = self.model(**kwargs)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    async def get_by_id(self, db: Session, entity_id: ID) -> T | None:
        """Get entity by ID"""
        return db.query(self.model).filter(self.model.id == entity_id).first()

    async def get_many(
        self, db: Session, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[T]:
        """Get multiple entities with pagination and filtering"""
        query = db.query(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)

        return query.offset(skip).limit(limit).all()

    async def update(self, db: Session, entity_id: ID, **kwargs) -> T | None:
        """Update an entity"""
        instance = await self.get_by_id(db, entity_id)
        if instance:
            for field, value in kwargs.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            db.commit()
            db.refresh(instance)
        return instance

    async def delete(self, db: Session, entity_id: ID) -> bool:
        """Delete an entity"""
        instance = await self.get_by_id(db, entity_id)
        if instance:
            db.delete(instance)
            db.commit()
            return True
        return False

    async def exists(self, db: Session, entity_id: ID) -> bool:
        """Check if entity exists"""
        return db.query(self.model).filter(self.model.id == entity_id).first() is not None

    async def count(self, db: Session, filters: dict[str, Any] | None = None) -> int:
        """Count entities with optional filters"""
        query = db.query(func.count(self.model.id))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)

        return query.scalar()

    async def get_by_field(self, db: Session, field: str, value: Any) -> T | None:
        """Get entity by specific field"""
        if hasattr(self.model, field):
            return db.query(self.model).filter(getattr(self.model, field) == value).first()
        return None

    async def get_many_by_field(self, db: Session, field: str, value: Any, skip: int = 0, limit: int = 100) -> list[T]:
        """Get multiple entities by specific field"""
        if hasattr(self.model, field):
            return db.query(self.model).filter(getattr(self.model, field) == value).offset(skip).limit(limit).all()
        return []
