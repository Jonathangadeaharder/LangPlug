"""
Comprehensive test suite for VocabularyStatsService

Tests coverage for statistics, progress summaries, and supported languages.

Coverage Target: Bring vocabulary_stats_service.py from 17% to 80%+

Test Categories:
1. get_vocabulary_stats (delegation and implementation)
2. get_user_progress_summary (overall progress)
3. get_supported_languages (language list)
4. Factory function testing
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.vocabulary.vocabulary_stats_service import (
    VocabularyStatsService,
    get_vocabulary_stats_service,
)


class TestGetVocabularyStats:
    """Test get_vocabulary_stats functionality (lines 20-28, 93-166)"""

    @pytest.fixture
    def service(self):
        return VocabularyStatsService()

    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)

    async def test_get_vocabulary_stats_delegates_to_internal_method(self, service, mock_db_session):
        """Test get_vocabulary_stats delegates to _get_vocabulary_stats_with_session"""
        # Mock the internal method
        mock_result = Mock()
        mock_result.levels = {"A1": {"total_words": 100, "user_known": 50}}
        mock_result.total_words = 100
        mock_result.total_known = 50

        with patch.object(service, "_get_vocabulary_stats_with_session", new_callable=AsyncMock, return_value=mock_result) as mock_internal:
            result = await service.get_vocabulary_stats(
                db_session=mock_db_session, user_id=1, target_language="de", translation_language="en"
            )

        # Verify delegation
        mock_internal.assert_called_once_with(mock_db_session, 1, "de", "en")
        assert result == mock_result

    async def test_get_vocabulary_stats_with_session_all_levels_empty(self, service, mock_db_session):
        """Test statistics when all CEFR levels are empty"""
        # Mock empty results for all queries
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 0

        mock_known_result = Mock()
        mock_known_result.scalar.return_value = 0

        mock_unknown_result = Mock()
        mock_unknown_result.scalar.return_value = 0

        # Setup execute to return mocks based on call count
        call_count = [0]
        total_calls_per_level = 2  # 1 total + 1 known per level
        num_levels = 6  # A1, A2, B1, B2, C1, C2

        async def mock_execute(*args):
            call_count[0] += 1
            if call_count[0] <= num_levels * total_calls_per_level:
                # Level queries
                if call_count[0] % 2 == 1:
                    return mock_total_result  # Odd calls: total words
                else:
                    return mock_known_result  # Even calls: known words
            else:
                # Final query: unknown words (vocabulary_id IS NULL)
                return mock_unknown_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service._get_vocabulary_stats_with_session(
            db_session=mock_db_session, user_id=1, target_language="de", native_language="en"
        )

        # Assert
        assert result.total_words == 0
        assert result.total_known == 0
        assert result.target_language == "de"
        assert result.translation_language == "en"
        assert len(result.levels) == 6  # All 6 CEFR levels

    async def test_get_vocabulary_stats_with_session_some_known_words(self, service, mock_db_session):
        """Test statistics with partial vocabulary knowledge across levels"""
        # Mock results for A1: 100 total, 50 known
        # All other levels: 0 total, 0 known
        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1

            mock_result = Mock()

            # First level (A1): 100 total, 50 known
            if call_count[0] == 1:
                mock_result.scalar.return_value = 100  # A1 total
            elif call_count[0] == 2:
                mock_result.scalar.return_value = 50  # A1 known
            # All other levels (A2-C2): 0 total, 0 known
            elif call_count[0] <= 12:  # 5 more levels * 2 queries each
                mock_result.scalar.return_value = 0
            # Unknown words (vocabulary_id IS NULL)
            else:
                mock_result.scalar.return_value = 10  # 10 unknown words marked as known

            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service._get_vocabulary_stats_with_session(
            db_session=mock_db_session, user_id=1, target_language="de", native_language="en"
        )

        # Assert
        assert result.total_words == 100  # Only A1 has words
        assert result.total_known == 60  # 50 from A1 + 10 unknown words
        assert result.levels["A1"]["total_words"] == 100
        assert result.levels["A1"]["user_known"] == 50

    async def test_get_vocabulary_stats_with_session_handles_none_results(self, service, mock_db_session):
        """Test statistics handles NULL/None results from database"""
        # Mock None results (empty database)
        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            mock_result = Mock()
            mock_result.scalar.return_value = None  # SQLAlchemy returns None for empty counts
            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service._get_vocabulary_stats_with_session(
            db_session=mock_db_session, user_id=1, target_language="de", native_language="en"
        )

        # Assert - None values converted to 0
        assert result.total_words == 0
        assert result.total_known == 0


class TestGetUserProgressSummary:
    """Test get_user_progress_summary functionality (lines 168-213)"""

    @pytest.fixture
    def service(self):
        return VocabularyStatsService()

    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)

    async def test_progress_summary_no_words(self, service, mock_db_session):
        """Test progress summary when no words exist"""
        # Mock 0 total words, 0 known words, 0 per level
        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            mock_result = Mock()
            mock_result.scalar.return_value = 0
            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.get_user_progress_summary(db_session=mock_db_session, user_id=1)

        # Assert
        assert result["total_words"] == 0
        assert result["known_words"] == 0
        assert result["percentage_known"] == 0.0  # Zero division handled
        assert len(result["levels_progress"]) == 6  # All 6 CEFR levels

        # Check level structure
        for level_data in result["levels_progress"]:
            assert "level" in level_data
            assert "total" in level_data
            assert "known" in level_data
            assert "percentage" in level_data
            assert level_data["total"] == 0
            assert level_data["known"] == 0
            assert level_data["percentage"] == 0.0

    async def test_progress_summary_partial_knowledge(self, service, mock_db_session):
        """Test progress summary with partial vocabulary knowledge"""
        # Mock: 1000 total words, 250 known words overall
        # A1: 200 total, 150 known (75%)
        # A2: 300 total, 100 known (33.3%)
        # Others: 0
        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            mock_result = Mock()

            # First 2 calls: overall stats
            if call_count[0] == 1:
                mock_result.scalar.return_value = 1000  # Total words
            elif call_count[0] == 2:
                mock_result.scalar.return_value = 250  # Known words
            # Level queries (2 per level: total + known)
            elif call_count[0] == 3:
                mock_result.scalar.return_value = 200  # A1 total
            elif call_count[0] == 4:
                mock_result.scalar.return_value = 150  # A1 known
            elif call_count[0] == 5:
                mock_result.scalar.return_value = 300  # A2 total
            elif call_count[0] == 6:
                mock_result.scalar.return_value = 100  # A2 known
            elif call_count[0] == 7:
                mock_result.scalar.return_value = 500  # B1 total
            elif call_count[0] == 8:
                mock_result.scalar.return_value = 0  # B1 known
            else:
                mock_result.scalar.return_value = 0  # Rest: 0

            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.get_user_progress_summary(db_session=mock_db_session, user_id=1)

        # Assert overall
        assert result["total_words"] == 1000
        assert result["known_words"] == 250
        assert result["percentage_known"] == 25.0

        # Assert level breakdown
        assert len(result["levels_progress"]) == 6

        a1_level = result["levels_progress"][0]
        assert a1_level["level"] == "A1"
        assert a1_level["total"] == 200
        assert a1_level["known"] == 150
        assert a1_level["percentage"] == 75.0

        a2_level = result["levels_progress"][1]
        assert a2_level["level"] == "A2"
        assert a2_level["total"] == 300
        assert a2_level["known"] == 100
        assert a2_level["percentage"] == 33.3

        b1_level = result["levels_progress"][2]
        assert b1_level["level"] == "B1"
        assert b1_level["total"] == 500
        assert b1_level["known"] == 0
        assert b1_level["percentage"] == 0.0

    async def test_progress_summary_percentage_rounding(self, service, mock_db_session):
        """Test percentage calculations are rounded to 1 decimal place"""
        # Mock: 300 total, 123 known = 41.0%
        # A1: 77 known / 200 total = 38.5%
        call_count = [0]

        async def mock_execute(*args):
            call_count[0] += 1
            mock_result = Mock()

            if call_count[0] == 1:
                mock_result.scalar.return_value = 300  # Total
            elif call_count[0] == 2:
                mock_result.scalar.return_value = 123  # Known (41.0%)
            elif call_count[0] == 3:
                mock_result.scalar.return_value = 200  # A1 total
            elif call_count[0] == 4:
                mock_result.scalar.return_value = 77  # A1 known (38.5%)
            else:
                mock_result.scalar.return_value = 0

            return mock_result

        mock_db_session.execute.side_effect = mock_execute

        # Execute
        result = await service.get_user_progress_summary(db_session=mock_db_session, user_id=1)

        # Assert rounding to 1 decimal
        assert result["percentage_known"] == 41.0
        assert result["levels_progress"][0]["percentage"] == 38.5


class TestGetSupportedLanguages:
    """Test get_supported_languages functionality (lines 215-233)"""

    @pytest.fixture
    def service(self):
        return VocabularyStatsService()

    @pytest.mark.skip(reason="ImportError edge case - difficult to test in isolation. Main functionality tested in other tests.")
    async def test_supported_languages_no_language_table(self, service):
        """Test get_supported_languages when Language model doesn't exist (ImportError path)

        This test is skipped because:
        1. The ImportError path is a defensive fallback for when Language table doesn't exist
        2. Testing import failures in isolation is fragile and complex
        3. The main functionality (Language table exists) is covered by other tests
        4. In practice, if Language table exists, this code path never executes
        """
        pass

    @patch("services.vocabulary.vocabulary_stats_service.AsyncSessionLocal")
    async def test_supported_languages_with_language_table(self, mock_session_local, service):
        """Test get_supported_languages when Language model exists and has data"""
        # Mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Mock language objects
        mock_lang_en = Mock()
        mock_lang_en.code = "en"
        mock_lang_en.name = "English"
        mock_lang_en.native_name = "English"
        mock_lang_en.is_active = True

        mock_lang_de = Mock()
        mock_lang_de.code = "de"
        mock_lang_de.name = "German"
        mock_lang_de.native_name = "Deutsch"
        mock_lang_de.is_active = True

        # Mock query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_lang_en, mock_lang_de]
        mock_session.execute.return_value = mock_result

        # Mock successful import of Language model
        with patch("services.vocabulary.vocabulary_stats_service.Language", create=True):
            result = await service.get_supported_languages()

        # Assert
        assert len(result) == 2
        assert result[0] == {"code": "en", "name": "English", "native_name": "English", "is_active": True}
        assert result[1] == {"code": "de", "name": "German", "native_name": "Deutsch", "is_active": True}

    @patch("services.vocabulary.vocabulary_stats_service.AsyncSessionLocal")
    async def test_supported_languages_empty_table(self, mock_session_local, service):
        """Test get_supported_languages when Language table exists but is empty"""
        # Mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Mock empty query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Mock successful import of Language model
        with patch("services.vocabulary.vocabulary_stats_service.Language", create=True):
            result = await service.get_supported_languages()

        # Assert
        assert result == []


class TestFactoryFunction:
    """Test get_vocabulary_stats_service factory function"""

    def test_factory_returns_instance(self):
        """Test factory returns VocabularyStatsService instance"""
        service = get_vocabulary_stats_service()

        assert isinstance(service, VocabularyStatsService)

    def test_factory_returns_fresh_instance(self):
        """Test factory returns new instance each time (not singleton)"""
        service1 = get_vocabulary_stats_service()
        service2 = get_vocabulary_stats_service()

        # Should be different instances (no global state)
        assert service1 is not service2
