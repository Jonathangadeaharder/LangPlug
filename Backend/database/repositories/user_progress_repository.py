#!/usr/bin/env python3
"""
User Progress Repository for A1Decider Database

Handles tracking of user learning progress, sessions,
and word discovery patterns for vocabulary learning.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class UserProgressRepository:
    """Repository for user learning progress and session management."""
    
    def __init__(self, db_manager):
        """
        Initialize the user progress repository.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def create_processing_session(self, session_type: str = 'subtitle_processing',
                                 source_file: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new processing session.
        
        Args:
            session_type: Type of processing session
            source_file: Source file being processed
            metadata: Additional session metadata
            
        Returns:
            Session ID
        """
        import json
        
        query = """
            INSERT INTO processing_sessions 
            (session_type, source_file, metadata)
            VALUES (?, ?, ?)
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        return self.db.execute_insert(query, (session_type, source_file, metadata_json))
    
    def end_processing_session(self, session_id: int, 
                              words_processed: int = 0,
                              new_words_discovered: int = 0) -> bool:
        """
        Mark a processing session as completed.
        
        Args:
            session_id: Session ID to end
            words_processed: Total words processed in session
            new_words_discovered: New words discovered in session
            
        Returns:
            True if session was updated, False otherwise
        """
        query = """
            UPDATE processing_sessions 
            SET end_time = CURRENT_TIMESTAMP,
                words_processed = ?,
                new_words_discovered = ?
            WHERE id = ?
        """
        
        rows_affected = self.db.execute_update(
            query, (words_processed, new_words_discovered, session_id)
        )
        return rows_affected > 0
    
    def record_word_discovery(self, session_id: int, word: str, 
                            discovery_context: Optional[str] = None,
                            frequency_in_session: int = 1) -> int:
        """
        Record a word discovery during a session.
        
        Args:
            session_id: Session ID where word was discovered
            word: The discovered word
            discovery_context: Context where word was found
            frequency_in_session: How many times word appeared in session
            
        Returns:
            Discovery record ID
        """
        query = """
            INSERT INTO session_word_discoveries 
            (session_id, word, discovery_context, frequency_in_session)
            VALUES (?, ?, ?, ?)
        """
        
        return self.db.execute_insert(
            query, (session_id, word.lower(), discovery_context, frequency_in_session)
        )
    
    def record_word_discoveries_batch(self, session_id: int, 
                                    discoveries: List[Dict[str, Any]]) -> int:
        """
        Record multiple word discoveries for a session.
        
        Args:
            session_id: Session ID
            discoveries: List of discovery dictionaries
            
        Returns:
            Number of discoveries recorded
        """
        recorded_count = 0
        
        for discovery in discoveries:
            word = discovery.get('word', '')
            context = discovery.get('context')
            frequency = discovery.get('frequency', 1)
            
            if word:
                self.record_word_discovery(session_id, word, context, frequency)
                recorded_count += 1
        
        return recorded_count
    
    def update_learning_progress(self, word: str, 
                               proficiency_level: str = 'beginner',
                               confidence_score: float = 0.0,
                               language: str = 'de') -> int:
        """
        Update or create learning progress for a word.
        
        Args:
            word: The word being learned
            proficiency_level: Current proficiency level
            confidence_score: Confidence score (0.0 to 1.0)
            language: Language code
            
        Returns:
            Progress record ID
        """
        # Check if progress record exists
        existing_id = self.get_learning_progress_id(word, language)
        
        if existing_id:
            # Update existing record
            query = """
                UPDATE user_learning_progress 
                SET proficiency_level = ?,
                    confidence_score = ?,
                    last_reviewed = CURRENT_TIMESTAMP,
                    review_count = review_count + 1
                WHERE id = ?
            """
            self.db.execute_update(query, (proficiency_level, confidence_score, existing_id))
            return existing_id
        else:
            # Create new record
            query = """
                INSERT INTO user_learning_progress 
                (word, proficiency_level, confidence_score, language, review_count)
                VALUES (?, ?, ?, ?, 1)
            """
            return self.db.execute_insert(
                query, (word.lower(), proficiency_level, confidence_score, language)
            )
    
    def get_learning_progress_id(self, word: str, language: str = 'de') -> Optional[int]:
        """
        Get the learning progress ID for a word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Progress ID or None if not found
        """
        query = """
            SELECT id FROM user_learning_progress 
            WHERE word = ? AND language = ?
        """
        results = self.db.execute_query(query, (word.lower(), language))
        return results[0]['id'] if results else None
    
    def get_learning_progress(self, word: str, language: str = 'de') -> Optional[Dict[str, Any]]:
        """
        Get learning progress for a specific word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Progress dictionary or None if not found
        """
        query = """
            SELECT word, proficiency_level, confidence_score, 
                   first_learned, last_reviewed, review_count
            FROM user_learning_progress 
            WHERE word = ? AND language = ?
        """
        
        results = self.db.execute_query(query, (word.lower(), language))
        return dict(results[0]) if results else None
    
    def get_words_by_proficiency(self, proficiency_level: str,
                               language: str = 'de',
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get words at a specific proficiency level.
        
        Args:
            proficiency_level: Proficiency level to filter by
            language: Language code
            limit: Maximum number of words to return
            
        Returns:
            List of words at the specified proficiency level
        """
        query = """
            SELECT word, proficiency_level, confidence_score, 
                   first_learned, last_reviewed, review_count
            FROM user_learning_progress 
            WHERE proficiency_level = ? AND language = ?
            ORDER BY last_reviewed DESC
            LIMIT ?
        """
        
        results = self.db.execute_query(query, (proficiency_level, language, limit))
        return [dict(row) for row in results]
    
    def get_words_needing_review(self, days_since_review: int = 7,
                               language: str = 'de',
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get words that need review based on time since last review.
        
        Args:
            days_since_review: Days since last review
            language: Language code
            limit: Maximum number of words to return
            
        Returns:
            List of words needing review
        """
        query = """
            SELECT word, proficiency_level, confidence_score, 
                   first_learned, last_reviewed, review_count
            FROM user_learning_progress 
            WHERE language = ? 
            AND last_reviewed <= datetime('now', '-{} days')
            ORDER BY last_reviewed ASC, confidence_score ASC
            LIMIT ?
        """.format(days_since_review)
        
        results = self.db.execute_query(query, (language, limit))
        return [dict(row) for row in results]
    
    def get_recent_sessions(self, days: int = 7, 
                          session_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent processing sessions.
        
        Args:
            days: Number of days to look back
            session_type: Optional session type filter
            
        Returns:
            List of recent sessions
        """
        base_query = """
            SELECT id, session_type, source_file, start_time, end_time,
                   words_processed, new_words_discovered, metadata
            FROM processing_sessions 
            WHERE start_time >= datetime('now', '-{} days')
        """.format(days)
        
        if session_type:
            query = base_query + " AND session_type = ? ORDER BY start_time DESC"
            params = (session_type,)
        else:
            query = base_query + " ORDER BY start_time DESC"
            params = ()
        
        results = self.db.execute_query(query, params)
        return [dict(row) for row in results]
    
    def get_session_discoveries(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get word discoveries for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of word discoveries in the session
        """
        query = """
            SELECT word, discovery_context, frequency_in_session, discovered_at
            FROM session_word_discoveries 
            WHERE session_id = ?
            ORDER BY discovered_at
        """
        
        results = self.db.execute_query(query, (session_id,))
        return [dict(row) for row in results]
    
    def get_learning_statistics(self, language: str = 'de',
                              days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive learning statistics.
        
        Args:
            language: Language code
            days: Number of days for recent statistics
            
        Returns:
            Dictionary with learning statistics
        """
        stats = {}
        
        # Total words being learned
        query = """
            SELECT COUNT(*) as total 
            FROM user_learning_progress 
            WHERE language = ?
        """
        result = self.db.execute_query(query, (language,))
        stats['total_words_learning'] = result[0]['total']
        
        # Proficiency distribution
        query = """
            SELECT proficiency_level, COUNT(*) as count
            FROM user_learning_progress 
            WHERE language = ?
            GROUP BY proficiency_level
        """
        results = self.db.execute_query(query, (language,))
        stats['proficiency_distribution'] = {row['proficiency_level']: row['count'] for row in results}
        
        # Average confidence score
        query = """
            SELECT AVG(confidence_score) as avg_confidence
            FROM user_learning_progress 
            WHERE language = ?
        """
        result = self.db.execute_query(query, (language,))
        stats['average_confidence'] = result[0]['avg_confidence'] or 0
        
        # Recent activity (last N days)
        query = """
            SELECT COUNT(*) as recent_sessions
            FROM processing_sessions 
            WHERE start_time >= datetime('now', '-{} days')
        """.format(days)
        result = self.db.execute_query(query)
        stats['recent_sessions'] = result[0]['recent_sessions']
        
        # Words discovered recently
        query = """
            SELECT COUNT(DISTINCT swd.word) as recent_discoveries
            FROM session_word_discoveries swd
            JOIN processing_sessions ps ON swd.session_id = ps.id
            WHERE ps.start_time >= datetime('now', '-{} days')
        """.format(days)
        result = self.db.execute_query(query)
        stats['recent_word_discoveries'] = result[0]['recent_discoveries']
        
        # Words needing review
        query = """
            SELECT COUNT(*) as needs_review
            FROM user_learning_progress 
            WHERE language = ? 
            AND last_reviewed <= datetime('now', '-7 days')
        """
        result = self.db.execute_query(query, (language,))
        stats['words_needing_review'] = result[0]['needs_review']
        
        # Most active days
        query = """
            SELECT DATE(start_time) as session_date, COUNT(*) as session_count
            FROM processing_sessions 
            WHERE start_time >= datetime('now', '-{} days')
            GROUP BY DATE(start_time)
            ORDER BY session_count DESC
            LIMIT 5
        """.format(days)
        results = self.db.execute_query(query)
        stats['most_active_days'] = [(row['session_date'], row['session_count']) for row in results]
        
        return stats
    
    def get_learning_streak(self, language: str = 'de') -> Dict[str, Any]:
        """
        Calculate learning streak information.
        
        Args:
            language: Language code
            
        Returns:
            Dictionary with streak information
        """
        # Get days with learning activity
        query = """
            SELECT DISTINCT DATE(start_time) as activity_date
            FROM processing_sessions 
            WHERE start_time >= datetime('now', '-90 days')
            ORDER BY activity_date DESC
        """
        
        results = self.db.execute_query(query)
        activity_dates = [row['activity_date'] for row in results]
        
        if not activity_dates:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_activity': None
            }
        
        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        
        for i, date_str in enumerate(activity_dates):
            activity_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            days_diff = (today - activity_date).days
            
            if days_diff == i:  # Consecutive days
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 1
        
        for i in range(1, len(activity_dates)):
            prev_date = datetime.strptime(activity_dates[i-1], '%Y-%m-%d').date()
            curr_date = datetime.strptime(activity_dates[i], '%Y-%m-%d').date()
            
            if (prev_date - curr_date).days == 1:  # Consecutive days
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_activity': activity_dates[0] if activity_dates else None,
            'total_active_days': len(activity_dates)
        }
    
    def delete_learning_progress(self, word: str, language: str = 'de') -> bool:
        """
        Delete learning progress for a word.
        
        Args:
            word: The word to remove progress for
            language: Language code
            
        Returns:
            True if progress was deleted, False otherwise
        """
        query = """
            DELETE FROM user_learning_progress 
            WHERE word = ? AND language = ?
        """
        
        rows_affected = self.db.execute_update(query, (word.lower(), language))
        return rows_affected > 0
    
    def clear_old_sessions(self, days_to_keep: int = 90) -> int:
        """
        Clear old processing sessions and their discoveries.
        
        Args:
            days_to_keep: Number of days of sessions to keep
            
        Returns:
            Number of sessions removed
        """
        # First, get session IDs to be deleted
        query = """
            SELECT id FROM processing_sessions 
            WHERE start_time < datetime('now', '-{} days')
        """.format(days_to_keep)
        
        sessions_to_delete = self.db.execute_query(query)
        session_ids = [row['id'] for row in sessions_to_delete]
        
        if not session_ids:
            return 0
        
        # Delete word discoveries for these sessions
        placeholders = ','.join(['?' for _ in session_ids])
        query = f"""
            DELETE FROM session_word_discoveries 
            WHERE session_id IN ({placeholders})
        """
        self.db.execute_update(query, tuple(session_ids))
        
        # Delete the sessions
        query = f"""
            DELETE FROM processing_sessions 
            WHERE id IN ({placeholders})
        """
        rows_affected = self.db.execute_update(query, tuple(session_ids))
        
        return rows_affected