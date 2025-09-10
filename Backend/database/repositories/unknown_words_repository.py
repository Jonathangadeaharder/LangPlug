#!/usr/bin/env python3
"""
Unknown Words Repository for A1Decider Database

Handles tracking of unknown words, their frequencies,
and discovery patterns for vocabulary learning.
"""

from typing import List, Dict, Any, Optional


class UnknownWordsRepository:
    """Repository for unknown words tracking and management."""
    
    def __init__(self, db_manager):
        """
        Initialize the unknown words repository.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def add_unknown_word(self, word: str, lemma: Optional[str] = None,
                        language: str = 'de', frequency: int = 1) -> int:
        """
        Add or update an unknown word's frequency.
        
        Args:
            word: The unknown word
            lemma: Lemmatized form of the word
            language: Language code
            frequency: Frequency count to add
            
        Returns:
            The ID of the unknown word record
        """
        # Check if word already exists
        existing_id = self.get_unknown_word_id(word, language)
        
        if existing_id:
            # Update existing record
            query = """
                UPDATE unknown_words 
                SET frequency_count = frequency_count + ?,
                    last_encountered = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self.db.execute_update(query, (frequency, existing_id))
            return existing_id
        else:
            # Insert new record
            query = """
                INSERT INTO unknown_words 
                (word, lemma, frequency_count, language)
                VALUES (?, ?, ?, ?)
            """
            return self.db.execute_insert(
                query, (word.lower(), lemma, frequency, language)
            )
    
    def add_unknown_words_batch(self, words_data: List[Dict[str, Any]]) -> int:
        """
        Add multiple unknown words in a batch operation.
        
        Args:
            words_data: List of word dictionaries with frequency data
            
        Returns:
            Number of words processed
        """
        processed_count = 0
        
        for word_data in words_data:
            word = word_data.get('word', '')
            frequency = word_data.get('frequency', 1)
            lemma = word_data.get('lemma')
            language = word_data.get('language', 'de')
            
            if word:
                self.add_unknown_word(word, lemma, language, frequency)
                processed_count += 1
        
        return processed_count
    
    def get_unknown_word_id(self, word: str, language: str = 'de') -> Optional[int]:
        """
        Get the ID of an unknown word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Unknown word ID or None if not found
        """
        query = "SELECT id FROM unknown_words WHERE word = ? AND language = ?"
        results = self.db.execute_query(query, (word.lower(), language))
        return results[0]['id'] if results else None
    
    def get_unknown_word_frequency(self, word: str, language: str = 'de') -> int:
        """
        Get the frequency count of an unknown word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Frequency count (0 if word not found)
        """
        query = """
            SELECT frequency_count FROM unknown_words 
            WHERE word = ? AND language = ?
        """
        results = self.db.execute_query(query, (word.lower(), language))
        return results[0]['frequency_count'] if results else 0
    
    def get_most_frequent_unknown_words(self, limit: int = 50, 
                                       language: str = 'de') -> List[Dict[str, Any]]:
        """
        Get the most frequently encountered unknown words.
        
        Args:
            limit: Maximum number of words to return
            language: Language code
            
        Returns:
            List of unknown word dictionaries sorted by frequency
        """
        query = """
            SELECT word, lemma, frequency_count, first_encountered, last_encountered
            FROM unknown_words 
            WHERE language = ?
            ORDER BY frequency_count DESC, last_encountered DESC
            LIMIT ?
        """
        
        results = self.db.execute_query(query, (language, limit))
        return [dict(row) for row in results]
    
    def get_recently_discovered_words(self, days: int = 7, 
                                     language: str = 'de') -> List[Dict[str, Any]]:
        """
        Get recently discovered unknown words.
        
        Args:
            days: Number of days to look back
            language: Language code
            
        Returns:
            List of recently discovered unknown words
        """
        query = """
            SELECT word, lemma, frequency_count, first_encountered, last_encountered
            FROM unknown_words 
            WHERE language = ? 
            AND first_encountered >= datetime('now', '-{} days')
            ORDER BY first_encountered DESC
        """.format(days)
        
        results = self.db.execute_query(query, (language,))
        return [dict(row) for row in results]
    
    def search_unknown_words(self, search_term: str, language: str = 'de',
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for unknown words matching a term.
        
        Args:
            search_term: Term to search for
            language: Language code
            limit: Maximum number of results
            
        Returns:
            List of matching unknown words
        """
        query = """
            SELECT word, lemma, frequency_count, first_encountered, last_encountered
            FROM unknown_words 
            WHERE (word LIKE ? OR lemma LIKE ?) AND language = ?
            ORDER BY frequency_count DESC
            LIMIT ?
        """
        
        search_pattern = f"%{search_term.lower()}%"
        results = self.db.execute_query(
            query, (search_pattern, search_pattern, language, limit)
        )
        return [dict(row) for row in results]
    
    def get_unknown_words_by_frequency_range(self, min_freq: int, max_freq: int,
                                           language: str = 'de') -> List[Dict[str, Any]]:
        """
        Get unknown words within a frequency range.
        
        Args:
            min_freq: Minimum frequency
            max_freq: Maximum frequency
            language: Language code
            
        Returns:
            List of unknown words in the frequency range
        """
        query = """
            SELECT word, lemma, frequency_count, first_encountered, last_encountered
            FROM unknown_words 
            WHERE frequency_count BETWEEN ? AND ? AND language = ?
            ORDER BY frequency_count DESC
        """
        
        results = self.db.execute_query(query, (min_freq, max_freq, language))
        return [dict(row) for row in results]
    
    def mark_word_as_learned(self, word: str, language: str = 'de') -> bool:
        """
        Remove a word from unknown words (mark as learned).
        
        Args:
            word: The word that was learned
            language: Language code
            
        Returns:
            True if word was removed, False otherwise
        """
        query = "DELETE FROM unknown_words WHERE word = ? AND language = ?"
        rows_affected = self.db.execute_update(query, (word.lower(), language))
        return rows_affected > 0
    
    def mark_words_as_learned_batch(self, words: List[str], 
                                   language: str = 'de') -> int:
        """
        Mark multiple words as learned (remove from unknown words).
        
        Args:
            words: List of words to mark as learned
            language: Language code
            
        Returns:
            Number of words removed
        """
        if not words:
            return 0
        
        placeholders = ','.join(['?' for _ in words])
        query = f"""
            DELETE FROM unknown_words 
            WHERE word IN ({placeholders}) AND language = ?
        """
        
        params = [word.lower() for word in words] + [language]
        return self.db.execute_update(query, tuple(params))
    
    def update_word_frequency(self, word: str, new_frequency: int,
                            language: str = 'de') -> bool:
        """
        Update the frequency of an unknown word.
        
        Args:
            word: The word to update
            new_frequency: New frequency count
            language: Language code
            
        Returns:
            True if word was updated, False otherwise
        """
        query = """
            UPDATE unknown_words 
            SET frequency_count = ?, last_encountered = CURRENT_TIMESTAMP
            WHERE word = ? AND language = ?
        """
        
        rows_affected = self.db.execute_update(
            query, (new_frequency, word.lower(), language)
        )
        return rows_affected > 0
    
    def get_unknown_words_stats(self, language: str = 'de') -> Dict[str, Any]:
        """
        Get statistics about unknown words.
        
        Args:
            language: Language code
            
        Returns:
            Dictionary with unknown words statistics
        """
        stats = {}
        
        # Total unknown words
        query = "SELECT COUNT(*) as total FROM unknown_words WHERE language = ?"
        result = self.db.execute_query(query, (language,))
        stats['total_unknown_words'] = result[0]['total']
        
        # Total frequency count
        query = """
            SELECT SUM(frequency_count) as total_frequency 
            FROM unknown_words WHERE language = ?
        """
        result = self.db.execute_query(query, (language,))
        stats['total_frequency'] = result[0]['total_frequency'] or 0
        
        # Average frequency
        if stats['total_unknown_words'] > 0:
            stats['average_frequency'] = stats['total_frequency'] / stats['total_unknown_words']
        else:
            stats['average_frequency'] = 0
        
        # Frequency distribution
        query = """
            SELECT 
                CASE 
                    WHEN frequency_count = 1 THEN '1'
                    WHEN frequency_count BETWEEN 2 AND 5 THEN '2-5'
                    WHEN frequency_count BETWEEN 6 AND 10 THEN '6-10'
                    WHEN frequency_count BETWEEN 11 AND 20 THEN '11-20'
                    ELSE '20+'
                END as frequency_range,
                COUNT(*) as count
            FROM unknown_words 
            WHERE language = ?
            GROUP BY frequency_range
        """
        results = self.db.execute_query(query, (language,))
        stats['frequency_distribution'] = {row['frequency_range']: row['count'] for row in results}
        
        # Recent discoveries (last 7 days)
        query = """
            SELECT COUNT(*) as recent_count 
            FROM unknown_words 
            WHERE language = ? AND first_encountered >= datetime('now', '-7 days')
        """
        result = self.db.execute_query(query, (language,))
        stats['recent_discoveries'] = result[0]['recent_count']
        
        # Top 10 most frequent
        query = """
            SELECT word, frequency_count 
            FROM unknown_words 
            WHERE language = ?
            ORDER BY frequency_count DESC 
            LIMIT 10
        """
        results = self.db.execute_query(query, (language,))
        stats['top_frequent'] = [(row['word'], row['frequency_count']) for row in results]
        
        return stats
    
    def export_unknown_words(self, language: str = 'de') -> Dict[str, int]:
        """
        Export all unknown words as a dictionary (compatible with old JSON format).
        
        Args:
            language: Language code
            
        Returns:
            Dictionary mapping words to frequency counts
        """
        query = """
            SELECT word, frequency_count 
            FROM unknown_words 
            WHERE language = ?
            ORDER BY word
        """
        
        results = self.db.execute_query(query, (language,))
        return {row['word']: row['frequency_count'] for row in results}
    
    def clear_unknown_words(self, language: str = 'de') -> int:
        """
        Clear all unknown words for a language.
        
        Args:
            language: Language code
            
        Returns:
            Number of words removed
        """
        query = "DELETE FROM unknown_words WHERE language = ?"
        return self.db.execute_update(query, (language,))