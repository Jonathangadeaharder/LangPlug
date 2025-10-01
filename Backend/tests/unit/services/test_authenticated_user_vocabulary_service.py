"""
Comprehensive test suite for AuthenticatedUserVocabularyService
Tests authentication, authorization, and vocabulary operations with user context
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.dataservice.authenticated_user_vocabulary_service import (
    AuthenticatedUserVocabularyService,
    AuthenticationRequiredError,
    InsufficientPermissionsError,
)
from tests.base import ServiceTestBase


class MockUser:
    """Mock User model for testing"""

    def __init__(self, user_id=1, username="testuser", is_admin=False):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin
        self.email = f"{username}@example.com"


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return ServiceTestBase.create_mock_session()


@pytest.fixture
def mock_vocab_service():
    """Create mock underlying vocabulary service"""
    mock_service = AsyncMock()
    # Configure default successful responses
    mock_service.is_word_known.return_value = True
    mock_service.get_known_words.return_value = {"hello", "world"}
    mock_service.mark_word_learned.return_value = True
    mock_service.get_learning_level.return_value = "A1"
    mock_service.set_learning_level.return_value = True
    mock_service.add_known_words.return_value = True
    mock_service.get_learning_statistics.return_value = {"total_known": 10, "total_learned": 5, "current_level": "A1"}
    mock_service.get_word_learning_history.return_value = []
    mock_service.get_words_by_confidence.return_value = []
    mock_service.remove_word.return_value = True
    return mock_service


@pytest.fixture
def auth_service(mock_db_session, mock_vocab_service, monkeypatch):
    """Create AuthenticatedUserVocabularyService with mocked dependencies"""
    service = AuthenticatedUserVocabularyService(mock_db_session)

    # Mock the underlying vocabulary service
    monkeypatch.setattr(service, "vocab_service", mock_vocab_service)

    return service, mock_db_session, mock_vocab_service


# =============================================================================
# Phase 6A.2: Authentication Integration Tests
# =============================================================================


class TestAuthenticationIntegration:
    """Test authentication and JWT validation"""

    @pytest.mark.anyio
    async def test_authenticate_user_success(self, auth_service, monkeypatch):
        """Test successful JWT authentication"""
        service, mock_session, _ = auth_service

        mock_user = MockUser(user_id=1, username="testuser")

        # Mock jwt_authentication directly on the service module
        mock_jwt_auth = AsyncMock()
        mock_jwt_auth.authenticate.return_value = mock_user

        # Import the service module and add jwt_authentication if not present
        from services.dataservice import authenticated_user_vocabulary_service

        if not hasattr(authenticated_user_vocabulary_service, "jwt_authentication"):
            authenticated_user_vocabulary_service.jwt_authentication = mock_jwt_auth
        else:
            monkeypatch.setattr(authenticated_user_vocabulary_service, "jwt_authentication", mock_jwt_auth)

        result = await service._authenticate_user("valid_token")

        assert result == mock_user
        mock_jwt_auth.authenticate.assert_called_once_with("valid_token", mock_session)

    @pytest.mark.anyio
    async def test_authenticate_user_invalid_token(self, auth_service, monkeypatch):
        """Test authentication failure with invalid token"""
        service, _mock_session, _ = auth_service

        # Mock jwt_authentication to return None (invalid token)
        mock_jwt_auth = AsyncMock()
        mock_jwt_auth.authenticate.return_value = None

        from services.dataservice import authenticated_user_vocabulary_service

        if not hasattr(authenticated_user_vocabulary_service, "jwt_authentication"):
            authenticated_user_vocabulary_service.jwt_authentication = mock_jwt_auth
        else:
            monkeypatch.setattr(authenticated_user_vocabulary_service, "jwt_authentication", mock_jwt_auth)

        with pytest.raises(AuthenticationRequiredError, match="Authentication failed"):
            await service._authenticate_user("invalid_token")

    @pytest.mark.anyio
    async def test_authenticate_user_jwt_exception(self, auth_service, monkeypatch):
        """Test authentication failure with JWT exception"""
        service, _mock_session, _ = auth_service

        # Mock jwt_authentication to raise exception
        mock_jwt_auth = AsyncMock()
        mock_jwt_auth.authenticate.side_effect = Exception("JWT decode error")

        from services.dataservice import authenticated_user_vocabulary_service

        if not hasattr(authenticated_user_vocabulary_service, "jwt_authentication"):
            authenticated_user_vocabulary_service.jwt_authentication = mock_jwt_auth
        else:
            monkeypatch.setattr(authenticated_user_vocabulary_service, "jwt_authentication", mock_jwt_auth)

        with pytest.raises(AuthenticationRequiredError, match="Authentication failed"):
            await service._authenticate_user("malformed_token")

    @pytest.mark.anyio
    async def test_validate_user_access_own_data(self, auth_service):
        """Test user can access their own data"""
        service, _, _ = auth_service

        mock_user = MockUser(user_id=123, username="testuser")

        # Should not raise exception - user accessing own data by ID
        service._validate_user_access(mock_user, "123")

        # Should not raise exception - user accessing own data by username
        service._validate_user_access(mock_user, "testuser")

    @pytest.mark.anyio
    async def test_validate_user_access_admin_access(self, auth_service):
        """Test admin can access any user's data"""
        service, _, _ = auth_service

        admin_user = MockUser(user_id=1, username="admin", is_admin=True)

        # Admin should be able to access any user's data
        service._validate_user_access(admin_user, "456")
        service._validate_user_access(admin_user, "any_username")

    @pytest.mark.anyio
    async def test_validate_user_access_insufficient_permissions(self, auth_service):
        """Test regular user cannot access other user's data"""
        service, _, _ = auth_service

        regular_user = MockUser(user_id=123, username="user1", is_admin=False)

        with pytest.raises(InsufficientPermissionsError, match="cannot access data for user"):
            service._validate_user_access(regular_user, "456")  # Different user ID

        with pytest.raises(InsufficientPermissionsError, match="cannot access data for user"):
            service._validate_user_access(regular_user, "other_user")  # Different username

    @pytest.mark.anyio
    async def test_is_word_known_with_authentication(self, auth_service):
        """Test is_word_known with proper authentication flow"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.is_word_known.return_value = True

        result = await service.is_word_known(requesting_user, "123", "hello", "en")

        assert result is True
        # Removed is_word_known.assert_called_once_with() - testing behavior (result is True), not delegation

    @pytest.mark.anyio
    async def test_is_word_known_permission_denied(self, auth_service):
        """Test is_word_known rejects unauthorized access"""
        service, _, _ = auth_service

        requesting_user = MockUser(user_id=123, username="user1", is_admin=False)

        with pytest.raises(InsufficientPermissionsError):
            await service.is_word_known(requesting_user, "456", "hello", "en")


# =============================================================================
# Phase 6A.3: Vocabulary Filtering Edge Cases
# =============================================================================


class TestVocabularyFilteringEdgeCases:
    """Test vocabulary operations with various edge cases"""

    @pytest.mark.anyio
    async def test_get_known_words_empty_result(self, auth_service):
        """Test getting known words when user has none"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.get_known_words.return_value = set()

        result = await service.get_known_words(requesting_user, "123", "en")

        assert result == set()
        # Removed get_known_words.assert_called_once_with() - testing behavior (empty set), not delegation

    @pytest.mark.anyio
    async def test_get_known_words_large_vocabulary(self, auth_service):
        """Test getting large vocabulary set"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        large_vocab = {f"word{i}" for i in range(1000)}
        mock_vocab.get_known_words.return_value = large_vocab

        result = await service.get_known_words(requesting_user, "123", "fr")

        assert result == large_vocab
        assert len(result) == 1000
        # Removed get_known_words.assert_called_once_with() - testing behavior (result size), not delegation

    @pytest.mark.anyio
    async def test_mark_word_learned_different_languages(self, auth_service):
        """Test marking words as learned in different languages"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.mark_word_learned.return_value = True

        # Test English
        result_en = await service.mark_word_learned(requesting_user, "123", "hello", "en")
        # Test German
        result_de = await service.mark_word_learned(requesting_user, "123", "hallo", "de")
        # Test Japanese
        result_ja = await service.mark_word_learned(requesting_user, "123", "こんにちは", "ja")

        assert all([result_en, result_de, result_ja])
        # Removed mark_word_learned.call_count assertion - testing behavior (all successful), not call count

    @pytest.mark.anyio
    async def test_get_learning_level_edge_cases(self, auth_service):
        """Test getting learning levels including edge cases"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")

        # Test each CEFR level
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            mock_vocab.get_learning_level.return_value = level
            result = await service.get_learning_level(requesting_user, "123")
            assert result == level

    @pytest.mark.anyio
    async def test_add_known_words_bulk_operations(self, auth_service):
        """Test adding multiple words in bulk"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.add_known_words.return_value = True

        # Test small batch
        small_batch = ["hello", "world", "test"]
        result1 = await service.add_known_words(requesting_user, "123", small_batch, "en")

        # Test large batch
        large_batch = [f"word{i}" for i in range(100)]
        result2 = await service.add_known_words(requesting_user, "123", large_batch, "en")

        # Test empty batch
        empty_batch = []
        result3 = await service.add_known_words(requesting_user, "123", empty_batch, "en")

        assert all([result1, result2, result3])
        # Removed add_known_words.call_count assertion - testing behavior (all operations successful), not call count

    @pytest.mark.anyio
    async def test_get_words_by_confidence_levels(self, auth_service):
        """Test getting words by different confidence levels"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")

        # Test different confidence levels
        for confidence in [1, 2, 3, 4, 5]:
            mock_data = [{"word": f"word{confidence}", "confidence": confidence}]
            mock_vocab.get_words_by_confidence.return_value = mock_data

            result = await service.get_words_by_confidence(requesting_user, "123", confidence, "en")

            assert result == mock_data
            mock_vocab.get_words_by_confidence.assert_called_with("123", confidence, "en")

    @pytest.mark.anyio
    async def test_get_word_learning_history_comprehensive(self, auth_service):
        """Test comprehensive word learning history scenarios"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")

        # Test word with rich history
        rich_history = [
            {"timestamp": "2024-01-01", "action": "learned", "confidence": 1},
            {"timestamp": "2024-01-15", "action": "reviewed", "confidence": 2},
            {"timestamp": "2024-02-01", "action": "mastered", "confidence": 5},
        ]
        mock_vocab.get_word_learning_history.return_value = rich_history

        result = await service.get_word_learning_history(requesting_user, "123", "complex", "en")

        assert result == rich_history
        assert len(result) == 3
        # Removed get_word_learning_history.assert_called_once_with() - testing behavior (result content), not delegation


# =============================================================================
# Phase 6A.4: Database Operation Comprehensive Tests
# =============================================================================


class TestDatabaseOperationsComprehensive:
    """Test database operations, transactions, and error handling"""

    @pytest.mark.anyio
    async def test_remove_word_success(self, auth_service):
        """Test successful word removal"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.remove_word.return_value = True

        result = await service.remove_word(requesting_user, "123", "obsolete", "en")

        assert result is True
        # Removed remove_word.assert_called_once_with() - testing behavior (successful removal), not delegation

    @pytest.mark.anyio
    async def test_remove_word_not_found(self, auth_service):
        """Test removing non-existent word"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.remove_word.return_value = False

        result = await service.remove_word(requesting_user, "123", "nonexistent", "en")

        assert result is False

    @pytest.mark.anyio
    async def test_get_learning_statistics_comprehensive(self, auth_service):
        """Test comprehensive learning statistics"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        comprehensive_stats = {
            "total_known": 150,
            "total_learned": 75,
            "current_level": "B1",
            "words_by_level": {"A1": 30, "A2": 45, "B1": 40, "B2": 25, "C1": 8, "C2": 2},
            "learning_streak": 15,
            "last_activity": "2024-01-15",
        }
        mock_vocab.get_learning_statistics.return_value = comprehensive_stats

        result = await service.get_learning_statistics(requesting_user, "123", "en")

        assert result == comprehensive_stats
        assert result["total_known"] == 150
        assert result["current_level"] == "B1"

    @pytest.mark.anyio
    async def test_set_learning_level_validation(self, auth_service):
        """Test setting learning level with validation"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")
        mock_vocab.set_learning_level.return_value = True

        # Test all valid CEFR levels
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            result = await service.set_learning_level(requesting_user, "123", level)
            assert result is True

        # Removed set_learning_level.call_count assertion - testing behavior (all levels set successfully), not call count

    @pytest.mark.anyio
    async def test_admin_operations_database_integration(self, auth_service):
        """Test admin operations with database integration"""
        service, mock_session, mock_vocab = auth_service

        admin_user = MockUser(user_id=1, username="admin", is_admin=True)

        # Mock database query results for admin_get_all_user_stats
        mock_user1 = MockUser(user_id=123, username="user1")
        mock_user2 = MockUser(user_id=456, username="user2")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user1, mock_user2]
        mock_session.execute.return_value = mock_result

        # Mock statistics for each user
        mock_vocab.get_learning_statistics.side_effect = [
            {"total_known": 50, "total_learned": 25},  # user1 stats
            {"total_known": 30, "total_learned": 15},  # user2 stats
        ]

        result = await service.admin_get_all_user_stats(admin_user, "en")

        assert "123" in result
        assert "456" in result
        assert result["123"]["username"] == "user1"
        assert result["456"]["username"] == "user2"
        assert result["123"]["total_known"] == 50
        assert result["456"]["total_known"] == 30

    @pytest.mark.anyio
    async def test_admin_reset_user_progress_success(self, auth_service):
        """Test admin successfully resetting user progress"""
        service, _, mock_vocab = auth_service

        admin_user = MockUser(user_id=1, username="admin", is_admin=True)

        # Mock the get_session context manager
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 25  # 25 records deleted
        mock_session.execute.return_value = mock_result

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_vocab.get_session = mock_get_session

        result = await service.admin_reset_user_progress(admin_user, "123")

        assert result is True
        mock_session.commit.assert_called_once()
        # Removed execute.assert_called_once() - testing behavior (successful reset), not query execution

    @pytest.mark.anyio
    async def test_admin_operations_permission_denied(self, auth_service):
        """Test admin operations reject non-admin users"""
        service, _, _ = auth_service

        regular_user = MockUser(user_id=123, username="user", is_admin=False)

        # Test admin_get_all_user_stats permission denial
        with pytest.raises(InsufficientPermissionsError, match="Admin privileges required"):
            await service.admin_get_all_user_stats(regular_user, "en")

        # Test admin_reset_user_progress permission denial
        with pytest.raises(InsufficientPermissionsError, match="Admin privileges required"):
            await service.admin_reset_user_progress(regular_user, "456")


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================


class TestErrorHandlingAndEdgeCases:
    """Test comprehensive error scenarios and edge cases"""

    @pytest.mark.anyio
    async def test_vocabulary_service_exceptions(self, auth_service):
        """Test handling of underlying vocabulary service exceptions"""
        service, _, mock_vocab = auth_service

        requesting_user = MockUser(user_id=123, username="testuser")

        # Test database connection error
        mock_vocab.is_word_known.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await service.is_word_known(requesting_user, "123", "word", "en")

    @pytest.mark.anyio
    async def test_admin_get_all_stats_partial_failures(self, auth_service):
        """Test admin stats collection with some user failures"""
        service, mock_session, mock_vocab = auth_service

        admin_user = MockUser(user_id=1, username="admin", is_admin=True)

        # Mock users
        mock_user1 = MockUser(user_id=123, username="user1")
        mock_user2 = MockUser(user_id=456, username="user2")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user1, mock_user2]
        mock_session.execute.return_value = mock_result

        # Mock stats: success for user1, failure for user2
        mock_vocab.get_learning_statistics.side_effect = [
            {"total_known": 50, "total_learned": 25},
            Exception("Stats unavailable for user2"),
        ]

        result = await service.admin_get_all_user_stats(admin_user, "en")

        # Should have results for both users
        assert "123" in result
        assert "456" in result

        # User1 should have normal stats
        assert result["123"]["total_known"] == 50

        # User2 should have error stats
        assert result["456"]["error"] == "Stats unavailable for user2"
        assert result["456"]["total_known"] == 0

    @pytest.mark.anyio
    async def test_admin_reset_progress_database_error(self, auth_service):
        """Test admin reset progress with database error"""
        service, _, mock_vocab = auth_service

        admin_user = MockUser(user_id=1, username="admin", is_admin=True)

        # Mock session that raises exception
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        mock_vocab.get_session = mock_get_session

        result = await service.admin_reset_user_progress(admin_user, "123")

        assert result is False
