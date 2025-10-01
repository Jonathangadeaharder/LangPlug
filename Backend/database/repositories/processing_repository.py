"""Repository for processing session database operations"""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ProcessingSession, SessionVocabulary

from .base_repository import BaseRepository


class ProcessingRepository(BaseRepository[ProcessingSession]):
    """Repository for processing session operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingSession, session)

    async def find_by_session_id(self, session_id: str) -> ProcessingSession | None:
        """Find processing session by session ID"""
        stmt = (
            select(ProcessingSession)
            .where(ProcessingSession.session_id == session_id)
            .options(selectinload(ProcessingSession.vocabulary))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, user_id: int, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[ProcessingSession]:
        """Get processing sessions for a user"""
        stmt = select(ProcessingSession).where(ProcessingSession.user_id == user_id)

        if status:
            stmt = stmt.where(ProcessingSession.status == status)

        stmt = stmt.order_by(ProcessingSession.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, session_id: str, status: str, error_message: str | None = None) -> bool:
        """Update processing session status"""
        values = {"status": status}
        if error_message:
            values["error_message"] = error_message
        if status == "completed":
            values["completed_at"] = datetime.utcnow()

        stmt = update(ProcessingSession).where(ProcessingSession.session_id == session_id).values(**values)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def add_session_vocabulary(self, session_id: str, vocabulary_items: list[dict[str, Any]]) -> int:
        """Add vocabulary items to a session"""
        session = await self.find_by_session_id(session_id)
        if not session:
            return 0

        added = 0
        for item in vocabulary_items:
            vocab = SessionVocabulary(
                session_id=session.id,
                word=item["word"],
                lemma=item.get("lemma"),
                frequency=item.get("frequency", 1),
                is_known=item.get("is_known", False),
                difficulty_score=item.get("difficulty_score", 0.5),
            )
            self.session.add(vocab)
            added += 1

        await self.session.commit()
        return added

    async def get_session_statistics(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a processing session"""
        session = await self.find_by_session_id(session_id)
        if not session:
            return {}

        # Get vocabulary statistics
        vocab_stmt = (
            select(
                func.count().label("total"),
                func.count().filter(SessionVocabulary.is_known).label("known"),
                func.count().filter(not SessionVocabulary.is_known).label("unknown"),
                func.avg(SessionVocabulary.difficulty_score).label("avg_difficulty"),
            )
            .select_from(SessionVocabulary)
            .where(SessionVocabulary.session_id == session.id)
        )
        result = await self.session.execute(vocab_stmt)
        stats = result.first()

        return {
            "session_id": session_id,
            "status": session.status,
            "content_type": session.content_type,
            "language": session.language,
            "total_words": session.total_words or 0,
            "unique_words": session.unique_words or 0,
            "unknown_words_count": session.unknown_words_count or 0,
            "processing_time": session.processing_time_seconds,
            "vocabulary_stats": {
                "total": stats.total or 0,
                "known": stats.known or 0,
                "unknown": stats.unknown or 0,
                "average_difficulty": float(stats.avg_difficulty) if stats.avg_difficulty else 0,
            }
            if stats
            else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up old processing sessions"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(ProcessingSession.id).where(
            and_(
                ProcessingSession.created_at < cutoff_date,
                ProcessingSession.status.in_(["completed", "error", "cancelled"]),
            )
        )
        result = await self.session.execute(stmt)
        session_ids = [row[0] for row in result]

        if session_ids:
            # Delete related vocabulary
            vocab_stmt = delete(SessionVocabulary).where(SessionVocabulary.session_id.in_(session_ids))
            await self.session.execute(vocab_stmt)

            # Delete sessions
            session_stmt = delete(ProcessingSession).where(ProcessingSession.id.in_(session_ids))
            await self.session.execute(session_stmt)
            await self.session.commit()

        return len(session_ids)
