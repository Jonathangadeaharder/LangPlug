"""
Database session management for dependency injection
"""

from contextlib import contextmanager

from sqlalchemy.orm import Session

from core.database import SessionLocal


@contextmanager
def get_db_session():
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Session:
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
