"""
User Vocabulary Data Service Implementation
Manages user's known vocabulary and learning progress
"""

from typing import Set, Dict, Any, Optional, List
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from sqlalchemy import select, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_session


class SQLiteUserVocabularyService:
    """
    SQLite-based implementation of user vocabulary service
    Uses async SQLAlchemy for all database operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async for session in get_async_session():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    
    async def is_word_known(self, user_id: str, word: str, language: str = "en") -> bool:
        """Check if user knows a specific word"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT COUNT(*) as count
                    FROM user_learning_progress ulp
                    JOIN vocabulary v ON ulp.word_id = v.id
                    WHERE ulp.user_id = :user_id AND v.word = :word AND v.language = :language
                """)
                result = await session.execute(query, {
                    "user_id": user_id,
                    "word": word.lower(),
                    "language": language
                })
                row = result.fetchone()
                return row[0] > 0 if row else False
                
        except Exception as e:
            self.logger.error(f"Error checking if word is known: {e}")
            return False
    
    async def get_known_words(self, user_id: str, language: str = "en") -> List[str]:
        """Get all words known by user"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT v.word 
                    FROM vocabulary v
                    JOIN user_learning_progress ulp ON v.id = ulp.word_id
                    WHERE ulp.user_id = :user_id AND v.language = :language
                    ORDER BY v.word
                """)
                result = await session.execute(query, {
                    "user_id": user_id,
                    "language": language
                })
                return [row[0] for row in result.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting known words: {e}")
            return []
    
    async def mark_word_learned(self, user_id: str, word: str, language: str = "en") -> bool:
        """Mark word as learned by user"""
        try:
            word_lower = word.lower()
            
            async with self.get_session() as session:
                # First, ensure the word exists in vocabulary table
                word_id = await self._ensure_word_exists(session, word_lower, language)
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
    
    async def get_learning_level(self, user_id: str) -> str:
        """Get user's current learning level"""
        try:
            # Determine level based on vocabulary size
            known_words_count = len(await self.get_known_words(user_id))
            
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
    
    async def set_learning_level(self, user_id: str, level: str) -> bool:
        """Set user's learning level (stored implicitly based on vocabulary)"""
        # In this implementation, level is computed based on vocabulary size
        # Could be extended to store explicit user level preferences
        self.logger.info(f"Learning level for {user_id} would be set to {level} (computed dynamically)")
        return True
    
    async def add_known_words(self, user_id: str, words: List[str], language: str = "en") -> bool:
        """Add multiple words to user's known vocabulary using batch operations"""
        try:
            if not words:
                return True
            
            # Normalize words
            normalized_words = [word.lower().strip() for word in words if word.strip()]
            if not normalized_words:
                return True
            
            async with self.get_session() as session:
                # Step 1: Ensure all words exist in vocabulary table (batch operation)
                word_ids = await self._ensure_words_exist_batch(session, normalized_words, language)
                if not word_ids:
                    self.logger.error("Failed to ensure words exist in vocabulary")
                    return False
                
                # Step 2: Get existing learning progress for these words
                existing_progress = await self._get_existing_progress_batch(session, user_id, list(word_ids.values()))
                
                # Step 3: Prepare and execute operations
                now = datetime.now().isoformat()
                success_count = 0
                
                for word, word_id in word_ids.items():
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
    
    async def get_learning_statistics(self, user_id: str, language: str = "en") -> Dict[str, Any]:
        """Get learning statistics for user"""
        try:
            async with self.get_session() as session:
                # Get total known words
                known_words = await self.get_known_words(user_id, language)
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
                    {
                        'word': row[0],
                        'review_count': row[1],
                        'confidence_level': row[2]
                    }
                    for row in top_reviewed_result.fetchall()
                ]
                
                learning_level = await self.get_learning_level(user_id)
                
                return {
                    "total_known": total_known,
                    "total_learned": total_known,  # Same as known in this context
                    "learning_level": learning_level,
                    "total_vocabulary": total_known,
                    "confidence_distribution": confidence_distribution,
                    "recent_learned_7_days": recent_learned,
                    "top_reviewed_words": top_reviewed,
                    "language": language
                }
                
        except Exception as e:
            self.logger.error(f"Error getting learning statistics: {e}")
            return {"total_known": 0, "total_learned": 0, "error": str(e)}
    
    async def _ensure_word_exists(self, session: AsyncSession, word: str, language: str = "en") -> Optional[int]:
        """Ensure word exists in vocabulary table and return its ID"""
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
            await session.flush()  # Ensure the insert is flushed to get the ID
            
            return result.lastrowid
            
        except Exception as e:
            self.logger.error(f"Error ensuring word exists: {e}")
            return None
    
    async def _ensure_words_exist_batch(self, session: AsyncSession, words: List[str], language: str = "en") -> Dict[str, int]:
        """Ensure multiple words exist in vocabulary table and return word->id mapping"""
        try:
            if not words:
                return {}
            
            # Step 1: Check which words already exist
            placeholders = ','.join([':word' + str(i) for i in range(len(words))])
            existing_query = text(f"""
                SELECT word, id FROM vocabulary 
                WHERE word IN ({placeholders}) AND language = :language
            """)
            params = {f'word{i}': word for i, word in enumerate(words)}
            params['language'] = language
            existing_result = await session.execute(existing_query, params)
            
            # Build mapping of existing words
            word_ids = {row[0]: row[1] for row in existing_result.fetchall()}
            existing_words = set(word_ids.keys())
            
            # Step 2: Insert missing words individually
            missing_words = [word for word in words if word not in existing_words]
            if missing_words:
                now = datetime.now().isoformat()
                insert_query = text("""
                    INSERT INTO vocabulary (word, language, created_at, updated_at)
                    VALUES (:word, :language, :now, :now)
                """)
                
                for word in missing_words:
                    result = await session.execute(insert_query, {
                        "word": word, "language": language, "now": now
                    })
                    word_ids[word] = result.lastrowid
                
                await session.flush()  # Ensure all inserts are flushed
            
            return word_ids
            
        except Exception as e:
            self.logger.error(f"Error ensuring words exist in batch: {e}")
            return {}
    
    async def _get_existing_progress_batch(self, session: AsyncSession, user_id: str, word_ids: List[int]) -> Set[int]:
        """Get existing learning progress for multiple word IDs"""
        try:
            if not word_ids:
                return set()
            
            placeholders = ','.join([':word_id' + str(i) for i in range(len(word_ids))])
            query = text(f"""
                SELECT word_id FROM user_learning_progress 
                WHERE user_id = :user_id AND word_id IN ({placeholders})
            """)
            params = {f'word_id{i}': word_id for i, word_id in enumerate(word_ids)}
            params['user_id'] = user_id
            result = await session.execute(query, params)
            
            return {row[0] for row in result.fetchall()}
            
        except Exception as e:
            self.logger.error(f"Error getting existing progress in batch: {e}")
            return set()
    
    async def get_word_learning_history(self, user_id: str, word: str, language: str = "en") -> List[Dict[str, Any]]:
        """Get learning history for a specific word"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT ulp.learned_at, ulp.confidence_level, ulp.review_count, ulp.last_reviewed
                    FROM user_learning_progress ulp
                    JOIN vocabulary v ON ulp.word_id = v.id
                    WHERE ulp.user_id = :user_id AND v.word = :word AND v.language = :language
                """)
                result = await session.execute(query, {
                    "user_id": user_id,
                    "word": word.lower(),
                    "language": language
                })
                
                return [
                    {
                        'learned_at': row[0],
                        'confidence_level': row[1],
                        'review_count': row[2],
                        'last_reviewed': row[3]
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting word learning history: {e}")
            return []
    
    async def get_words_by_confidence(self, user_id: str, confidence_level: int, language: str = "en", limit: int = 100) -> List[Dict[str, Any]]:
        """Get words by confidence level"""
        try:
            async with self.get_session() as session:
                query = text("""
                    SELECT v.word, ulp.confidence_level, ulp.learned_at, ulp.review_count
                    FROM user_learning_progress ulp
                    JOIN vocabulary v ON ulp.word_id = v.id
                    WHERE ulp.user_id = :user_id AND ulp.confidence_level = :confidence_level AND v.language = :language
                    ORDER BY ulp.learned_at DESC
                    LIMIT :limit
                """)
                result = await session.execute(query, {
                    "user_id": user_id,
                    "confidence_level": confidence_level,
                    "language": language,
                    "limit": limit
                })
                
                return [
                    {
                        'word': row[0],
                        'confidence_level': row[1],
                        'learned_at': row[2],
                        'review_count': row[3]
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting words by confidence: {e}")
            return []
    
    async def remove_word(self, user_id: str, word: str, language: str = "en") -> bool:
        """Remove a word from user's learning progress"""
        try:
            async with self.get_session() as session:
                # First get the word ID
                word_query = text("SELECT id FROM vocabulary WHERE word = :word AND language = :language")
                word_result = await session.execute(word_query, {
                    "word": word.lower(),
                    "language": language
                })
                word_row = word_result.fetchone()
                
                if not word_row:
                    self.logger.warning(f"Word '{word}' not found in vocabulary")
                    return False
                
                word_id = word_row[0]
                
                # Remove from user's learning progress
                delete_query = text("DELETE FROM user_learning_progress WHERE user_id = :user_id AND word_id = :word_id")
                delete_result = await session.execute(delete_query, {
                    "user_id": user_id,
                    "word_id": word_id
                })
                
                await session.commit()
                
                if delete_result.rowcount > 0:
                    self.logger.info(f"Removed word '{word}' from user {user_id}'s learning progress")
                    return True
                else:
                    self.logger.warning(f"Word '{word}' not found in user {user_id}'s learning progress")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error removing word: {e}")
            return False