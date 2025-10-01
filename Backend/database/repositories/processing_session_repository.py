"""
Repository for processing session operations
"""

from datetime import datetime

from sqlalchemy.orm import Session

from database.models import ProcessingSession
from database.repositories.base_repository_sync import BaseSyncRepository
from database.repositories.interfaces import ProcessingSessionRepositoryInterface


class ProcessingSessionRepository(BaseSyncRepository[ProcessingSession, str], ProcessingSessionRepositoryInterface):
    """Repository for processing session operations"""

    def __init__(self):
        super().__init__(ProcessingSession)

    async def get_by_session_id(self, db: Session, session_id: str) -> ProcessingSession | None:
        """Get processing session by session ID"""
        return db.query(ProcessingSession).filter(ProcessingSession.session_id == session_id).first()

    async def update_status(
        self, db: Session, session_id: str, status: str, error_message: str | None = None
    ) -> ProcessingSession | None:
        """Update processing session status"""
        session = await self.get_by_session_id(db, session_id)
        if session:
            session.status = status
            if error_message:
                session.error_message = error_message
            if status == "completed":
                session.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session

    async def get_user_sessions(self, db: Session, user_id: int, status: str | None = None) -> list[ProcessingSession]:
        """Get processing sessions for a user"""
        query = db.query(ProcessingSession).filter(ProcessingSession.user_id == user_id)

        if status:
            query = query.filter(ProcessingSession.status == status)

        return query.order_by(ProcessingSession.created_at.desc()).all()

    async def get_recent_sessions(
        self, db: Session, limit: int = 10, status: str | None = None
    ) -> list[ProcessingSession]:
        """Get recent processing sessions"""
        query = db.query(ProcessingSession)

        if status:
            query = query.filter(ProcessingSession.status == status)

        return query.order_by(ProcessingSession.created_at.desc()).limit(limit).all()

    async def update_processing_stats(
        self,
        db: Session,
        session_id: str,
        total_words: int,
        unique_words: int,
        unknown_words_count: int,
        processing_time_seconds: float,
    ) -> ProcessingSession | None:
        """Update processing statistics"""
        session = await self.get_by_session_id(db, session_id)
        if session:
            session.total_words = total_words
            session.unique_words = unique_words
            session.unknown_words_count = unknown_words_count
            session.processing_time_seconds = processing_time_seconds
            db.commit()
            db.refresh(session)
        return session

    async def delete_old_sessions(self, db: Session, days_old: int = 30) -> int:
        """Delete processing sessions older than specified days"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        deleted_count = db.query(ProcessingSession).filter(ProcessingSession.created_at < cutoff_date).delete()
        db.commit()
        return deleted_count

    async def get_by_id(self, db: Session, entity_id: str) -> ProcessingSession | None:
        """Override base method to use session_id as primary key"""
        return await self.get_by_session_id(db, entity_id)
