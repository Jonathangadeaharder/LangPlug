"""
Vocabulary Repository
Handles data access for vocabulary and user learning progress tables
"""

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class VocabularyRepository:
    """Repository for vocabulary and user learning progress data access"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def ensure_word_exists(self, session: AsyncSession, word: str, language: str = "en") -> int | None:
        """
        Ensure word exists in vocabulary table and return its ID

        Args:
            session: Database session
            word: Word to ensure exists
            language: Language code

        Returns:
            Word ID if successful, None otherwise
        """
        try:
            # Check if word already exists
            existing_query = text("SELECT id FROM vocabulary WHERE word = :word AND language = :language")
            existing_result = await session.execute(existing_query, {"word": word, "language": language})
            existing_row = existing_result.fetchone()

            if existing_row:
                return existing_row[0]

            # Insert new word
            insert_query = text("""
                INSERT INTO vocabulary (word, language, created_at, updated_at)
                VALUES (:word, :language, :now, :now)
            """)
            now = datetime.now().isoformat()
            result = await session.execute(insert_query, {"word": word, "language": language, "now": now})
            await session.flush()

            return result.lastrowid

        except Exception as e:
            self.logger.error(f"Error ensuring word exists: {e}")
            return None

    async def ensure_words_exist_batch(
        self, session: AsyncSession, words: list[str], language: str = "en"
    ) -> dict[str, int]:
        """
        Ensure multiple words exist in vocabulary table and return word->id mapping

        Args:
            session: Database session
            words: List of words to ensure exist
            language: Language code

        Returns:
            Dictionary mapping word to word_id
        """
        try:
            if not words:
                return {}

            # Check which words already exist
            placeholders = ",".join([":word" + str(i) for i in range(len(words))])
            existing_query = text(f"""
                SELECT word, id FROM vocabulary
                WHERE word IN ({placeholders}) AND language = :language
            """)
            params = {f"word{i}": word for i, word in enumerate(words)}
            params["language"] = language
            existing_result = await session.execute(existing_query, params)

            # Build mapping of existing words
            word_ids = {row[0]: row[1] for row in existing_result.fetchall()}
            existing_words = set(word_ids.keys())

            # Insert missing words individually
            missing_words = [word for word in words if word not in existing_words]
            if missing_words:
                now = datetime.now().isoformat()
                insert_query = text("""
                    INSERT INTO vocabulary (word, language, created_at, updated_at)
                    VALUES (:word, :language, :now, :now)
                """)

                for word in missing_words:
                    result = await session.execute(insert_query, {"word": word, "language": language, "now": now})
                    word_ids[word] = result.lastrowid

                await session.flush()

            return word_ids

        except Exception as e:
            self.logger.error(f"Error ensuring words exist in batch: {e}")
            return {}

    async def get_existing_progress_batch(self, session: AsyncSession, user_id: str, word_ids: list[int]) -> set[int]:
        """
        Get existing learning progress for multiple word IDs

        Args:
            session: Database session
            user_id: User ID
            word_ids: List of word IDs to check

        Returns:
            Set of word IDs that have existing progress
        """
        try:
            if not word_ids:
                return set()

            placeholders = ",".join([":word_id" + str(i) for i in range(len(word_ids))])
            query = text(f"""
                SELECT word_id FROM user_learning_progress
                WHERE user_id = :user_id AND word_id IN ({placeholders})
            """)
            params = {f"word_id{i}": word_id for i, word_id in enumerate(word_ids)}
            params["user_id"] = user_id
            result = await session.execute(query, params)

            return {row[0] for row in result.fetchall()}

        except Exception as e:
            self.logger.error(f"Error getting existing progress in batch: {e}")
            return set()

    async def get_word_id(self, session: AsyncSession, word: str, language: str = "en") -> int | None:
        """
        Get word ID from vocabulary table

        Args:
            session: Database session
            word: Word to look up
            language: Language code

        Returns:
            Word ID if found, None otherwise
        """
        try:
            query = text("SELECT id FROM vocabulary WHERE word = :word AND language = :language")
            result = await session.execute(query, {"word": word, "language": language})
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Error getting word ID: {e}")
            return None


# Singleton instance
vocabulary_repository = VocabularyRepository()
