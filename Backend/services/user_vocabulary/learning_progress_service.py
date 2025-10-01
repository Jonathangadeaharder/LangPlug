"""
Learning Progress Service
Handles tracking user learning progress (marking words learned, removing words)
"""

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .vocabulary_repository import vocabulary_repository


class LearningProgressService:
    """Service for managing user learning progress"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repository = vocabulary_repository

    async def mark_word_learned(self, session: AsyncSession, user_id: str, word: str, language: str = "en") -> bool:
        """
        Mark word as learned by user

        Args:
            session: Database session
            user_id: User ID
            word: Word to mark as learned
            language: Language code

        Returns:
            True if successful, False otherwise
        """
        try:
            word_lower = word.lower()

            # Ensure the word exists in vocabulary table
            word_id = await self.repository.ensure_word_exists(session, word_lower, language)
            if not word_id:
                return False

            # Check if already learned
            existing_query = text("""
                SELECT id FROM user_learning_progress
                WHERE user_id = :user_id AND word_id = :word_id
            """)
            existing_result = await session.execute(existing_query, {"user_id": user_id, "word_id": word_id})
            existing_row = existing_result.fetchone()

            now = datetime.now().isoformat()

            if existing_row:
                # Update existing record
                update_query = text("""
                    UPDATE user_learning_progress
                    SET confidence_level = confidence_level + 1,
                        review_count = review_count + 1,
                        last_reviewed = :now
                    WHERE user_id = :user_id AND word_id = :word_id
                """)
                await session.execute(update_query, {"now": now, "user_id": user_id, "word_id": word_id})
            else:
                # Insert new learning record
                insert_query = text("""
                    INSERT INTO user_learning_progress (user_id, word_id, learned_at, confidence_level, review_count)
                    VALUES (:user_id, :word_id, :now, 1, 1)
                """)
                await session.execute(insert_query, {"user_id": user_id, "word_id": word_id, "now": now})

            await session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error marking word as learned: {e}")
            return False

    async def add_known_words(
        self, session: AsyncSession, user_id: str, words: list[str], language: str = "en"
    ) -> bool:
        """
        Add multiple words to user's known vocabulary using batch operations

        Args:
            session: Database session
            user_id: User ID
            words: List of words to add
            language: Language code

        Returns:
            True if any words were added, False otherwise
        """
        try:
            if not words:
                return True

            # Normalize words
            normalized_words = [word.lower().strip() for word in words if word.strip()]
            if not normalized_words:
                return True

            # Ensure all words exist in vocabulary table (batch operation)
            word_ids = await self.repository.ensure_words_exist_batch(session, normalized_words, language)
            if not word_ids:
                self.logger.error("Failed to ensure words exist in vocabulary")
                return False

            # Get existing learning progress for these words
            existing_progress = await self.repository.get_existing_progress_batch(
                session, user_id, list(word_ids.values())
            )

            # Prepare and execute operations
            now = datetime.now().isoformat()
            success_count = 0

            for _word, word_id in word_ids.items():
                if word_id in existing_progress:
                    # Update existing record
                    update_query = text("""
                        UPDATE user_learning_progress
                        SET confidence_level = confidence_level + 1,
                            review_count = review_count + 1,
                            last_reviewed = :now
                        WHERE user_id = :user_id AND word_id = :word_id
                    """)
                    await session.execute(update_query, {"now": now, "user_id": user_id, "word_id": word_id})
                    success_count += 1
                else:
                    # Insert new learning record
                    insert_query = text("""
                        INSERT INTO user_learning_progress (user_id, word_id, learned_at, confidence_level, review_count)
                        VALUES (:user_id, :word_id, :now, 1, 1)
                    """)
                    await session.execute(insert_query, {"user_id": user_id, "word_id": word_id, "now": now})
                    success_count += 1

            await session.commit()
            self.logger.info(f"Batch added {success_count}/{len(normalized_words)} words for user {user_id}")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Error adding known words in batch: {e}")
            return False

    async def remove_word(self, session: AsyncSession, user_id: str, word: str, language: str = "en") -> bool:
        """
        Remove word from user's learned vocabulary

        Args:
            session: Database session
            user_id: User ID
            word: Word to remove
            language: Language code

        Returns:
            True if successful, False otherwise
        """
        try:
            word_lower = word.lower()

            # Get word ID
            word_id = await self.repository.get_word_id(session, word_lower, language)
            if not word_id:
                self.logger.warning(f"Word '{word}' not found in vocabulary")
                return False

            # Delete learning progress record
            delete_query = text("""
                DELETE FROM user_learning_progress
                WHERE user_id = :user_id AND word_id = :word_id
            """)
            result = await session.execute(delete_query, {"user_id": user_id, "word_id": word_id})
            await session.commit()

            deleted_count = result.rowcount
            if deleted_count > 0:
                self.logger.info(f"Removed word '{word}' from user {user_id}'s learned vocabulary")
                return True
            else:
                self.logger.warning(f"Word '{word}' was not in user {user_id}'s learned vocabulary")
                return False

        except Exception as e:
            self.logger.error(f"Error removing word: {e}")
            return False


# Singleton instance
learning_progress_service = LearningProgressService()
