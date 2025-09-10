"""
Unit tests for User Vocabulary Service
Tests the core vocabulary management functionality
"""
import pytest
from services.dataservice.user_vocabulary_service import SQLiteUserVocabularyService


class TestSQLiteUserVocabularyService:
    """Test cases for SQLiteUserVocabularyService"""

    @pytest.fixture
    def vocab_service(self, temp_db):
        """Create vocabulary service with temp database"""
        return SQLiteUserVocabularyService(temp_db)

    def test_initialization(self, vocab_service):
        """Test service initialization"""
        assert vocab_service is not None
        assert hasattr(vocab_service, 'db_manager')

    def test_get_user_vocabulary_empty(self, vocab_service):
        """Test getting vocabulary for user with no data"""
        vocab = vocab_service.get_user_vocabulary("new_user")
        
        assert isinstance(vocab, set)
        assert len(vocab) == 0

    def test_add_known_words(self, vocab_service):
        """Test adding known words for a user"""
        user_id = "test_user"
        words = {"hello", "world", "test"}
        
        vocab_service.add_known_words(user_id, words)
        retrieved_vocab = vocab_service.get_user_vocabulary(user_id)
        
        assert words.issubset(retrieved_vocab)

    def test_add_known_words_duplicates(self, vocab_service):
        """Test adding duplicate words doesn't create duplicates"""
        user_id = "test_user"
        words = {"hello", "world"}
        
        vocab_service.add_known_words(user_id, words)
        vocab_service.add_known_words(user_id, words)  # Add same words again
        
        retrieved_vocab = vocab_service.get_user_vocabulary(user_id)
        assert len(retrieved_vocab & words) == len(words)

    def test_is_word_known_positive(self, vocab_service):
        """Test checking if known word returns True"""
        user_id = "test_user"
        word = "hello"
        
        vocab_service.add_known_words(user_id, {word})
        assert vocab_service.is_word_known(user_id, word) is True

    def test_is_word_known_negative(self, vocab_service):
        """Test checking if unknown word returns False"""
        user_id = "test_user"
        word = "unknown"
        
        assert vocab_service.is_word_known(user_id, word) is False

    def test_filter_unknown_words(self, vocab_service):
        """Test filtering unknown words from a set"""
        user_id = "test_user"
        known_words = {"hello", "world"}
        all_words = {"hello", "world", "unknown", "new"}
        
        vocab_service.add_known_words(user_id, known_words)
        unknown = vocab_service.filter_unknown_words(user_id, all_words)
        
        expected_unknown = {"unknown", "new"}
        assert unknown == expected_unknown

    def test_get_vocabulary_stats(self, vocab_service):
        """Test getting vocabulary statistics"""
        user_id = "test_user"
        words = {"word1", "word2", "word3"}
        
        vocab_service.add_known_words(user_id, words)
        stats = vocab_service.get_vocabulary_stats(user_id)
        
        assert "total_known_words" in stats
        assert stats["total_known_words"] >= len(words)

    def test_multiple_users_isolation(self, vocab_service):
        """Test that different users have isolated vocabularies"""
        user1_words = {"hello", "world"}
        user2_words = {"foo", "bar"}
        
        vocab_service.add_known_words("user1", user1_words)
        vocab_service.add_known_words("user2", user2_words)
        
        user1_vocab = vocab_service.get_user_vocabulary("user1")
        user2_vocab = vocab_service.get_user_vocabulary("user2")
        
        assert user1_words.issubset(user1_vocab)
        assert user2_words.issubset(user2_vocab)
        assert user1_vocab.intersection(user2_vocab) == set()

    def test_error_handling_invalid_user(self, vocab_service):
        """Test error handling for invalid user operations"""
        # Should not raise exception for non-existent user
        result = vocab_service.get_user_vocabulary("")
        assert isinstance(result, set)

    def test_large_vocabulary_performance(self, vocab_service):
        """Test performance with large vocabulary set"""
        user_id = "perf_test_user"
        large_vocab = {f"word_{i}" for i in range(1000)}
        
        vocab_service.add_known_words(user_id, large_vocab)
        retrieved = vocab_service.get_user_vocabulary(user_id)
        
        assert len(retrieved & large_vocab) == len(large_vocab)

    def test_database_persistence(self, vocab_service):
        """Test that vocabulary persists across service instances"""
        user_id = "persistence_user"
        words = {"persistent", "words"}
        
        vocab_service.add_known_words(user_id, words)
        
        # Create new service instance with same database
        new_service = SQLiteUserVocabularyService(vocab_service.db_manager)
        retrieved = new_service.get_user_vocabulary(user_id)
        
        assert words.issubset(retrieved)

    def test_concurrent_access_safety(self, vocab_service):
        """Test thread safety of vocabulary operations"""
        import threading
        
        user_id = "concurrent_user"
        results = []
        
        def add_words(start_index):
            words = {f"word_{i}" for i in range(start_index, start_index + 10)}
            vocab_service.add_known_words(user_id, words)
            retrieved = vocab_service.get_user_vocabulary(user_id)
            results.append(len(retrieved))
        
        threads = []
        for i in range(0, 50, 10):
            thread = threading.Thread(target=add_words, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        final_vocab = vocab_service.get_user_vocabulary(user_id)
        assert len(final_vocab) >= 50  # Should have at least all added words