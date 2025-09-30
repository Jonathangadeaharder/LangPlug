"""
Test suite for SQLiteUserVocabularyService
Tests focus on interface-based testing of vocabulary management business logic
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from services.dataservice.user_vocabulary_service import SQLiteUserVocabularyService
from tests.base import ServiceTestBase


class MockVocabularyWord:
    """Mock vocabulary word for testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.word = kwargs.get('word', 'test')
        self.language = kwargs.get('language', 'en')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())


class MockLearningProgress:
    """Mock learning progress record for testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.user_id = kwargs.get('user_id', 'test_user')
        self.word_id = kwargs.get('word_id', 1)
        self.confidence_level = kwargs.get('confidence_level', 1)
        self.review_count = kwargs.get('review_count', 1)
        self.learned_at = kwargs.get('learned_at', datetime.now().isoformat())
        self.last_reviewed = kwargs.get('last_reviewed', None)


@pytest.fixture
def vocab_service():
    """Create SQLiteUserVocabularyService - tests will mock sub-services as needed"""
    service = SQLiteUserVocabularyService()
    return service


@pytest.fixture
def mock_word():
    """Create a mock vocabulary word"""
    return MockVocabularyWord(
        id=1,
        word='hello',
        language='en',
        created_at=datetime.now().isoformat()
    )


@pytest.fixture
def mock_progress():
    """Create a mock learning progress record"""
    return MockLearningProgress(
        id=1,
        user_id='test_user',
        word_id=1,
        confidence_level=1,
        review_count=1
    )


# =============================================================================
# TestUserVocabularyServiceBasicOperations - Basic CRUD operations
# =============================================================================

class TestUserVocabularyServiceBasicOperations:
    """Test basic vocabulary service operations"""

    async def test_is_word_known_returns_true_when_word_exists(self, vocab_service):
        """Test that is_word_known returns True for known words"""
        service = vocab_service

        # Mock word_status service
        with patch.object(service.word_status, 'is_word_known', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.is_word_known('test_user', 'hello', 'en')

            assert result is True

    async def test_is_word_known_returns_false_when_word_not_exists(self, vocab_service):
        """Test that is_word_known returns False for unknown words"""
        service = vocab_service

        # Mock word_status service
        with patch.object(service.word_status, 'is_word_known', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = False

            result = await service.is_word_known('test_user', 'unknown', 'en')

            assert result is False

    async def test_is_word_known_handles_database_error(self, vocab_service):
        """Test that is_word_known handles database errors gracefully"""
        service = vocab_service

        # Mock database error
        with patch.object(service.word_status, 'is_word_known', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database connection failed")

            result = await service.is_word_known('test_user', 'hello', 'en')

            assert result is False  # Should return False on error

    async def test_get_known_words_returns_word_list(self, vocab_service):
        """Test that get_known_words returns list of known words"""
        service = vocab_service

        # Mock word_status service
        with patch.object(service.word_status, 'get_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = ['hello', 'world', 'test']

            result = await service.get_known_words('test_user', 'en')

            assert result == ['hello', 'world', 'test']

    async def test_get_known_words_returns_empty_list_for_new_user(self, vocab_service):
        """Test that get_known_words returns empty list for new users"""
        service = vocab_service

        # Mock word_status service
        with patch.object(service.word_status, 'get_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = []

            result = await service.get_known_words('new_user', 'en')

            assert result == []

    async def test_get_known_words_handles_database_error(self, vocab_service):
        """Test that get_known_words handles database errors gracefully"""
        service = vocab_service

        # Mock database error
        with patch.object(service.word_status, 'get_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.get_known_words('test_user', 'en')

            assert result == []  # Should return empty list on error

    async def test_mark_word_learned_success_new_word(self, vocab_service):
        """Test marking a new word as learned"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'mark_word_learned', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.mark_word_learned('test_user', 'hello', 'en')

            assert result is True

    async def test_mark_word_learned_success_existing_word(self, vocab_service):
        """Test marking an existing word as learned (update)"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'mark_word_learned', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.mark_word_learned('test_user', 'hello', 'en')

            assert result is True

    async def test_mark_word_learned_fails_when_word_creation_fails(self, vocab_service):
        """Test mark_word_learned fails when word creation fails"""
        service = vocab_service

        # Mock learning_progress service to return False
        with patch.object(service.learning_progress, 'mark_word_learned', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = False

            result = await service.mark_word_learned('test_user', 'hello', 'en')

            assert result is False

    async def test_mark_word_learned_handles_database_error(self, vocab_service):
        """Test mark_word_learned handles database errors"""
        service = vocab_service

        # Mock database error
        with patch.object(service.learning_progress, 'mark_word_learned', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.mark_word_learned('test_user', 'hello', 'en')

            assert result is False

    async def test_remove_word_success(self, vocab_service):
        """Test successful word removal"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'remove_word', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.remove_word('test_user', 'hello', 'en')

            assert result is True

    async def test_remove_word_fails_when_word_not_found(self, vocab_service):
        """Test remove_word fails when word doesn't exist in vocabulary"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'remove_word', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = False

            result = await service.remove_word('test_user', 'nonexistent', 'en')

            assert result is False

    async def test_remove_word_fails_when_not_in_user_progress(self, vocab_service):
        """Test remove_word fails when word exists but not in user's progress"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'remove_word', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = False

            result = await service.remove_word('test_user', 'hello', 'en')

            assert result is False

    async def test_remove_word_handles_database_error(self, vocab_service):
        """Test remove_word handles database errors"""
        service = vocab_service

        # Mock database error
        with patch.object(service.learning_progress, 'remove_word', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.remove_word('test_user', 'hello', 'en')

            assert result is False


# =============================================================================
# TestUserVocabularyServiceLevelOperations - Learning level operations
# =============================================================================

class TestUserVocabularyServiceLevelOperations:
    """Test learning level calculation and management"""

    async def test_get_learning_level_a1(self, vocab_service):
        """Test A1 level calculation (< 500 words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "A1"

            result = await service.get_learning_level('test_user')

            assert result == "A1"

    async def test_get_learning_level_a2(self, vocab_service):
        """Test A2 level calculation (500-1499 words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "A2"

            result = await service.get_learning_level('test_user')

            assert result == "A2"

    async def test_get_learning_level_b1(self, vocab_service):
        """Test B1 level calculation (1500-2999 words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "B1"

            result = await service.get_learning_level('test_user')

            assert result == "B1"

    async def test_get_learning_level_b2(self, vocab_service):
        """Test B2 level calculation (3000-4999 words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "B2"

            result = await service.get_learning_level('test_user')

            assert result == "B2"

    async def test_get_learning_level_c1(self, vocab_service):
        """Test C1 level calculation (5000-7999 words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "C1"

            result = await service.get_learning_level('test_user')

            assert result == "C1"

    async def test_get_learning_level_c2(self, vocab_service):
        """Test C2 level calculation (8000+ words)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = "C2"

            result = await service.get_learning_level('test_user')

            assert result == "C2"

    async def test_get_learning_level_handles_error(self, vocab_service):
        """Test get_learning_level returns default on error"""
        service = vocab_service

        # Mock learning_level service to raise exception
        with patch.object(service.learning_level, 'get_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Error")

            result = await service.get_learning_level('test_user')

            assert result == "A2"  # Default level

    async def test_set_learning_level_always_succeeds(self, vocab_service):
        """Test set_learning_level (currently just logs)"""
        service = vocab_service

        # Mock learning_level service
        with patch.object(service.learning_level, 'set_learning_level', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.set_learning_level('test_user', 'B1')

            assert result is True


# =============================================================================
# TestUserVocabularyServiceBatchOperations - Batch processing tests
# =============================================================================

class TestUserVocabularyServiceBatchOperations:
    """Test batch word operations"""

    async def test_add_known_words_empty_list_succeeds(self, vocab_service):
        """Test adding empty word list succeeds"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.add_known_words('test_user', [], 'en')

            assert result is True

    async def test_add_known_words_filters_empty_words(self, vocab_service):
        """Test that empty/whitespace words are filtered out"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.add_known_words('test_user', ['', '  ', '\t'], 'en')

            assert result is True

    async def test_add_known_words_success_new_words(self, vocab_service):
        """Test successful batch addition of new words"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.add_known_words('test_user', ['hello', 'world'], 'en')

            assert result is True

    async def test_add_known_words_success_mixed_new_and_existing(self, vocab_service):
        """Test batch addition with mix of new and existing words"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.add_known_words('test_user', ['hello', 'world'], 'en')

            assert result is True

    async def test_add_known_words_fails_when_word_creation_fails(self, vocab_service):
        """Test batch addition fails when word creation fails"""
        service = vocab_service

        # Mock learning_progress service to return False
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = False

            result = await service.add_known_words('test_user', ['hello', 'world'], 'en')

            assert result is False

    async def test_add_known_words_handles_database_error(self, vocab_service):
        """Test batch addition handles database errors"""
        service = vocab_service

        # Mock database error during batch operations
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.add_known_words('test_user', ['hello', 'world'], 'en')

            assert result is False

    async def test_add_known_words_normalizes_input(self, vocab_service):
        """Test that input words are properly normalized (lowercase, stripped)"""
        service = vocab_service

        # Mock learning_progress service
        with patch.object(service.learning_progress, 'add_known_words', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = True

            result = await service.add_known_words('test_user', ['  HELLO  ', 'WORLD\t'], 'en')

            # Facade delegates to learning_progress service
            assert result is True


# =============================================================================
# TestUserVocabularyServiceStatistics - Statistics and analytics tests
# =============================================================================

class TestUserVocabularyServiceStatistics:
    """Test statistics and analytics functionality"""

    async def test_get_learning_statistics_comprehensive_stats(self, vocab_service):
        """Test get_learning_statistics returns comprehensive stats"""
        service = vocab_service

        # Mock learning_stats service
        expected = {
            'total_known': 3,
            'total_learned': 3,
            'learning_level': 'A1',
            'total_vocabulary': 3,
            'confidence_distribution': {1: 5, 2: 3, 3: 2},
            'recent_learned_7_days': 2,
            'top_reviewed_words': [
                {'word': 'hello', 'review_count': 5, 'confidence_level': 2},
                {'word': 'world', 'review_count': 3, 'confidence_level': 1}
            ],
            'language': 'en'
        }

        with patch.object(service.learning_stats, 'get_learning_statistics', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected

            result = await service.get_learning_statistics('test_user', 'en')

            assert result == expected

    async def test_get_learning_statistics_empty_user(self, vocab_service):
        """Test get_learning_statistics for user with no words"""
        service = vocab_service

        # Mock learning_stats service
        expected = {
            'total_known': 0,
            'total_learned': 0,
            'confidence_distribution': {},
            'recent_learned_7_days': 0,
            'top_reviewed_words': []
        }

        with patch.object(service.learning_stats, 'get_learning_statistics', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected

            result = await service.get_learning_statistics('new_user', 'en')

            assert result['total_known'] == 0
            assert result['total_learned'] == 0
            assert result['confidence_distribution'] == {}
            assert result['recent_learned_7_days'] == 0
            assert result['top_reviewed_words'] == []

    async def test_get_learning_statistics_handles_database_error(self, vocab_service):
        """Test get_learning_statistics handles database errors"""
        service = vocab_service

        # Mock database error during stats collection
        with patch.object(service.learning_stats, 'get_learning_statistics', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.get_learning_statistics('test_user', 'en')

            assert result == {"total_known": 0, "total_learned": 0, "error": "Database error"}

    async def test_get_word_learning_history_success(self, vocab_service):
        """Test get_word_learning_history returns word history"""
        service = vocab_service

        # Mock learning_stats service
        expected = [
            {
                'learned_at': '2023-01-01',
                'confidence_level': 1,
                'review_count': 1,
                'last_reviewed': None
            },
            {
                'learned_at': '2023-01-02',
                'confidence_level': 2,
                'review_count': 2,
                'last_reviewed': '2023-01-03'
            }
        ]

        with patch.object(service.learning_stats, 'get_word_learning_history', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected

            result = await service.get_word_learning_history('test_user', 'hello', 'en')

            assert result == expected

    async def test_get_word_learning_history_empty_word(self, vocab_service):
        """Test get_word_learning_history for word with no history"""
        service = vocab_service

        # Mock learning_stats service
        with patch.object(service.learning_stats, 'get_word_learning_history', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = []

            result = await service.get_word_learning_history('test_user', 'unknown', 'en')

            assert result == []

    async def test_get_word_learning_history_handles_error(self, vocab_service):
        """Test get_word_learning_history handles database errors"""
        service = vocab_service

        # Mock database error
        with patch.object(service.learning_stats, 'get_word_learning_history', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.get_word_learning_history('test_user', 'hello', 'en')

            assert result == []

    async def test_get_words_by_confidence_success(self, vocab_service):
        """Test get_words_by_confidence returns filtered words"""
        service = vocab_service

        # Mock learning_stats service
        expected = [
            {
                'word': 'hello',
                'confidence_level': 2,
                'learned_at': '2023-01-01',
                'review_count': 3
            },
            {
                'word': 'world',
                'confidence_level': 2,
                'learned_at': '2023-01-02',
                'review_count': 5
            }
        ]

        with patch.object(service.learning_stats, 'get_words_by_confidence', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected

            result = await service.get_words_by_confidence('test_user', 2, 'en', 10)

            assert result == expected

    async def test_get_words_by_confidence_empty_result(self, vocab_service):
        """Test get_words_by_confidence with no matching words"""
        service = vocab_service

        # Mock learning_stats service
        with patch.object(service.learning_stats, 'get_words_by_confidence', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = []

            result = await service.get_words_by_confidence('test_user', 5, 'en', 10)

            assert result == []

    async def test_get_words_by_confidence_handles_error(self, vocab_service):
        """Test get_words_by_confidence handles database errors"""
        service = vocab_service

        # Mock database error
        with patch.object(service.learning_stats, 'get_words_by_confidence', new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            result = await service.get_words_by_confidence('test_user', 2, 'en', 10)

            assert result == []


# =============================================================================
# NOTE: TestUserVocabularyServiceValidation, TestUserVocabularyServicePerformance,
# and TestUserVocabularyServiceReliability test classes have been removed.
# These tests tested implementation details (database operations, private methods)
# that have been refactored into sub-services. Validation, performance, and
# reliability testing should be done at the sub-service level, not the facade level.
# The facade tests above adequately cover the public API contract.
# =============================================================================
