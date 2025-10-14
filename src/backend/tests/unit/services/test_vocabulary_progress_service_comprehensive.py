"""
Comprehensive test suite for VocabularyProgressService

Tests coverage for bulk operations, statistics, and edge cases.
Complements existing tests in test_vocabulary_progress_service.py.

Coverage Target: Bring vocabulary_progress_service.py from 38% to 85%+

Test Categories:
1. mark_word_known edge cases (confidence boundaries, marking as unknown)
2. bulk_mark_level functionality (complete coverage)
3. get_user_vocabulary_stats functionality (complete coverage)
4. Factory function testing
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserVocabularyProgress, VocabularyWord
from services.vocabulary.vocabulary_progress_service import (
    VocabularyProgressService,
    get_vocabulary_progress_service,
)


class TestMarkWordKnownEdgeCases:
    """Test edge cases for mark_word_known not covered by existing tests"""

    @pytest.fixture
    def service(self):
        return VocabularyProgressService()

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        return session

    @pytest.fixture
    def mock_vocab_word(self):
        word = Mock()
        word.id = 1
        word.lemma = "haus"
        word.difficulty_level = "A1"
        return word

    @patch("services.lemmatization_service.get_lemmatization_service")
    async def test_mark_word_as_unknown_new_word(self, mock_get_lemma, service, mock_db_session, mock_vocab_word):
        """Test marking a word as UNKNOWN for the first time (is_known=False)"""
        # Setup
        mock_lemma_service = Mock()
        mock_lemma_service.lemmatize.return_value = "haus"
        mock_get_lemma.return_value = mock_lemma_service

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

        # Execute - mark as UNKNOWN
        result = await service.mark_word_known(1, "haus", "de", is_known=False, db=mock_db_session)

        # Assert
        assert result["success"] is True
        assert result["is_known"] is False
        assert result["confidence_level"] == 0  # Unknown words start at confidence 0

        # Verify new progress was added
        mock_db_session.add.assert_called_once()
        added_progress = mock_db_session.add.call_args[0][0]
        assert added_progress.is_known is False
        assert added_progress.confidence_level == 0

    @patch("services.lemmatization_service.get_lemmatization_service")
    async def test_mark_word_as_unknown_existing_progress(
        self, mock_get_lemma, service, mock_db_session, mock_vocab_word
    ):
        """Test marking a word as UNKNOWN when progress exists (confidence decreases)"""
        # Setup
        mock_lemma_service = Mock()
        mock_lemma_service.lemmatize.return_value = "haus"
        mock_get_lemma.return_value = mock_lemma_service

        # Mock vocabulary word lookup
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_word

        # Mock existing progress at confidence level 2
        mock_progress = Mock()
        mock_progress.confidence_level = 2
        mock_progress.review_count = 3
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = mock_progress

        mock_results = [mock_vocab_result, mock_progress_result]

        async def mock_execute_side_effect(*args):
            return mock_results.pop(0)

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Execute - mark as UNKNOWN
        result = await service.mark_word_known(1, "haus", "de", is_known=False, db=mock_db_session)

        # Assert
        assert result["success"] is True
        assert mock_progress.is_known is False
        assert mock_progress.confidence_level == 1  # Decreased from 2 to 1
        assert mock_progress.review_count == 4

    @patch("services.lemmatization_service.get_lemmatization_service")
    async def test_confidence_level_max_boundary(self, mock_get_lemma, service, mock_db_session, mock_vocab_word):
        """Test confidence level doesn't exceed maximum of 5"""
        # Setup
        mock_lemma_service = Mock()
        mock_lemma_service.lemmatize.return_value = "haus"
        mock_get_lemma.return_value = mock_lemma_service

        # Mock vocabulary word lookup
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_word

        # Mock existing progress at MAX confidence level 5
        mock_progress = Mock()
        mock_progress.confidence_level = 5
        mock_progress.review_count = 10
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = mock_progress

        mock_results = [mock_vocab_result, mock_progress_result]

        async def mock_execute_side_effect(*args):
            return mock_results.pop(0)

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Execute - mark as known (should stay at 5)
        result = await service.mark_word_known(1, "haus", "de", is_known=True, db=mock_db_session)

        # Assert - confidence capped at 5
        assert result["success"] is True
        assert mock_progress.confidence_level == 5  # Stays at max
        assert mock_progress.review_count == 11

    @patch("services.lemmatization_service.get_lemmatization_service")
    async def test_confidence_level_min_boundary(self, mock_get_lemma, service, mock_db_session, mock_vocab_word):
        """Test confidence level doesn't go below minimum of 0"""
        # Setup
        mock_lemma_service = Mock()
        mock_lemma_service.lemmatize.return_value = "haus"
        mock_get_lemma.return_value = mock_lemma_service

        # Mock vocabulary word lookup
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_word

        # Mock existing progress at MIN confidence level 0
        mock_progress = Mock()
        mock_progress.confidence_level = 0
        mock_progress.review_count = 2
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = mock_progress

        mock_results = [mock_vocab_result, mock_progress_result]

        async def mock_execute_side_effect(*args):
            return mock_results.pop(0)

        mock_db_session.execute.side_effect = mock_execute_side_effect

        # Execute - mark as unknown (should stay at 0)
        result = await service.mark_word_known(1, "haus", "de", is_known=False, db=mock_db_session)

        # Assert - confidence stays at 0
        assert result["success"] is True
        assert mock_progress.confidence_level == 0  # Can't go below 0
        assert mock_progress.review_count == 3


class TestBulkMarkLevel:
    """Test bulk_mark_level functionality (lines 189-246)"""

    @pytest.fixture
    def service(self):
        return VocabularyProgressService()

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.add_all = Mock()
        return session

    async def test_bulk_mark_level_empty_level(self, service, mock_db_session):
        """Test bulk marking when level has no words"""
        # Mock empty word list
        mock_vocab_result = Mock()
        mock_vocab_result.all.return_value = []

        mock_db_session.execute.return_value = mock_vocab_result

        # Execute
        result = await service.bulk_mark_level(
            db=mock_db_session, user_id=1, language="de", level="C2", is_known=True
        )

        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 0
        assert result["level"] == "C2"
        assert result["language"] == "de"
        assert result["is_known"] is True

        # No database writes for empty level
        mock_db_session.add_all.assert_not_called()

    async def test_bulk_mark_level_creates_new_progress_records(self, service, mock_db_session):
        """Test bulk marking creates new progress records when none exist"""
        # Mock word list for A1 level
        mock_words = [(1, "der"), (2, "die"), (3, "das")]
        mock_vocab_result = Mock()
        mock_vocab_result.all.return_value = mock_words

        # Mock empty existing progress
        mock_progress_result = Mock()
        mock_progress_result.scalars.return_value = []

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_vocab_result  # First call: get words
            else:
                return mock_progress_result  # Second call: get existing progress

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.bulk_mark_level(
            db=mock_db_session, user_id=1, language="de", level="A1", is_known=True
        )

        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 3
        assert result["level"] == "A1"
        assert result["is_known"] is True

        # Verify add_all called with 3 new progress records
        mock_db_session.add_all.assert_called_once()
        added_records = mock_db_session.add_all.call_args[0][0]
        assert len(added_records) == 3
        assert all(isinstance(record, UserVocabularyProgress) for record in added_records)
        assert all(record.is_known is True for record in added_records)
        assert all(record.confidence_level == 3 for record in added_records)  # Bulk sets to 3

        # Verify flush called (transactional)
        mock_db_session.flush.assert_called_once()

    async def test_bulk_mark_level_updates_existing_progress_records(self, service, mock_db_session):
        """Test bulk marking updates existing progress records"""
        # Mock word list
        mock_words = [(1, "der"), (2, "die")]
        mock_vocab_result = Mock()
        mock_vocab_result.all.return_value = mock_words

        # Mock existing progress for both words
        mock_progress_1 = Mock()
        mock_progress_1.vocabulary_id = 1
        mock_progress_1.confidence_level = 2
        mock_progress_1.is_known = False

        mock_progress_2 = Mock()
        mock_progress_2.vocabulary_id = 2
        mock_progress_2.confidence_level = 1
        mock_progress_2.is_known = False

        mock_progress_result = Mock()
        mock_progress_result.scalars.return_value = [mock_progress_1, mock_progress_2]

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_vocab_result
            else:
                return mock_progress_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.bulk_mark_level(
            db=mock_db_session, user_id=1, language="de", level="A1", is_known=True
        )

        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 2

        # Verify existing records were updated (not created)
        assert mock_progress_1.is_known is True
        assert mock_progress_1.confidence_level == 3
        assert mock_progress_2.is_known is True
        assert mock_progress_2.confidence_level == 3

        # No new records added
        mock_db_session.add_all.assert_not_called()

    async def test_bulk_mark_level_mixed_existing_and_new(self, service, mock_db_session):
        """Test bulk marking with mix of existing and new progress records"""
        # Mock 3 words
        mock_words = [(1, "der"), (2, "die"), (3, "das")]
        mock_vocab_result = Mock()
        mock_vocab_result.all.return_value = mock_words

        # Mock existing progress for only first word
        mock_progress_1 = Mock()
        mock_progress_1.vocabulary_id = 1
        mock_progress_1.confidence_level = 2
        mock_progress_1.is_known = False

        mock_progress_result = Mock()
        mock_progress_result.scalars.return_value = [mock_progress_1]

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_vocab_result
            else:
                return mock_progress_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.bulk_mark_level(
            db=mock_db_session, user_id=1, language="de", level="A1", is_known=True
        )

        # Assert
        assert result["success"] is True
        assert result["updated_count"] == 3

        # Verify existing record updated
        assert mock_progress_1.is_known is True
        assert mock_progress_1.confidence_level == 3

        # Verify 2 new records created
        mock_db_session.add_all.assert_called_once()
        added_records = mock_db_session.add_all.call_args[0][0]
        assert len(added_records) == 2

    async def test_bulk_mark_level_as_unknown(self, service, mock_db_session):
        """Test bulk marking words as UNKNOWN (is_known=False)"""
        # Mock word list
        mock_words = [(1, "der"), (2, "die")]
        mock_vocab_result = Mock()
        mock_vocab_result.all.return_value = mock_words

        # Mock empty existing progress
        mock_progress_result = Mock()
        mock_progress_result.scalars.return_value = []

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_vocab_result
            else:
                return mock_progress_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute - mark as UNKNOWN
        result = await service.bulk_mark_level(
            db=mock_db_session, user_id=1, language="de", level="A1", is_known=False
        )

        # Assert
        assert result["success"] is True
        assert result["is_known"] is False

        # Verify confidence set to 0 for unknown
        added_records = mock_db_session.add_all.call_args[0][0]
        assert all(record.is_known is False for record in added_records)
        assert all(record.confidence_level == 0 for record in added_records)


class TestGetUserVocabularyStats:
    """Test get_user_vocabulary_stats functionality (lines 248-301)"""

    @pytest.fixture
    def service(self):
        return VocabularyProgressService()

    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)

    async def test_stats_with_no_words(self, service, mock_db_session):
        """Test statistics when language has no words"""
        # Mock 0 total words
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 0

        # Mock 0 known words
        mock_known_result = Mock()
        mock_known_result.scalar.return_value = 0

        # Mock empty level breakdown - return empty list directly
        mock_level_result = []

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_total_result
            elif call_count[0] == 2:
                return mock_known_result
            else:
                return mock_level_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        stats = await service.get_user_vocabulary_stats(user_id=1, language="ja", db=mock_db_session)

        # Assert
        assert stats["total_words"] == 0
        assert stats["total_known"] == 0
        assert stats["percentage_known"] == 0  # Zero division handled
        assert stats["words_by_level"] == {}
        assert stats["language"] == "ja"

    async def test_stats_with_some_known_words(self, service, mock_db_session):
        """Test statistics with partial vocabulary knowledge"""
        # Mock 1000 total words
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 1000

        # Mock 250 known words
        mock_known_result = Mock()
        mock_known_result.scalar.return_value = 250

        # Mock level breakdown - return list directly
        mock_level_result = [
            ("A1", 200, 150),  # level, total, known
            ("A2", 300, 100),
            ("B1", 500, 0),
        ]

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_total_result
            elif call_count[0] == 2:
                return mock_known_result
            else:
                return mock_level_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        stats = await service.get_user_vocabulary_stats(user_id=1, language="de", db=mock_db_session)

        # Assert overall stats
        assert stats["total_words"] == 1000
        assert stats["total_known"] == 250
        assert stats["percentage_known"] == 25.0
        assert stats["language"] == "de"

        # Assert level breakdown
        assert "A1" in stats["words_by_level"]
        assert stats["words_by_level"]["A1"]["total"] == 200
        assert stats["words_by_level"]["A1"]["known"] == 150
        assert stats["words_by_level"]["A1"]["percentage"] == 75.0

        assert stats["words_by_level"]["A2"]["known"] == 100
        assert stats["words_by_level"]["A2"]["percentage"] == 33.3

        assert stats["words_by_level"]["B1"]["known"] == 0
        assert stats["words_by_level"]["B1"]["percentage"] == 0.0

    async def test_stats_handles_null_known_counts(self, service, mock_db_session):
        """Test statistics when level has NULL known count (no progress records)"""
        # Mock 100 total words
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 100

        # Mock 0 known words
        mock_known_result = Mock()
        mock_known_result.scalar.return_value = 0

        # Mock level with NULL known (no progress records exist) - return list directly
        mock_level_result = [("A1", 100, None)]  # NULL known

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_total_result
            elif call_count[0] == 2:
                return mock_known_result
            else:
                return mock_level_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        stats = await service.get_user_vocabulary_stats(user_id=1, language="de", db=mock_db_session)

        # Assert - NULL handled as 0
        assert stats["words_by_level"]["A1"]["known"] == 0
        assert stats["words_by_level"]["A1"]["percentage"] == 0.0

    async def test_stats_percentage_rounding(self, service, mock_db_session):
        """Test percentage calculations are rounded to 1 decimal place"""
        # Mock total and known for non-round percentage
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 300

        mock_known_result = Mock()
        mock_known_result.scalar.return_value = 123  # 41.0% exactly

        # Mock level with odd percentage: 77/200 = 38.5% - return list directly
        mock_level_result = [("A1", 200, 77)]

        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_total_result
            elif call_count[0] == 2:
                return mock_known_result
            else:
                return mock_level_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        stats = await service.get_user_vocabulary_stats(user_id=1, language="de", db=mock_db_session)

        # Assert rounded to 1 decimal
        assert stats["percentage_known"] == 41.0
        assert stats["words_by_level"]["A1"]["percentage"] == 38.5


class TestFactoryFunction:
    """Test get_vocabulary_progress_service factory function"""

    def test_factory_returns_instance(self):
        """Test factory returns VocabularyProgressService instance"""
        service = get_vocabulary_progress_service()

        assert isinstance(service, VocabularyProgressService)

    def test_factory_returns_fresh_instance(self):
        """Test factory returns new instance each time (not singleton)"""
        service1 = get_vocabulary_progress_service()
        service2 = get_vocabulary_progress_service()

        # Should be different instances (no global state)
        assert service1 is not service2
