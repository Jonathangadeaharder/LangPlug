#!/usr/bin/env python3
"""
Vocabulary Repository for A1Decider Database

Handles all vocabulary-related database operations including
word storage, retrieval, and category management.
"""

from typing import List, Set, Optional, Dict, Any


class VocabularyRepository:
    """Repository for vocabulary-related database operations."""
    
    def __init__(self, db_manager):
        """
        Initialize the vocabulary repository.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def add_word(self, word: str, lemma: Optional[str] = None, 
                 language: str = 'de', difficulty_level: Optional[str] = None,
                 word_type: Optional[str] = None) -> int:
        """
        Add a new word to the vocabulary.
        
        Args:
            word: The word to add
            lemma: Lemmatized form of the word
            language: Language code (default: 'de')
            difficulty_level: Difficulty level (A1, A2, B1, etc.)
            word_type: Type of word (noun, verb, etc.)
            
        Returns:
            The ID of the inserted word
        """
        query = """
            INSERT OR IGNORE INTO vocabulary 
            (word, lemma, language, difficulty_level, word_type)
            VALUES (?, ?, ?, ?, ?)
        """
        
        word_id = self.db.execute_insert(
            query, (word.lower(), lemma, language, difficulty_level, word_type)
        )
        
        # If word already exists, get its ID
        if word_id == 0:
            word_id = self.get_word_id(word, language)
        
        return word_id
    
    def add_words_batch(self, words: List[Dict[str, Any]]) -> int:
        """
        Add multiple words in a batch operation.
        
        Args:
            words: List of word dictionaries with keys: word, lemma, language, etc.
            
        Returns:
            Number of words added
        """
        query = """
            INSERT OR IGNORE INTO vocabulary 
            (word, lemma, language, difficulty_level, word_type)
            VALUES (?, ?, ?, ?, ?)
        """
        
        params_list = []
        for word_data in words:
            params_list.append((
                word_data.get('word', '').lower(),
                word_data.get('lemma'),
                word_data.get('language', 'de'),
                word_data.get('difficulty_level'),
                word_data.get('word_type')
            ))
        
        return self.db.execute_many(query, params_list)
    
    def get_word_id(self, word: str, language: str = 'de') -> Optional[int]:
        """
        Get the ID of a word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Word ID or None if not found
        """
        query = "SELECT id FROM vocabulary WHERE word = ? AND language = ?"
        results = self.db.execute_query(query, (word.lower(), language))
        return results[0]['id'] if results else None
    
    def word_exists(self, word: str, language: str = 'de') -> bool:
        """
        Check if a word exists in the vocabulary.
        
        Args:
            word: The word to check
            language: Language code
            
        Returns:
            True if word exists, False otherwise
        """
        return self.get_word_id(word, language) is not None
    
    def get_words_by_category(self, category_name: str) -> Set[str]:
        """
        Get all words belonging to a specific category.
        
        Args:
            category_name: Name of the category
            
        Returns:
            Set of words in the category
        """
        query = """
            SELECT v.word 
            FROM vocabulary v
            JOIN word_category_associations wca ON v.id = wca.word_id
            JOIN word_categories wc ON wca.category_id = wc.id
            WHERE wc.name = ? AND wc.is_active = TRUE
        """
        
        results = self.db.execute_query(query, (category_name,))
        return {row['word'] for row in results}
    
    def get_all_known_words(self, language: str = 'de') -> Set[str]:
        """
        Get all known words from all active categories.
        
        Args:
            language: Language code
            
        Returns:
            Set of all known words
        """
        query = """
            SELECT DISTINCT v.word 
            FROM vocabulary v
            JOIN word_category_associations wca ON v.id = wca.word_id
            JOIN word_categories wc ON wca.category_id = wc.id
            WHERE v.language = ? AND wc.is_active = TRUE
        """
        
        results = self.db.execute_query(query, (language,))
        return {row['word'] for row in results}
    
    def get_words_by_difficulty(self, difficulty_level: str, 
                               language: str = 'de') -> Set[str]:
        """
        Get words by difficulty level.
        
        Args:
            difficulty_level: Difficulty level (A1, A2, etc.)
            language: Language code
            
        Returns:
            Set of words at the specified difficulty level
        """
        query = """
            SELECT word FROM vocabulary 
            WHERE difficulty_level = ? AND language = ?
        """
        
        results = self.db.execute_query(query, (difficulty_level, language))
        return {row['word'] for row in results}
    
    def associate_word_with_category(self, word_id: int, category_id: int) -> bool:
        """
        Associate a word with a category.
        
        Args:
            word_id: ID of the word
            category_id: ID of the category
            
        Returns:
            True if association was created, False otherwise
        """
        query = """
            INSERT OR IGNORE INTO word_category_associations 
            (word_id, category_id) VALUES (?, ?)
        """
        
        rows_affected = self.db.execute_update(query, (word_id, category_id))
        return rows_affected > 0
    
    def remove_word_from_category(self, word_id: int, category_id: int) -> bool:
        """
        Remove a word from a category.
        
        Args:
            word_id: ID of the word
            category_id: ID of the category
            
        Returns:
            True if association was removed, False otherwise
        """
        query = """
            DELETE FROM word_category_associations 
            WHERE word_id = ? AND category_id = ?
        """
        
        rows_affected = self.db.execute_update(query, (word_id, category_id))
        return rows_affected > 0
    
    def search_words(self, search_term: str, language: str = 'de', 
                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for words matching a term.
        
        Args:
            search_term: Term to search for
            language: Language code
            limit: Maximum number of results
            
        Returns:
            List of word dictionaries
        """
        query = """
            SELECT v.*, GROUP_CONCAT(wc.name) as categories
            FROM vocabulary v
            LEFT JOIN word_category_associations wca ON v.id = wca.word_id
            LEFT JOIN word_categories wc ON wca.category_id = wc.id
            WHERE (v.word LIKE ? OR v.lemma LIKE ?) AND v.language = ?
            GROUP BY v.id
            ORDER BY v.word
            LIMIT ?
        """
        
        search_pattern = f"%{search_term.lower()}%"
        results = self.db.execute_query(
            query, (search_pattern, search_pattern, language, limit)
        )
        
        return [dict(row) for row in results]
    
    def get_word_details(self, word: str, language: str = 'de') -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a word.
        
        Args:
            word: The word to look up
            language: Language code
            
        Returns:
            Word details dictionary or None if not found
        """
        query = """
            SELECT v.*, GROUP_CONCAT(wc.name) as categories
            FROM vocabulary v
            LEFT JOIN word_category_associations wca ON v.id = wca.word_id
            LEFT JOIN word_categories wc ON wca.category_id = wc.id
            WHERE v.word = ? AND v.language = ?
            GROUP BY v.id
        """
        
        results = self.db.execute_query(query, (word.lower(), language))
        return dict(results[0]) if results else None
    
    def update_word(self, word_id: int, **kwargs) -> bool:
        """
        Update word properties.
        
        Args:
            word_id: ID of the word to update
            **kwargs: Fields to update
            
        Returns:
            True if word was updated, False otherwise
        """
        if not kwargs:
            return False
        
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for field, value in kwargs.items():
            if field in ['lemma', 'difficulty_level', 'word_type']:
                set_clauses.append(f"{field} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(word_id)
        
        query = f"""
            UPDATE vocabulary 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """
        
        rows_affected = self.db.execute_update(query, tuple(params))
        return rows_affected > 0
    
    def delete_word(self, word_id: int) -> bool:
        """
        Delete a word from the vocabulary.
        
        Args:
            word_id: ID of the word to delete
            
        Returns:
            True if word was deleted, False otherwise
        """
        query = "DELETE FROM vocabulary WHERE id = ?"
        rows_affected = self.db.execute_update(query, (word_id,))
        return rows_affected > 0
    
    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """
        Get vocabulary statistics.
        
        Returns:
            Dictionary with vocabulary statistics
        """
        stats = {}
        
        # Total word count
        query = "SELECT COUNT(*) as total FROM vocabulary"
        result = self.db.execute_query(query)
        stats['total_words'] = result[0]['total']
        
        # Words by language
        query = """
            SELECT language, COUNT(*) as count 
            FROM vocabulary 
            GROUP BY language
        """
        results = self.db.execute_query(query)
        stats['by_language'] = {row['language']: row['count'] for row in results}
        
        # Words by difficulty
        query = """
            SELECT difficulty_level, COUNT(*) as count 
            FROM vocabulary 
            WHERE difficulty_level IS NOT NULL
            GROUP BY difficulty_level
        """
        results = self.db.execute_query(query)
        stats['by_difficulty'] = {row['difficulty_level']: row['count'] for row in results}
        
        # Words by category
        query = """
            SELECT wc.name, COUNT(DISTINCT v.id) as count
            FROM word_categories wc
            LEFT JOIN word_category_associations wca ON wc.id = wca.category_id
            LEFT JOIN vocabulary v ON wca.word_id = v.id
            WHERE wc.is_active = TRUE
            GROUP BY wc.id, wc.name
        """
        results = self.db.execute_query(query)
        stats['by_category'] = {row['name']: row['count'] for row in results}
        
        return stats