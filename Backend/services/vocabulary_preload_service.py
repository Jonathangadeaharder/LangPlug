"""
Vocabulary Preload Service
Loads vocabulary data from text files into the database
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from database.models import VocabularyWord

logger = logging.getLogger(__name__)


class VocabularyPreloadService:
    """Service for preloading vocabulary data from files"""

    def __init__(self, data_path=None):
        self.data_path = data_path or (Path(__file__).parent.parent / "data")

    async def load_vocabulary_files(self) -> dict[str, int]:
        """
        Load all vocabulary files into the database

        Returns:
            Dictionary with level -> word count mapping
        """
        result = {}

        vocabulary_files = {
            "A1": self.data_path / "a1.txt",
            "A2": self.data_path / "a2.txt",
            "B1": self.data_path / "b1.txt",
            "B2": self.data_path / "b2.txt",
        }

        async with AsyncSessionLocal() as session:
            for level, file_path in vocabulary_files.items():
                if file_path.exists():
                    count = await self._load_level_vocabulary(session, level, file_path)
                    result[level] = count
                    logger.info(f"Loaded {count} {level} words from {file_path}")
                else:
                    logger.warning(f"Vocabulary file not found: {file_path}")
                    result[level] = 0

        return result

    async def _load_level_vocabulary(self, session: AsyncSession, level: str, file_path: Path) -> int:
        """Load vocabulary words from a specific level file"""
        words = []

        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:  # Skip empty lines
                        words.append(word)

            # Insert words into database using SQLAlchemy
            if words:
                try:
                    loaded_count = 0
                    for word in words:
                        # Check if word already exists
                        existing = await session.get(VocabularyWord, word.lower())
                        if not existing:
                            vocab_entry = VocabularyWord(
                                word=word.lower(),
                                lemma=word.lower(),
                                language="de",
                                difficulty_level=level,
                                part_of_speech="noun",
                                translation_en="",
                                translation_native="",
                                pronunciation="",
                                notes="",
                                frequency_rank=0,
                                created_at=datetime.now(UTC),
                                updated_at=datetime.now(UTC),
                            )
                            session.add(vocab_entry)
                            loaded_count += 1

                    await session.commit()
                    logger.info(f"Batch inserted {loaded_count} words for level {level}")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to batch insert words for level {level}: {e}")
                    loaded_count = 0
            else:
                loaded_count = 0

            return loaded_count

        except Exception as e:
            logger.error(f"Error loading vocabulary from {file_path}: {e}")
            raise Exception(f"Failed to load vocabulary from {file_path}: {e}") from e

    async def get_level_words(self, level: str, session: AsyncSession = None) -> list[dict[str, str]]:
        """Get all words for a specific difficulty level"""
        try:
            # If no session provided, create one (fallback for backwards compatibility)
            if session is None:
                from sqlalchemy.ext.asyncio import async_sessionmaker

                from core.database import engine

                async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
                async with async_session_maker() as session:
                    return await self._execute_get_level_words(session, level)
            else:
                return await self._execute_get_level_words(session, level)
        except Exception as e:
            logger.error(f"Error getting {level} words: {e}")
            raise Exception(f"Failed to get {level} words: {e}") from e

    async def _execute_get_level_words(self, session: AsyncSession, level: str) -> list[dict[str, str]]:
        """Execute the actual database query for level words"""
        from sqlalchemy import select

        from database.models import VocabularyWord

        stmt = (
            select(VocabularyWord)
            .where(VocabularyWord.difficulty_level == level, VocabularyWord.language == "de")
            .order_by(VocabularyWord.word)
        )

        result = await session.execute(stmt)
        words_db = result.scalars().all()

        words = []
        for word_db in words_db:
            words.append(
                {
                    "id": word_db.id,
                    "word": word_db.word,
                    "difficulty_level": word_db.difficulty_level,
                    "word_type": word_db.part_of_speech or "noun",
                    "part_of_speech": word_db.part_of_speech or "noun",
                    "definition": word_db.notes or "",
                }
            )
        return words

    async def get_user_known_words(
        self, user_id: int, level: str | None = None, session: AsyncSession = None
    ) -> set[str]:
        """Get words that a user has marked as known"""
        try:
            # If no session provided, create one (fallback for backwards compatibility)
            if session is None:
                from sqlalchemy.ext.asyncio import async_sessionmaker

                from core.database import engine

                async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
                async with async_session_maker() as session:
                    return await self._execute_get_user_known_words(session, user_id, level)
            else:
                return await self._execute_get_user_known_words(session, user_id, level)
        except Exception as e:
            logger.error(f"Error getting user known words: {e}")
            raise Exception(f"Failed to get user known words: {e}") from e

    async def _execute_get_user_known_words(
        self, session: AsyncSession, user_id: int, level: str | None = None
    ) -> set[str]:
        """Execute the actual database query for user known words"""
        from sqlalchemy import select

        from database.models import UserVocabularyProgress, VocabularyWord

        if level:
            stmt = (
                select(VocabularyWord.word)
                .join(UserVocabularyProgress, UserVocabularyProgress.vocabulary_id == VocabularyWord.id)
                .where(
                    UserVocabularyProgress.user_id == user_id,
                    VocabularyWord.difficulty_level == level,
                    VocabularyWord.language == "de",
                )
            )
        else:
            stmt = (
                select(VocabularyWord.word)
                .join(UserVocabularyProgress, UserVocabularyProgress.vocabulary_id == VocabularyWord.id)
                .where(UserVocabularyProgress.user_id == user_id, VocabularyWord.language == "de")
            )

        result = await session.execute(stmt)
        words = result.scalars().all()
        return set(words)

    async def mark_user_word_known(self, user_id: int, word: str, known: bool = True) -> bool:
        """Mark a word as known/unknown for a specific user"""
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import delete, select

                # First, get the word from vocabulary table
                from database.models import UserVocabularyProgress, VocabularyWord

                vocab_stmt = select(VocabularyWord).where(
                    VocabularyWord.word == word.lower(), VocabularyWord.language == "de"
                )
                vocab_result = await session.execute(vocab_stmt)
                vocab_word = vocab_result.scalar_one_or_none()

                if not vocab_word:
                    logger.warning(f"Word '{word}' not found in vocabulary")
                    return False

                # Get the vocabulary ID
                vocabulary_id = vocab_word.id

                if known:
                    # Check if progress entry already exists
                    existing_stmt = select(UserVocabularyProgress).where(
                        UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id == vocabulary_id
                    )
                    existing_result = await session.execute(existing_stmt)
                    existing_progress = existing_result.scalar_one_or_none()

                    if existing_progress:
                        # Update existing
                        existing_progress.is_known = True
                        existing_progress.confidence_level = 5
                        existing_progress.review_count = (existing_progress.review_count or 0) + 1
                        existing_progress.last_reviewed_at = datetime.now(UTC)
                    else:
                        # Create new
                        progress = UserVocabularyProgress(
                            user_id=user_id,
                            vocabulary_id=vocabulary_id,
                            lemma=vocab_word.lemma,
                            language=vocab_word.language,
                            is_known=True,
                            confidence_level=5,
                            review_count=1,
                            last_reviewed_at=datetime.now(UTC),
                            first_seen_at=datetime.now(UTC),
                            created_at=datetime.now(UTC),
                            updated_at=datetime.now(UTC),
                        )
                        session.add(progress)
                else:
                    # Set as unknown
                    delete_stmt = delete(UserVocabularyProgress).where(
                        UserVocabularyProgress.user_id == user_id, UserVocabularyProgress.vocabulary_id == vocabulary_id
                    )
                    await session.execute(delete_stmt)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking word '{word}' as {'known' if known else 'unknown'}: {e}")
            return False

    async def bulk_mark_level_known(
        self, user_id: int, level: str, known: bool = True, session: AsyncSession = None
    ) -> int:
        """Mark all words of a specific level as known/unknown for a user"""
        try:
            level_words = await self.get_level_words(level, session)
            success_count = 0

            for word_data in level_words:
                if await self.mark_user_word_known(user_id, word_data["word"], known):
                    success_count += 1

            logger.info(
                f"Bulk marked {success_count}/{len(level_words)} {level} words as {'known' if known else 'unknown'}"
            )
            return success_count
        except Exception as e:
            logger.error(f"Error bulk marking {level} words: {e}")
            raise Exception(f"Failed to bulk mark {level} words: {e}") from e

    async def get_vocabulary_stats(self, session: AsyncSession = None) -> dict[str, dict[str, int]]:
        """Get vocabulary statistics by level"""
        try:
            # Use provided session or create a new one
            if session:
                # Use provided session directly
                query = text("""
                    SELECT
                        v.difficulty_level,
                        COUNT(*) as total_words,
                        0 as has_definition,
                        COUNT(CASE WHEN ulp.vocabulary_id IS NOT NULL THEN 1 END) as user_known
                    FROM vocabulary_words v
                    LEFT JOIN user_vocabulary_progress ulp ON v.id = ulp.vocabulary_id
                    WHERE v.language = 'de'
                    GROUP BY v.difficulty_level
                    ORDER BY v.difficulty_level
                """)

                result = await session.execute(query)
                rows = result.fetchall()

                stats = {}
                for row in rows:
                    level = row.difficulty_level
                    stats[level] = {
                        "total_words": row.total_words,
                        "has_definition": row.has_definition,
                        "user_known": row.user_known,
                    }
                return stats
            else:
                # Fallback to original behavior for backward compatibility
                async with AsyncSessionLocal() as session:
                    query = text("""
                        SELECT
                            v.difficulty_level,
                            COUNT(*) as total_words,
                            0 as has_definition,
                            COUNT(CASE WHEN ulp.vocabulary_id IS NOT NULL THEN 1 END) as user_known
                        FROM vocabulary_words v
                        LEFT JOIN user_vocabulary_progress ulp ON v.id = ulp.vocabulary_id
                        WHERE v.language = 'de'
                        GROUP BY v.difficulty_level
                        ORDER BY v.difficulty_level
                    """)

                    result = await session.execute(query)
                    rows = result.fetchall()

                    stats = {}
                    for row in rows:
                        level = row.difficulty_level
                        stats[level] = {
                            "total_words": row.total_words,
                            "has_definition": row.has_definition,
                            "user_known": row.user_known,
                        }
                return stats
        except Exception as e:
            logger.error(f"Error getting vocabulary stats: {e}")
            raise Exception(f"Failed to get vocabulary stats: {e}") from e


# Utility function for easy access
def get_vocabulary_preload_service() -> VocabularyPreloadService:
    """Get a vocabulary preload service instance"""
    return VocabularyPreloadService()
