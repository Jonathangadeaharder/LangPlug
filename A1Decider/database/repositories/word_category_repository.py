#!/usr/bin/env python3
"""
Word Category Repository for A1Decider Database

Handles management of word categories and their associations
with vocabulary words for organized learning.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import sqlite3


class WordCategoryRepository:
    """Repository for word category management and associations."""
    
    def __init__(self, db_manager):
        """
        Initialize the word category repository.
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def create_category(self, name: str, description: Optional[str] = None,
                       language: str = 'de', parent_id: Optional[int] = None) -> int:
        """
        Create a new word category.
        
        Args:
            name: Category name
            description: Optional category description
            language: Language code
            parent_id: Optional parent category ID for hierarchical categories
            
        Returns:
            Category ID
        """
        # Check if category already exists
        existing_id = self.get_category_id(name, language)
        if existing_id:
            return existing_id
        
        query = """
            INSERT INTO word_categories 
            (name, description, language, parent_id)
            VALUES (?, ?, ?, ?)
        """
        
        return self.db.execute_insert(query, (name, description, language, parent_id))
    
    def get_category_id(self, name: str, language: str = 'de') -> Optional[int]:
        """
        Get the ID of a category by name.
        
        Args:
            name: Category name
            language: Language code
            
        Returns:
            Category ID or None if not found
        """
        query = """
            SELECT id FROM word_categories 
            WHERE name = ? AND language = ?
        """
        results = self.db.execute_query(query, (name, language))
        return results[0]['id'] if results else None
    
    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Get category details by ID.
        
        Args:
            category_id: Category ID
            
        Returns:
            Category dictionary or None if not found
        """
        query = """
            SELECT id, name, description, language, parent_id, created_at
            FROM word_categories 
            WHERE id = ?
        """
        
        results = self.db.execute_query(query, (category_id,))
        return dict(results[0]) if results else None
    
    def get_all_categories(self, language: str = 'de') -> List[Dict[str, Any]]:
        """
        Get all categories for a language.
        
        Args:
            language: Language code
            
        Returns:
            List of category dictionaries
        """
        query = """
            SELECT id, name, description, language, parent_id, created_at
            FROM word_categories 
            WHERE language = ?
            ORDER BY name
        """
        
        results = self.db.execute_query(query, (language,))
        return [dict(row) for row in results]
    
    def get_root_categories(self, language: str = 'de') -> List[Dict[str, Any]]:
        """
        Get root categories (categories without parents).
        
        Args:
            language: Language code
            
        Returns:
            List of root category dictionaries
        """
        query = """
            SELECT id, name, description, language, parent_id, created_at
            FROM word_categories 
            WHERE language = ? AND parent_id IS NULL
            ORDER BY name
        """
        
        results = self.db.execute_query(query, (language,))
        return [dict(row) for row in results]
    
    def get_child_categories(self, parent_id: int) -> List[Dict[str, Any]]:
        """
        Get child categories of a parent category.
        
        Args:
            parent_id: Parent category ID
            
        Returns:
            List of child category dictionaries
        """
        query = """
            SELECT id, name, description, language, parent_id, created_at
            FROM word_categories 
            WHERE parent_id = ?
            ORDER BY name
        """
        
        results = self.db.execute_query(query, (parent_id,))
        return [dict(row) for row in results]
    
    def update_category(self, category_id: int, name: Optional[str] = None,
                       description: Optional[str] = None,
                       parent_id: Optional[int] = None) -> bool:
        """
        Update category details.
        
        Args:
            category_id: Category ID to update
            name: New category name
            description: New category description
            parent_id: New parent category ID
            
        Returns:
            True if category was updated, False otherwise
        """
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if parent_id is not None:
            updates.append("parent_id = ?")
            params.append(parent_id)
        
        if not updates:
            return False
        
        params.append(category_id)
        query = f"""
            UPDATE word_categories 
            SET {', '.join(updates)}
            WHERE id = ?
        """
        
        rows_affected = self.db.execute_update(query, tuple(params))
        return rows_affected > 0
    
    def delete_category(self, category_id: int, 
                       delete_associations: bool = True) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: Category ID to delete
            delete_associations: Whether to delete word associations
            
        Returns:
            True if category was deleted, False otherwise
        """
        if delete_associations:
            # Delete word associations first
            self.db.execute_update(
                "DELETE FROM word_category_associations WHERE category_id = ?",
                (category_id,)
            )
        
        # Update child categories to have no parent
        self.db.execute_update(
            "UPDATE word_categories SET parent_id = NULL WHERE parent_id = ?",
            (category_id,)
        )
        
        # Delete the category
        query = "DELETE FROM word_categories WHERE id = ?"
        rows_affected = self.db.execute_update(query, (category_id,))
        return rows_affected > 0
    
    def associate_word_with_category(self, word_id: int, category_id: int) -> int:
        """
        Associate a word with a category.
        
        Args:
            word_id: Vocabulary word ID
            category_id: Category ID
            
        Returns:
            Association ID
        """
        # Check if association already exists
        query = """
            SELECT id FROM word_category_associations 
            WHERE word_id = ? AND category_id = ?
        """
        results = self.db.execute_query(query, (word_id, category_id))
        
        if results:
            return results[0]['id']
        
        # Create new association
        query = """
            INSERT INTO word_category_associations (word_id, category_id)
            VALUES (?, ?)
        """
        
        return self.db.execute_insert(query, (word_id, category_id))
    
    def remove_word_from_category(self, word_id: int, category_id: int) -> bool:
        """
        Remove a word from a category.
        
        Args:
            word_id: Vocabulary word ID
            category_id: Category ID
            
        Returns:
            True if association was removed, False otherwise
        """
        query = """
            DELETE FROM word_category_associations 
            WHERE word_id = ? AND category_id = ?
        """
        
        rows_affected = self.db.execute_update(query, (word_id, category_id))
        return rows_affected > 0
    
    def get_word_categories(self, word_id: int) -> List[Dict[str, Any]]:
        """
        Get all categories associated with a word.
        
        Args:
            word_id: Vocabulary word ID
            
        Returns:
            List of category dictionaries
        """
        query = """
            SELECT wc.id, wc.name, wc.description, wc.language, 
                   wc.parent_id, wc.created_at
            FROM word_categories wc
            JOIN word_category_associations wca ON wc.id = wca.category_id
            WHERE wca.word_id = ?
            ORDER BY wc.name
        """
        
        results = self.db.execute_query(query, (word_id,))
        return [dict(row) for row in results]
    
    def get_words_in_category(self, category_id: int, 
                            include_subcategories: bool = False) -> List[Dict[str, Any]]:
        """
        Get all words in a category.
        
        Args:
            category_id: Category ID
            include_subcategories: Whether to include words from subcategories
            
        Returns:
            List of word dictionaries
        """
        if include_subcategories:
            # Get all descendant category IDs
            category_ids = self._get_descendant_category_ids(category_id)
            category_ids.append(category_id)
            
            placeholders = ','.join(['?' for _ in category_ids])
            query = f"""
                SELECT DISTINCT v.id, v.word, v.lemma, v.frequency, 
                       v.difficulty_level, v.language, v.created_at
                FROM vocabulary v
                JOIN word_category_associations wca ON v.id = wca.word_id
                WHERE wca.category_id IN ({placeholders})
                ORDER BY v.word
            """
            params = tuple(category_ids)
        else:
            query = """
                SELECT v.id, v.word, v.lemma, v.frequency, 
                       v.difficulty_level, v.language, v.created_at
                FROM vocabulary v
                JOIN word_category_associations wca ON v.id = wca.word_id
                WHERE wca.category_id = ?
                ORDER BY v.word
            """
            params = (category_id,)
        
        results = self.db.execute_query(query, params)
        return [dict(row) for row in results]
    
    def _get_descendant_category_ids(self, parent_id: int) -> List[int]:
        """
        Recursively get all descendant category IDs.
        
        Args:
            parent_id: Parent category ID
            
        Returns:
            List of descendant category IDs
        """
        descendant_ids = []
        
        # Get direct children
        query = "SELECT id FROM word_categories WHERE parent_id = ?"
        results = self.db.execute_query(query, (parent_id,))
        
        for row in results:
            child_id = row['id']
            descendant_ids.append(child_id)
            # Recursively get descendants of this child
            descendant_ids.extend(self._get_descendant_category_ids(child_id))
        
        return descendant_ids
    
    def get_category_hierarchy(self, language: str = 'de') -> Dict[str, Any]:
        """
        Get the complete category hierarchy for a language.
        
        Args:
            language: Language code
            
        Returns:
            Nested dictionary representing the category hierarchy
        """
        # Get all categories
        all_categories = self.get_all_categories(language)
        
        # Build hierarchy
        category_map = {cat['id']: cat for cat in all_categories}
        hierarchy = {}
        
        # Add children to their parents
        for category in all_categories:
            category['children'] = []
        
        for category in all_categories:
            if category['parent_id'] is None:
                # Root category
                hierarchy[category['id']] = category
            else:
                # Child category
                parent = category_map.get(category['parent_id'])
                if parent:
                    parent['children'].append(category)
        
        return hierarchy
    
    def search_categories(self, search_term: str, language: str = 'de') -> List[Dict[str, Any]]:
        """
        Search for categories by name or description.
        
        Args:
            search_term: Term to search for
            language: Language code
            
        Returns:
            List of matching categories
        """
        query = """
            SELECT id, name, description, language, parent_id, created_at
            FROM word_categories 
            WHERE (name LIKE ? OR description LIKE ?) AND language = ?
            ORDER BY name
        """
        
        search_pattern = f"%{search_term}%"
        results = self.db.execute_query(
            query, (search_pattern, search_pattern, language)
        )
        return [dict(row) for row in results]
    
    def get_category_statistics(self, category_id: int, 
                              include_subcategories: bool = False) -> Dict[str, Any]:
        """
        Get statistics for a category.
        
        Args:
            category_id: Category ID
            include_subcategories: Whether to include subcategory statistics
            
        Returns:
            Dictionary with category statistics
        """
        stats = {}
        
        # Get category info
        category = self.get_category(category_id)
        if not category:
            return {}
        
        stats['category'] = category
        
        # Count words in category
        words = self.get_words_in_category(category_id, include_subcategories)
        stats['word_count'] = len(words)
        
        if words:
            # Difficulty distribution
            difficulty_counts = {}
            for word in words:
                level = word.get('difficulty_level', 'unknown')
                difficulty_counts[level] = difficulty_counts.get(level, 0) + 1
            stats['difficulty_distribution'] = difficulty_counts
            
            # Average frequency
            frequencies = [word.get('frequency', 0) for word in words]
            stats['average_frequency'] = sum(frequencies) / len(frequencies) if frequencies else 0
        else:
            stats['difficulty_distribution'] = {}
            stats['average_frequency'] = 0
        
        # Count subcategories
        subcategories = self.get_child_categories(category_id)
        stats['subcategory_count'] = len(subcategories)
        
        return stats
    
    def get_popular_categories(self, language: str = 'de', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get categories with the most words.
        
        Args:
            language: Language code
            limit: Maximum number of categories to return
            
        Returns:
            List of popular categories with word counts
        """
        query = """
            SELECT wc.id, wc.name, wc.description, COUNT(wca.word_id) as word_count
            FROM word_categories wc
            LEFT JOIN word_category_associations wca ON wc.id = wca.category_id
            WHERE wc.language = ?
            GROUP BY wc.id, wc.name, wc.description
            ORDER BY word_count DESC, wc.name
            LIMIT ?
        """
        
        results = self.db.execute_query(query, (language, limit))
        return [dict(row) for row in results]
    
    def bulk_associate_words(self, word_ids: List[int], category_id: int) -> int:
        """
        Associate multiple words with a category.
        
        Args:
            word_ids: List of vocabulary word IDs
            category_id: Category ID
            
        Returns:
            Number of associations created
        """
        associations_created = 0
        
        for word_id in word_ids:
            try:
                self.associate_word_with_category(word_id, category_id)
                associations_created += 1
            except sqlite3.IntegrityError:
                # Association already exists, skip
                continue
        
        return associations_created
    
    def clear_word_categories(self, word_id: int) -> int:
        """
        Remove a word from all categories.
        
        Args:
            word_id: Vocabulary word ID
            
        Returns:
            Number of associations removed
        """
        query = "DELETE FROM word_category_associations WHERE word_id = ?"
        return self.db.execute_update(query, (word_id,))
    
    def export_category_structure(self, language: str = 'de') -> Dict[str, Any]:
        """
        Export the complete category structure for backup or migration.
        
        Args:
            language: Language code
            
        Returns:
            Dictionary with complete category structure and associations
        """
        export_data = {
            'categories': self.get_all_categories(language),
            'hierarchy': self.get_category_hierarchy(language),
            'associations': []
        }
        
        # Get all word-category associations
        query = """
            SELECT wca.word_id, wca.category_id, v.word, wc.name as category_name
            FROM word_category_associations wca
            JOIN vocabulary v ON wca.word_id = v.id
            JOIN word_categories wc ON wca.category_id = wc.id
            WHERE wc.language = ?
            ORDER BY wc.name, v.word
        """
        
        results = self.db.execute_query(query, (language,))
        export_data['associations'] = [dict(row) for row in results]
        
        return export_data