"""
Vocabulary Preload Service
Loads vocabulary data from text files into the database
"""

import logging
from pathlib import Path
from typing import List, Dict, Set
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Vocabulary
from core.database import get_async_session
from datetime import datetime

logger = logging.getLogger(__name__)


class VocabularyPreloadService:
    """Service for preloading vocabulary data from files"""

    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data"

    async def load_vocabulary_files(self) -> Dict[str, int]:
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

        async with get_async_session() as session:
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
            with open(file_path, "r", encoding="utf-8") as f:
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
                        existing = await session.get(Vocabulary, word.lower())
                        if not existing:
                            vocab_entry = Vocabulary(
                                word=word.lower(),
                                difficulty_level=level,
                                language="de",
                                word_type="unknown",
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
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

    async def get_level_words(self, level: str) -> List[Dict[str, str]]:
        """Get all words for a specific difficulty level"""
        try:
            async with get_async_session() as session:
                from sqlalchemy import select
                
                stmt = select(Vocabulary).where(
                    Vocabulary.difficulty_level == level,
                    Vocabulary.language == 'de'
                ).order_by(Vocabulary.word)
                
                result = await session.execute(stmt)
                vocab_entries = result.scalars().all()
                
                words = []
                for vocab in vocab_entries:
                    words.append({
                        "id": vocab.id,
                        "word": vocab.word,
                        "difficulty_level": vocab.difficulty_level,
                        "word_type": vocab.word_type or "noun",
                        "part_of_speech": vocab.part_of_speech or vocab.word_type or "noun",
                        "definition": vocab.definition or "",
                    })
                return words
        except Exception as e:
            logger.error(f"Error getting {level} words: {e}")
            raise Exception(f"Failed to get {level} words: {e}") from e

    async def get_user_known_words(self, user_id: int, level: str = None) -> Set[str]:
        """Get words that a user has marked as known"""
        try:
            async with get_async_session() as session:
                from sqlalchemy import select
                from database.models import UserLearningProgress
                
                if level:
                    stmt = select(Vocabulary.word).join(
                        UserLearningProgress, UserLearningProgress.word_id == Vocabulary.id
                    ).where(
                        UserLearningProgress.user_id == str(user_id),
                        Vocabulary.difficulty_level == level,
                        Vocabulary.language == 'de'
                    )
                else:
                    stmt = select(Vocabulary.word).join(
                        UserLearningProgress, UserLearningProgress.word_id == Vocabulary.id
                    ).where(
                        UserLearningProgress.user_id == str(user_id),
                        Vocabulary.language == 'de'
                    )
                
                result = await session.execute(stmt)
                words = result.scalars().all()
                return set(words)
        except Exception as e:
            logger.error(f"Error getting user known words: {e}")
            raise Exception(f"Failed to get user known words: {e}") from e

    async def mark_user_word_known(self, user_id: int, word: str, known: bool = True) -> bool:
        """Mark a word as known/unknown for a specific user"""
        try:
            async with get_async_session() as session:
                from sqlalchemy import select, delete
                from database.models import UserLearningProgress
                
                # First, get the word from vocabulary table
                vocab_stmt = select(Vocabulary).where(
                    Vocabulary.word == word.lower(),
                    Vocabulary.language == 'de'
                )
                vocab_result = await session.execute(vocab_stmt)
                vocab_entry = vocab_result.scalar_one_or_none()
                
                if not vocab_entry:
                    logger.warning(f"Word '{word}' not found in vocabulary")
                    return False

                if known:
                    # Check if progress entry already exists
                    existing_stmt = select(UserLearningProgress).where(
                        UserLearningProgress.user_id == str(user_id),
                        UserLearningProgress.word_id == vocab_entry.id
                    )
                    existing_result = await session.execute(existing_stmt)
                    existing_progress = existing_result.scalar_one_or_none()
                    
                    if existing_progress:
                        # Update existing
                        existing_progress.learned_at = datetime.utcnow()
                        existing_progress.confidence_level = 5
                        existing_progress.review_count = (existing_progress.review_count or 0) + 1
                        existing_progress.last_reviewed = datetime.utcnow()
                    else:
                        # Create new
                        progress = UserLearningProgress(
                            user_id=str(user_id),
                            word_id=vocab_entry.id,
                            learned_at=datetime.utcnow(),
                            confidence_level=5,
                            review_count=1,
                            last_reviewed=datetime.utcnow()
                        )
                        session.add(progress)
                else:
                    # Remove from known words
                    delete_stmt = delete(UserLearningProgress).where(
                        UserLearningProgress.user_id == str(user_id),
                        UserLearningProgress.word_id == vocab_entry.id
                    )
                    await session.execute(delete_stmt)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(
                f"Error marking word '{word}' as {'known' if known else 'unknown'}: {e}"
            )
            return False

    async def bulk_mark_level_known(
        self, user_id: int, level: str, known: bool = True
    ) -> int:
        """Mark all words of a specific level as known/unknown for a user"""
        try:
            level_words = await self.get_level_words(level)
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

    async def get_vocabulary_stats(self) -> Dict[str, Dict[str, int]]:
        """Get vocabulary statistics by level"""
        try:
            async with get_async_session() as session:
                # Get comprehensive statistics with definitions and user knowledge counts
                query = text("""
                    SELECT 
                        v.difficulty_level,
                        COUNT(*) as total_words,
                        COUNT(CASE WHEN v.definition IS NOT NULL AND v.definition != '' THEN 1 END) as has_definition,
                        COUNT(CASE WHEN ukw.word IS NOT NULL THEN 1 END) as user_known
                    FROM vocabulary v
                    LEFT JOIN user_known_words ukw ON v.word = ukw.word
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
