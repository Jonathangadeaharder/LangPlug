"""
User Vocabulary Data Service Implementation
Manages user's known vocabulary and learning progress
"""

from typing import Set, Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    from ..filterservice.interface import IUserVocabularyService
    from ...database.database_manager import DatabaseManager
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from database.database_manager import DatabaseManager


class SQLiteUserVocabularyService:
    """
    SQLite-based implementation of user vocabulary service
    Uses the DatabaseManager for all database operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def is_word_known(self, user_id: str, word: str, language: str = "en") -> bool:
        """Check if user knows a specific word"""
        try:
            # First check if word exists in vocabulary table
            word_query = """
                SELECT id FROM vocabulary 
                WHERE word = ? AND language = ?
            """
            word_results = self.db.execute_query(word_query, (word.lower(), language))
            
            if not word_results:
                return False
            
            word_id = word_results[0]['id']
            
            # Check if user has learned this word
            progress_query = """
                SELECT id FROM user_learning_progress 
                WHERE user_id = ? AND word_id = ?
            """
            progress_results = self.db.execute_query(progress_query, (user_id, word_id))
            
            return len(progress_results) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking if word is known: {e}")
            return False
    
    def get_known_words(self, user_id: str, language: str = "en") -> Set[str]:
        """Get all words known by user"""
        try:
            query = """
                SELECT v.word 
                FROM vocabulary v
                JOIN user_learning_progress ulp ON v.id = ulp.word_id
                WHERE ulp.user_id = ? AND v.language = ?
            """
            results = self.db.execute_query(query, (user_id, language))
            
            return {row['word'] for row in results}
            
        except Exception as e:
            self.logger.error(f"Error getting known words: {e}")
            return set()
    
    def mark_word_learned(self, user_id: str, word: str, language: str = "en") -> bool:
        """Mark word as learned by user"""
        try:
            word_lower = word.lower()
            
            # First, ensure the word exists in vocabulary table
            word_id = self._ensure_word_exists(word_lower, language)
            if not word_id:
                return False
            
            # Check if already learned
            existing_query = """
                SELECT id FROM user_learning_progress 
                WHERE user_id = ? AND word_id = ?
            """
            existing = self.db.execute_query(existing_query, (user_id, word_id))
            
            if existing:
                # Update existing record
                update_query = """
                    UPDATE user_learning_progress 
                    SET confidence_level = confidence_level + 1,
                        review_count = review_count + 1,
                        last_reviewed = ?
                    WHERE user_id = ? AND word_id = ?
                """
                self.db.execute_update(update_query, (datetime.now().isoformat(), user_id, word_id))
            else:
                # Insert new learning record
                insert_query = """
                    INSERT INTO user_learning_progress (user_id, word_id, learned_at, confidence_level, review_count)
                    VALUES (?, ?, ?, 1, 1)
                """
                self.db.execute_insert(insert_query, (user_id, word_id, datetime.now().isoformat()))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking word as learned: {e}")
            return False
    
    def get_learning_level(self, user_id: str) -> str:
        """Get user's current learning level"""
        try:
            # Determine level based on vocabulary size
            known_words_count = len(self.get_known_words(user_id))
            
            if known_words_count < 500:
                return "A1"
            elif known_words_count < 1500:
                return "A2"
            elif known_words_count < 3000:
                return "B1"
            elif known_words_count < 5000:
                return "B2"
            elif known_words_count < 8000:
                return "C1"
            else:
                return "C2"
                
        except Exception as e:
            self.logger.error(f"Error getting learning level: {e}")
            return "A2"  # Default level
    
    def set_learning_level(self, user_id: str, level: str) -> bool:
        """Set user's learning level (stored implicitly based on vocabulary)"""
        # In this implementation, level is computed based on vocabulary size
        # Could be extended to store explicit user level preferences
        self.logger.info(f"Learning level for {user_id} would be set to {level} (computed dynamically)")
        return True
    
    def add_known_words(self, user_id: str, words: List[str], language: str = "en") -> bool:
        """Add multiple words to user's known vocabulary"""
        try:
            success_count = 0
            for word in words:
                if self.mark_word_learned(user_id, word, language):
                    success_count += 1
            
            self.logger.info(f"Added {success_count}/{len(words)} words for user {user_id}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error adding known words: {e}")
            return False
    
    def get_learning_statistics(self, user_id: str, language: str = "en") -> Dict[str, Any]:
        """Get learning statistics for user"""
        try:
            # Get total known words
            known_words = self.get_known_words(user_id, language)
            total_known = len(known_words)
            
            # Get confidence distribution
            confidence_query = """
                SELECT confidence_level, COUNT(*) as count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = ? AND v.language = ?
                GROUP BY confidence_level
                ORDER BY confidence_level
            """
            confidence_results = self.db.execute_query(confidence_query, (user_id, language))
            confidence_distribution = {row['confidence_level']: row['count'] for row in confidence_results}
            
            # Get recent learning activity
            recent_query = """
                SELECT COUNT(*) as recent_count
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = ? AND v.language = ? 
                AND ulp.learned_at >= date('now', '-7 days')
            """
            recent_results = self.db.execute_query(recent_query, (user_id, language))
            recent_learned = recent_results[0]['recent_count'] if recent_results else 0
            
            # Get most reviewed words
            top_reviewed_query = """
                SELECT v.word, ulp.review_count, ulp.confidence_level
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = ? AND v.language = ?
                ORDER BY ulp.review_count DESC
                LIMIT 10
            """
            top_reviewed_results = self.db.execute_query(top_reviewed_query, (user_id, language))
            top_reviewed = [
                {
                    'word': row['word'],
                    'review_count': row['review_count'],
                    'confidence_level': row['confidence_level']
                }
                for row in top_reviewed_results
            ]
            
            return {
                "total_known": total_known,
                "total_learned": total_known,  # Same as known in this context
                "learning_level": self.get_learning_level(user_id),
                "total_vocabulary": total_known,
                "confidence_distribution": confidence_distribution,
                "recent_learned_7_days": recent_learned,
                "top_reviewed_words": top_reviewed,
                "language": language
            }
            
        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {e}")
            return {"total_known": 0, "total_learned": 0, "error": str(e)}
    
    def _ensure_word_exists(self, word: str, language: str = "en") -> Optional[int]:
        """Ensure word exists in vocabulary table and return its ID"""
        try:
            # Check if word already exists
            existing_query = "SELECT id FROM vocabulary WHERE word = ? AND language = ?"
            existing_results = self.db.execute_query(existing_query, (word, language))
            
            if existing_results:
                return existing_results[0]['id']
            
            # Insert new word
            insert_query = """
                INSERT INTO vocabulary (word, language, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """
            now = datetime.now().isoformat()
            word_id = self.db.execute_insert(insert_query, (word, language, now, now))
            
            return word_id
            
        except Exception as e:
            self.logger.error(f"Error ensuring word exists: {e}")
            return None
    
    def get_word_learning_history(self, user_id: str, word: str, language: str = "en") -> List[Dict[str, Any]]:
        """Get learning history for a specific word"""
        try:
            query = """
                SELECT ulp.learned_at, ulp.confidence_level, ulp.review_count, ulp.last_reviewed
                FROM user_learning_progress ulp
                JOIN vocabulary v ON ulp.word_id = v.id
                WHERE ulp.user_id = ? AND v.word = ? AND v.language = ?
            """
            results = self.db.execute_query(query, (user_id, word.lower(), language))
            
            return [
                {
                    'learned_at': row['learned_at'],
                    'confidence_level': row['confidence_level'],
                    'review_count': row['review_count'],
                    'last_reviewed': row['last_reviewed']
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting word learning history: {e}")
            return []
    
    def get_words_by_confidence(self, user_id: str, confidence_level: int, language: str = "en") -> List[str]:
        """Get words at a specific confidence level"""
        try:
            query = """
                SELECT v.word
                FROM vocabulary v
                JOIN user_learning_progress ulp ON v.id = ulp.word_id
                WHERE ulp.user_id = ? AND ulp.confidence_level = ? AND v.language = ?
                ORDER BY ulp.last_reviewed DESC
            """
            results = self.db.execute_query(query, (user_id, confidence_level, language))
            
            return [row['word'] for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting words by confidence: {e}")
            return []
    
    def remove_word(self, user_id: str, word: str, language: str = "en") -> bool:
        """Remove a word from user's learning progress"""
        try:
            # Get word ID
            word_query = "SELECT id FROM vocabulary WHERE word = ? AND language = ?"
            word_results = self.db.execute_query(word_query, (word.lower(), language))
            
            if not word_results:
                return False
            
            word_id = word_results[0]['id']
            
            # Remove from user progress
            delete_query = "DELETE FROM user_learning_progress WHERE user_id = ? AND word_id = ?"
            rows_affected = self.db.execute_update(delete_query, (user_id, word_id))
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error removing word: {e}")
            return False