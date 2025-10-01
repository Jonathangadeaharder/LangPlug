"""
Learning Statistics Service
Handles learning statistics, history tracking, and analytics
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .learning_level_service import learning_level_service
from .word_status_service import word_status_service


class LearningStatsService:
    """Service for learning statistics and analytics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.word_status = word_status_service
        self.learning_level = learning_level_service

    async def get_learning_statistics(
        self, session: AsyncSession, user_id: str, language: str = "en"
    ) -> dict[str, Any]:
        """
        Get comprehensive learning statistics for user

        Args:
            session: Database session
            user_id: User ID
            language: Language code

        Returns:
            Dictionary with statistics including total known words, confidence distribution, recent activity
        """
        try:
            # Get total known words
            known_words = await self.word_status.get_known_words(session, user_id, language)
            total_known = len(known_words)

            # Get confidence distribution
            confidence_query = text("""
                SELECT confidence_level, COUNT(*) as count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND v.language = :language
                GROUP BY confidence_level
                ORDER BY confidence_level
            """)
            confidence_result = await session.execute(confidence_query, {"user_id": user_id, "language": language})
            confidence_distribution = {row[0]: row[1] for row in confidence_result.fetchall()}

            # Get recent learning activity
            recent_query = text("""
                SELECT COUNT(*) as recent_count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND v.language = :language
                AND ulp.learned_at >= date('now', '-7 days')
            """)
            recent_result = await session.execute(recent_query, {"user_id": user_id, "language": language})
            recent_row = recent_result.fetchone()
            recent_learned = recent_row[0] if recent_row else 0

            # Get most reviewed words
            top_reviewed_query = text("""
                SELECT v.word, ulp.review_count, ulp.confidence_level
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND v.language = :language
                ORDER BY ulp.review_count DESC
                LIMIT 10
            """)
            top_reviewed_result = await session.execute(top_reviewed_query, {"user_id": user_id, "language": language})
            top_reviewed = [
                {"word": row[0], "review_count": row[1], "confidence_level": row[2]}
                for row in top_reviewed_result.fetchall()
            ]

            learning_level = await self.learning_level.get_learning_level(session, user_id, language)

            return {
                "total_known": total_known,
                "total_learned": total_known,  # Same as known in this context
                "learning_level": learning_level,
                "total_vocabulary": total_known,
                "confidence_distribution": confidence_distribution,
                "recent_learned_7_days": recent_learned,
                "top_reviewed_words": top_reviewed,
                "language": language,
            }

        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {e}")
            return {"total_known": 0, "total_learned": 0, "error": str(e)}

    async def get_word_learning_history(
        self, session: AsyncSession, user_id: str, word: str, language: str = "en"
    ) -> list[dict[str, Any]]:
        """
        Get learning history for a specific word

        Args:
            session: Database session
            user_id: User ID
            word: Word to get history for
            language: Language code

        Returns:
            List of history entries with learned_at, confidence_level, review_count
        """
        try:
            query = text("""
                SELECT ulp.learned_at, ulp.confidence_level, ulp.review_count, ulp.last_reviewed
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND v.word = :word AND v.language = :language
            """)
            result = await session.execute(query, {"user_id": user_id, "word": word.lower(), "language": language})

            return [
                {"learned_at": row[0], "confidence_level": row[1], "review_count": row[2], "last_reviewed": row[3]}
                for row in result.fetchall()
            ]

        except Exception as e:
            self.logger.error(f"Error getting word learning history: {e}")
            return []

    async def get_words_by_confidence(
        self, session: AsyncSession, user_id: str, confidence_level: int, language: str = "en", limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get words by confidence level

        Args:
            session: Database session
            user_id: User ID
            confidence_level: Confidence level to filter by
            language: Language code
            limit: Maximum number of words to return

        Returns:
            List of words with confidence and review information
        """
        try:
            query = text("""
                SELECT v.word, ulp.confidence_level, ulp.learned_at, ulp.review_count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = :user_id AND ulp.confidence_level = :confidence_level AND v.language = :language
                ORDER BY ulp.learned_at DESC
                LIMIT :limit
            """)
            result = await session.execute(
                query, {"user_id": user_id, "confidence_level": confidence_level, "language": language, "limit": limit}
            )

            return [
                {"word": row[0], "confidence_level": row[1], "learned_at": row[2], "review_count": row[3]}
                for row in result.fetchall()
            ]

        except Exception as e:
            self.logger.error(f"Error getting words by confidence: {e}")
            return []


# Singleton instance
learning_stats_service = LearningStatsService()
