#!/usr/bin/env python3
"""
Test Suite for A1Decider Database Components

Comprehensive tests for database manager, repositories, and migration.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from database_manager import DatabaseManager
from repositories.vocabulary_repository import VocabularyRepository
from repositories.unknown_words_repository import UnknownWordsRepository
from repositories.word_category_repository import WordCategoryRepository
from repositories.user_progress_repository import UserProgressRepository
from migration import DataMigration
from config import DatabaseConfig, get_database_config, reset_config


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_create_database(self):
        """Test database creation."""
        self.db_manager.create_database()
        self.assertTrue(os.path.exists(self.db_path))
        
        # Test that tables are created
        tables = self.db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [row['name'] for row in tables]
        
        expected_tables = [
            'vocabulary', 'unknown_words', 'word_categories',
            'word_category_associations', 'user_learning_progress',
            'processing_sessions', 'session_word_discoveries'
        ]
        
        for table in expected_tables:
            self.assertIn(table, table_names)
    
    def test_connection_management(self):
        """Test database connection management."""
        self.db_manager.create_database()
        
        # Test getting connection
        conn = self.db_manager.get_connection()
        self.assertIsNotNone(conn)
        
        # Test connection is working
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
    
    def test_transaction_management(self):
        """Test transaction management."""
        self.db_manager.create_database()
        
        # Test successful transaction
        with self.db_manager.transaction():
            self.db_manager.execute_update(
                "INSERT INTO vocabulary (word, language) VALUES (?, ?)",
                ('test', 'de')
            )
        
        # Verify data was committed
        results = self.db_manager.execute_query(
            "SELECT word FROM vocabulary WHERE word = ?", ('test',)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['word'], 'test')
    
    def test_backup_database(self):
        """Test database backup functionality."""
        self.db_manager.create_database()
        
        # Add some test data
        self.db_manager.execute_update(
            "INSERT INTO vocabulary (word, language) VALUES (?, ?)",
            ('backup_test', 'de')
        )
        
        # Create backup
        backup_path = self.db_manager.backup_database()
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup contains data
        backup_manager = DatabaseManager(backup_path)
        results = backup_manager.execute_query(
            "SELECT word FROM vocabulary WHERE word = ?", ('backup_test',)
        )
        self.assertEqual(len(results), 1)


class TestVocabularyRepository(unittest.TestCase):
    """Test cases for VocabularyRepository."""
    
    def setUp(self):
        """Set up test database and repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_database()
        self.repo = VocabularyRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_add_word(self):
        """Test adding a vocabulary word."""
        word_id = self.repo.add_word(
            word='test',
            frequency=5,
            difficulty_level='beginner',
            language='de'
        )
        
        self.assertIsNotNone(word_id)
        self.assertIsInstance(word_id, int)
        
        # Verify word was added
        word = self.repo.get_word('test')
        self.assertIsNotNone(word)
        self.assertEqual(word['word'], 'test')
        self.assertEqual(word['frequency'], 5)
        self.assertEqual(word['difficulty_level'], 'beginner')
    
    def test_duplicate_word(self):
        """Test handling of duplicate words."""
        # Add word first time
        word_id1 = self.repo.add_word('duplicate', language='de')
        
        # Try to add same word again
        word_id2 = self.repo.add_word('duplicate', language='de')
        
        # Should return the same ID
        self.assertEqual(word_id1, word_id2)
    
    def test_search_words(self):
        """Test word search functionality."""
        # Add test words
        self.repo.add_word('apple', language='en')
        self.repo.add_word('application', language='en')
        self.repo.add_word('banana', language='en')
        
        # Search for words containing 'app'
        results = self.repo.search_words('app', language='en')
        
        self.assertEqual(len(results), 2)
        words = [r['word'] for r in results]
        self.assertIn('apple', words)
        self.assertIn('application', words)
        self.assertNotIn('banana', words)
    
    def test_get_words_by_difficulty(self):
        """Test filtering words by difficulty level."""
        # Add words with different difficulty levels
        self.repo.add_word('easy', difficulty_level='beginner')
        self.repo.add_word('medium', difficulty_level='intermediate')
        self.repo.add_word('hard', difficulty_level='advanced')
        
        # Get beginner words
        beginner_words = self.repo.get_words_by_difficulty('beginner')
        self.assertEqual(len(beginner_words), 1)
        self.assertEqual(beginner_words[0]['word'], 'easy')
    
    def test_update_word_frequency(self):
        """Test updating word frequency."""
        word_id = self.repo.add_word('frequency_test', frequency=1)
        
        # Update frequency
        success = self.repo.update_word_frequency('frequency_test', 10)
        self.assertTrue(success)
        
        # Verify update
        word = self.repo.get_word('frequency_test')
        self.assertEqual(word['frequency'], 10)


class TestUnknownWordsRepository(unittest.TestCase):
    """Test cases for UnknownWordsRepository."""
    
    def setUp(self):
        """Set up test database and repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_database()
        self.repo = UnknownWordsRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_add_unknown_word(self):
        """Test adding an unknown word."""
        word_id = self.repo.add_unknown_word('unknown', frequency=3)
        
        self.assertIsNotNone(word_id)
        
        # Verify word was added
        frequency = self.repo.get_unknown_word_frequency('unknown')
        self.assertEqual(frequency, 3)
    
    def test_update_frequency(self):
        """Test updating unknown word frequency."""
        # Add word with initial frequency
        self.repo.add_unknown_word('update_test', frequency=1)
        
        # Add same word again (should update frequency)
        self.repo.add_unknown_word('update_test', frequency=2)
        
        # Verify frequency was updated
        frequency = self.repo.get_unknown_word_frequency('update_test')
        self.assertEqual(frequency, 3)  # 1 + 2
    
    def test_most_frequent_words(self):
        """Test getting most frequent unknown words."""
        # Add words with different frequencies
        self.repo.add_unknown_word('rare', frequency=1)
        self.repo.add_unknown_word('common', frequency=10)
        self.repo.add_unknown_word('medium', frequency=5)
        
        # Get most frequent words
        frequent_words = self.repo.get_most_frequent_unknown_words(limit=2)
        
        self.assertEqual(len(frequent_words), 2)
        self.assertEqual(frequent_words[0]['word'], 'common')
        self.assertEqual(frequent_words[1]['word'], 'medium')
    
    def test_mark_word_as_learned(self):
        """Test marking word as learned (removing from unknown words)."""
        # Add unknown word
        self.repo.add_unknown_word('learned_word', frequency=5)
        
        # Verify it exists
        frequency = self.repo.get_unknown_word_frequency('learned_word')
        self.assertEqual(frequency, 5)
        
        # Mark as learned
        success = self.repo.mark_word_as_learned('learned_word')
        self.assertTrue(success)
        
        # Verify it's removed
        frequency = self.repo.get_unknown_word_frequency('learned_word')
        self.assertEqual(frequency, 0)


class TestWordCategoryRepository(unittest.TestCase):
    """Test cases for WordCategoryRepository."""
    
    def setUp(self):
        """Set up test database and repositories."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_database()
        self.category_repo = WordCategoryRepository(self.db_manager)
        self.vocab_repo = VocabularyRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_create_category(self):
        """Test creating a word category."""
        category_id = self.category_repo.create_category(
            name='Test Category',
            description='A test category',
            language='de'
        )
        
        self.assertIsNotNone(category_id)
        
        # Verify category was created
        category = self.category_repo.get_category(category_id)
        self.assertIsNotNone(category)
        self.assertEqual(category['name'], 'Test Category')
    
    def test_associate_word_with_category(self):
        """Test associating a word with a category."""
        # Create category and word
        category_id = self.category_repo.create_category('Nouns', language='de')
        word_id = self.vocab_repo.add_word('house', language='de')
        
        # Associate word with category
        association_id = self.category_repo.associate_word_with_category(
            word_id, category_id
        )
        
        self.assertIsNotNone(association_id)
        
        # Verify association
        categories = self.category_repo.get_word_categories(word_id)
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['name'], 'Nouns')
    
    def test_get_words_in_category(self):
        """Test getting words in a category."""
        # Create category and words
        category_id = self.category_repo.create_category('Verbs', language='de')
        word1_id = self.vocab_repo.add_word('run', language='de')
        word2_id = self.vocab_repo.add_word('jump', language='de')
        word3_id = self.vocab_repo.add_word('house', language='de')  # Not a verb
        
        # Associate verbs with category
        self.category_repo.associate_word_with_category(word1_id, category_id)
        self.category_repo.associate_word_with_category(word2_id, category_id)
        
        # Get words in category
        words = self.category_repo.get_words_in_category(category_id)
        
        self.assertEqual(len(words), 2)
        word_names = [w['word'] for w in words]
        self.assertIn('run', word_names)
        self.assertIn('jump', word_names)
        self.assertNotIn('house', word_names)
    
    def test_hierarchical_categories(self):
        """Test hierarchical category structure."""
        # Create parent and child categories
        parent_id = self.category_repo.create_category('Grammar', language='de')
        child_id = self.category_repo.create_category(
            'Nouns', language='de', parent_id=parent_id
        )
        
        # Verify hierarchy
        child_category = self.category_repo.get_category(child_id)
        self.assertEqual(child_category['parent_id'], parent_id)
        
        # Get child categories
        children = self.category_repo.get_child_categories(parent_id)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0]['name'], 'Nouns')


class TestUserProgressRepository(unittest.TestCase):
    """Test cases for UserProgressRepository."""
    
    def setUp(self):
        """Set up test database and repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_database()
        self.repo = UserProgressRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_create_processing_session(self):
        """Test creating a processing session."""
        session_id = self.repo.create_processing_session(
            session_type='test_session',
            source_file='test.txt',
            metadata={'test': 'data'}
        )
        
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, int)
    
    def test_update_learning_progress(self):
        """Test updating learning progress for a word."""
        progress_id = self.repo.update_learning_progress(
            word='learn_test',
            proficiency_level='intermediate',
            confidence_score=0.7,
            language='de'
        )
        
        self.assertIsNotNone(progress_id)
        
        # Verify progress was recorded
        progress = self.repo.get_learning_progress('learn_test')
        self.assertIsNotNone(progress)
        self.assertEqual(progress['proficiency_level'], 'intermediate')
        self.assertEqual(progress['confidence_score'], 0.7)
    
    def test_get_words_by_proficiency(self):
        """Test getting words by proficiency level."""
        # Add words with different proficiency levels
        self.repo.update_learning_progress('easy', proficiency_level='beginner')
        self.repo.update_learning_progress('medium', proficiency_level='intermediate')
        self.repo.update_learning_progress('hard', proficiency_level='advanced')
        
        # Get intermediate words
        intermediate_words = self.repo.get_words_by_proficiency('intermediate')
        
        self.assertEqual(len(intermediate_words), 1)
        self.assertEqual(intermediate_words[0]['word'], 'medium')


class TestDataMigration(unittest.TestCase):
    """Test cases for DataMigration."""
    
    def setUp(self):
        """Set up test environment for migration."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.source_dir = os.path.join(self.temp_dir, 'source')
        os.makedirs(self.source_dir)
        
        # Create test data files
        self._create_test_files()
        
        self.migration = DataMigration(self.db_path, self.source_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self):
        """Create test data files for migration."""
        # Create globalunknowns.json
        unknown_words = {
            'unbekannt': 5,
            'schwierig': 3,
            'kompliziert': 1
        }
        with open(os.path.join(self.source_dir, 'globalunknowns.json'), 'w') as f:
            json.dump(unknown_words, f)
        
        # Create vocabulary.txt
        vocab_content = """haus 10
baum 7
auto 15
"""
        with open(os.path.join(self.source_dir, 'vocabulary.txt'), 'w') as f:
            f.write(vocab_content)
        
        # Create giuliwords.txt
        giulia_content = """schön
gut
schlecht
"""
        with open(os.path.join(self.source_dir, 'giuliwords.txt'), 'w') as f:
            f.write(giulia_content)
    
    def test_migration_process(self):
        """Test the complete migration process."""
        results = self.migration.run_migration(backup_existing=False)
        
        self.assertTrue(results['success'])
        self.assertGreater(results['vocabulary_migrated'], 0)
        self.assertGreater(results['unknown_words_migrated'], 0)
        
        # Verify data was migrated correctly
        unknown_repo = UnknownWordsRepository(self.migration.db_manager)
        vocab_repo = VocabularyRepository(self.migration.db_manager)
        
        # Check unknown words
        frequency = unknown_repo.get_unknown_word_frequency('unbekannt')
        self.assertEqual(frequency, 5)
        
        # Check vocabulary words
        word = vocab_repo.get_word('haus')
        self.assertIsNotNone(word)
        self.assertEqual(word['frequency'], 10)


class TestDatabaseConfig(unittest.TestCase):
    """Test cases for DatabaseConfig."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        reset_config()  # Reset global config
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        reset_config()
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        config = DatabaseConfig(self.temp_dir)
        
        self.assertEqual(config.base_dir, Path(self.temp_dir))
        self.assertEqual(config.default_language, 'de')
        self.assertIn('de', config.supported_languages)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = DatabaseConfig(self.temp_dir)
        
        # Valid configuration should pass
        self.assertTrue(config.validate_config())
        
        # Invalid configuration should fail
        config.cache_size = -1
        self.assertFalse(config.validate_config())
    
    @patch.dict(os.environ, {'A1DECIDER_DEFAULT_LANGUAGE': 'en'})
    def test_environment_variables(self):
        """Test loading configuration from environment variables."""
        config = DatabaseConfig(self.temp_dir)
        
        self.assertEqual(config.default_language, 'en')
    
    def test_sqlite_pragmas(self):
        """Test SQLite PRAGMA settings."""
        config = DatabaseConfig(self.temp_dir)
        pragmas = config.sqlite_pragmas
        
        self.assertIn('journal_mode', pragmas)
        self.assertIn('foreign_keys', pragmas)
        self.assertEqual(pragmas['foreign_keys'], 'ON')


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete database system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'integration_test.db')
        
        # Initialize database and repositories
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.create_database()
        
        self.vocab_repo = VocabularyRepository(self.db_manager)
        self.unknown_repo = UnknownWordsRepository(self.db_manager)
        self.category_repo = WordCategoryRepository(self.db_manager)
        self.progress_repo = UserProgressRepository(self.db_manager)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow(self):
        """Test a complete vocabulary learning workflow."""
        # 1. Create a processing session
        session_id = self.progress_repo.create_processing_session(
            session_type='integration_test',
            source_file='test_workflow.txt'
        )
        
        # 2. Add unknown words
        unknown_words = ['unbekannt', 'schwierig', 'kompliziert']
        for word in unknown_words:
            self.unknown_repo.add_unknown_word(word, frequency=1)
            self.progress_repo.record_word_discovery(session_id, word)
        
        # 3. Move some unknown words to vocabulary
        learned_word = 'unbekannt'
        word_id = self.vocab_repo.add_word(
            learned_word,
            frequency=5,
            difficulty_level='intermediate'
        )
        self.unknown_repo.mark_word_as_learned(learned_word)
        
        # 4. Create categories and associate words
        category_id = self.category_repo.create_category(
            'Learned Words',
            'Words that have been learned'
        )
        self.category_repo.associate_word_with_category(word_id, category_id)
        
        # 5. Track learning progress
        self.progress_repo.update_learning_progress(
            learned_word,
            proficiency_level='intermediate',
            confidence_score=0.8
        )
        
        # 6. End session
        self.progress_repo.end_processing_session(
            session_id,
            words_processed=len(unknown_words),
            new_words_discovered=1
        )
        
        # Verify the workflow
        # Check that unknown word was moved to vocabulary
        vocab_word = self.vocab_repo.get_word(learned_word)
        self.assertIsNotNone(vocab_word)
        
        unknown_frequency = self.unknown_repo.get_unknown_word_frequency(learned_word)
        self.assertEqual(unknown_frequency, 0)  # Should be removed from unknown words
        
        # Check category association
        word_categories = self.category_repo.get_word_categories(word_id)
        self.assertEqual(len(word_categories), 1)
        self.assertEqual(word_categories[0]['name'], 'Learned Words')
        
        # Check learning progress
        progress = self.progress_repo.get_learning_progress(learned_word)
        self.assertIsNotNone(progress)
        self.assertEqual(progress['proficiency_level'], 'intermediate')
        self.assertEqual(progress['confidence_score'], 0.8)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)