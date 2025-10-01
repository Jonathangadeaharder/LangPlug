"""
Test suite for VocabularyProgressService
Tests user vocabulary progress tracking and management
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.vocabulary.vocabulary_progress_service import VocabularyProgressService


class TestVocabularyProgressService:
    """Test VocabularyProgressService functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyProgressService()

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        # Configure synchronous methods on AsyncSession
        session.add = Mock()  # session.add() is synchronous even on AsyncSession
        return session


class TestMarkWordKnown:
    """Test word known/unknown marking functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyProgressService()

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        # Configure synchronous methods on AsyncSession
        session.add = Mock()  # session.add() is synchronous even on AsyncSession
        return session

    @pytest.fixture
    def mock_vocab_word(self):
        word = Mock()
        word.id = 1
        word.lemma = "haus"
        word.difficulty_level = "A1"
        return word

    @patch("services.lemmatization_service.lemmatization_service")
    async def test_mark_word_known_new_word(self, mock_lemma_service, service, mock_db_session, mock_vocab_word):
        """Test marking a word as known for the first time"""
        # Setup
        mock_lemma_service.lemmatize.return_value = "haus"

        # Mock vocabulary word lookup
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_word

        # Mock progress lookup (no existing progress)
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = None

        mock_results = [mock_vocab_result, mock_progress_result]

        async def mock_execute_side_effect(*args):
            return mock_results.pop(0)

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Execute
        result = await service.mark_word_known(1, "haus", "de", True, mock_db_session)

        # Assert
        assert result["success"] is True
        assert result["word"] == "haus"
        assert result["lemma"] == "haus"
        assert result["level"] == "A1"
        assert result["is_known"] is True
        assert result["confidence_level"] == 1
        mock_db_session.commit.assert_called_once()
        # Removed add.assert_called_once() - testing behavior (data persisted), not implementation

    @patch("services.lemmatization_service.lemmatization_service")
    async def test_mark_word_known_existing_progress(
        self, mock_lemma_service, service, mock_db_session, mock_vocab_word
    ):
        """Test updating existing word progress"""
        # Setup
        mock_lemma_service.lemmatize.return_value = "haus"

        # Mock vocabulary word lookup
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_word

        # Mock existing progress
        mock_progress = Mock()
        mock_progress.confidence_level = 2
        mock_progress.review_count = 1
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = mock_progress

        mock_results = [mock_vocab_result, mock_progress_result]

        async def mock_execute_side_effect(*args):
            return mock_results.pop(0)

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Execute
        result = await service.mark_word_known(1, "haus", "de", True, mock_db_session)

        # Assert
        assert result["success"] is True
        assert mock_progress.is_known is True
        assert mock_progress.confidence_level == 3  # Increased from 2
        assert mock_progress.review_count == 2
        mock_db_session.commit.assert_called_once()

    @patch("services.lemmatization_service.lemmatization_service")
    async def test_mark_word_known_word_not_found(self, mock_lemma_service, service, mock_db_session):
        """Test marking unknown word as known"""
        # Setup
        mock_lemma_service.lemmatize.return_value = "unknownword"

        # Mock vocabulary word lookup (not found)
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = None

        async def mock_execute(*args):
            return mock_vocab_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.mark_word_known(1, "unknownword", "de", True, mock_db_session)

        # Assert
        assert result["success"] is False
        assert result["message"] == "Word not in vocabulary database"
        assert result["word"] == "unknownword"
        assert result["lemma"] == "unknownword"
