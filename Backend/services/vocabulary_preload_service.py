"""
Vocabulary Preload Service
Loads vocabulary data from text files into the database
"""

import logging
from pathlib import Path
from typing import List, Dict, Set
from database.unified_database_manager import UnifiedDatabaseManager as DatabaseManager

logger = logging.getLogger(__name__)


class VocabularyPreloadService:
    """Service for preloading vocabulary data from files"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.data_path = Path(__file__).parent.parent / "data"

    def load_vocabulary_files(self) -> Dict[str, int]:
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

        for level, file_path in vocabulary_files.items():
            if file_path.exists():
                count = self._load_level_vocabulary(level, file_path)
                result[level] = count
                logger.info(f"Loaded {count} {level} words from {file_path}")
            else:
                logger.warning(f"Vocabulary file not found: {file_path}")
                result[level] = 0

        return result

    def _load_level_vocabulary(self, level: str, file_path: Path) -> int:
        """Load vocabulary words from a specific level file"""
        words = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:  # Skip empty lines
                        words.append(word)

            # Insert words into database using batch operation
            if words:
                query = """
                    INSERT OR IGNORE INTO vocabulary 
                    (word, difficulty_level, language, word_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                """
                
                # Prepare batch parameters
                params_list = [
                    (word.lower(), level, "de", "unknown")
                    for word in words
                ]
                
                try:
                    loaded_count = self.db.execute_many(query, params_list)
                    logger.info(f"Batch inserted {loaded_count} words for level {level}")
                except Exception as e:
                    logger.error(f"Failed to batch insert words for level {level}: {e}")
                    loaded_count = 0
            else:
                loaded_count = 0

            return loaded_count

        except Exception as e:
            logger.error(f"Error loading vocabulary from {file_path}: {e}")
            raise Exception(f"Failed to load vocabulary from {file_path}: {e}") from e

    def get_level_words(self, level: str) -> List[Dict[str, str]]:
        """Get all words for a specific difficulty level"""
        try:
            results = self.db.execute_query(
                """
                SELECT id, word, difficulty_level, word_type, definition, part_of_speech
                FROM vocabulary 
                WHERE difficulty_level = ? AND language = 'de'
                ORDER BY word
            """,
                (level,),
            )

            words = []
            for row in results:
                # Convert Row to dict for easier access
                row_dict = dict(row)
                words.append({
                    "id": row_dict.get("id"),
                    "word": row_dict.get("word"),
                    "difficulty_level": row_dict.get("difficulty_level"),
                    "word_type": row_dict.get("word_type", "noun"),
                    "part_of_speech": row_dict.get("part_of_speech") or row_dict.get("word_type", "noun"),
                    "definition": row_dict.get("definition", ""),
                })
            return words
        except Exception as e:
            logger.error(f"Error getting {level} words: {e}")
            raise Exception(f"Failed to get {level} words: {e}") from e

    def get_user_known_words(self, user_id: int, level: str = None) -> Set[str]:
        """Get words that a user has marked as known"""
        try:
            if level:
                results = self.db.execute_query(
                    """
                    SELECT v.word
                    FROM user_learning_progress ulp
                    JOIN vocabulary v ON ulp.word_id = v.id
                    WHERE ulp.user_id = ? AND v.difficulty_level = ? AND v.language = 'de'
                """,
                    (str(user_id), level),
                )
            else:
                results = self.db.execute_query(
                    """
                    SELECT v.word
                    FROM user_learning_progress ulp
                    JOIN vocabulary v ON ulp.word_id = v.id
                    WHERE ulp.user_id = ? AND v.language = 'de'
                """,
                    (str(user_id),),
                )

            return {row["word"] for row in results}
        except Exception as e:
            logger.error(f"Error getting user known words: {e}")
            raise Exception(f"Failed to get user known words: {e}") from e

    def mark_user_word_known(self, user_id: int, word: str, known: bool = True) -> bool:
        """Mark a word as known/unknown for a specific user"""
        try:
            # First, get the word_id from vocabulary table
            word_results = self.db.execute_query(
                """
                SELECT id FROM vocabulary WHERE word = ? AND language = 'de'
            """,
                (word.lower(),),
            )

            if not word_results:
                logger.warning(f"Word '{word}' not found in vocabulary")
                return False

            word_id = word_results[0]["id"]

            if known:
                # Insert or update as known
                self.db.execute_update(
                    """
                    INSERT OR REPLACE INTO user_learning_progress 
                    (user_id, word_id, learned_at, confidence_level, review_count, last_reviewed)
                    VALUES (?, ?, datetime('now'), 5, 1, datetime('now'))
                """,
                    (str(user_id), word_id),
                )
            else:
                # Remove from known words
                self.db.execute_update(
                    """
                    DELETE FROM user_learning_progress
                    WHERE user_id = ? AND word_id = ?
                """,
                    (str(user_id), word_id),
                )

            return True
        except Exception as e:
            logger.error(
                f"Error marking word '{word}' as {'known' if known else 'unknown'}: {e}"
            )
            return False

    def bulk_mark_level_known(
        self, user_id: int, level: str, known: bool = True
    ) -> int:
        """Mark all words of a specific level as known/unknown for a user"""
        try:
            level_words = self.get_level_words(level)
            success_count = 0

            for word_data in level_words:
                if self.mark_user_word_known(user_id, word_data["word"], known):
                    success_count += 1

            logger.info(
                f"Bulk marked {success_count}/{len(level_words)} {level} words as {'known' if known else 'unknown'}"
            )
            return success_count
        except Exception as e:
            logger.error(f"Error bulk marking {level} words: {e}")
            raise Exception(f"Failed to bulk mark {level} words: {e}") from e

    def get_vocabulary_stats(self) -> Dict[str, Dict[str, int]]:
        """Get vocabulary statistics by level"""
        try:
            # Get comprehensive statistics with definitions and user knowledge counts
            results = self.db.execute_query(
                """
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
            """
            )

            stats = {}
            for row in results:
                level = row["difficulty_level"]
                stats[level] = {
                    "total_words": row["total_words"],
                    "has_definition": row["has_definition"],
                    "user_known": row["user_known"],
                }

            return stats
        except Exception as e:
            logger.error(f"Error getting vocabulary stats: {e}")
            raise Exception(f"Failed to get vocabulary stats: {e}") from e


# Utility function for easy access
def get_vocabulary_preload_service(
    db_manager: DatabaseManager,
) -> VocabularyPreloadService:
    """Get a vocabulary preload service instance"""
    return VocabularyPreloadService(db_manager)
