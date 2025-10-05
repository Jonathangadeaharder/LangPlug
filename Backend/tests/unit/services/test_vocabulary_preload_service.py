"""
Test suite for VocabularyPreloadService
Tests vocabulary loading, level management, and user progress tracking
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from services.vocabulary.vocabulary_preload_service import VocabularyPreloadService, get_vocabulary_preload_service


class TestVocabularyPreloadService:
    """Test VocabularyPreloadService initialization and basic functionality"""

    def test_initialization(self):
        """Test service initialization with default data path"""
        service = VocabularyPreloadService()

        # Check that data_path is properly set to expected location
        assert service.data_path.name == "data"
        # We should not check if it exists to avoid coupling to real filesystem

    def test_initialization_with_custom_path(self):
        """Test service initialization with custom data path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir)
            service = VocabularyPreloadService(data_path=custom_path)

            assert service.data_path == custom_path
            assert service.data_path.exists()  # We control this temp directory

    def test_get_vocabulary_preload_service_utility(self):
        """Test utility function for service creation"""
        service = get_vocabulary_preload_service()
        assert isinstance(service, VocabularyPreloadService)


class TestLoadVocabularyFiles:
    """Test vocabulary file loading functionality"""

    @pytest.fixture
    def service(self):
        """Create service instance with temporary data path"""
        temp_dir = Path(tempfile.mkdtemp())
        # Use constructor injection instead of directly setting attribute
        service = VocabularyPreloadService(data_path=temp_dir)
        return service

    def teardown_method(self):
        """Clean up temporary files"""
        # Cleanup is handled by tempfile

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_load_vocabulary_files_success(self, mock_session_local, service):
        """Test successful vocabulary file loading"""
        # Create mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Create temporary vocabulary files
        test_files = ["a1.txt", "a2.txt", "b1.txt", "b2.txt"]
        for filename in test_files:
            file_path = service.data_path / filename
            file_path.write_text("word1\nword2\nword3\n", encoding="utf-8")

        # Mock the _load_level_vocabulary method
        with patch.object(service, "_load_level_vocabulary", return_value=3):
            result = await service.load_vocabulary_files()

        # Verify results
        assert result == {"A1": 3, "A2": 3, "B1": 3, "B2": 3}

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_load_vocabulary_files_missing_files(self, mock_session_local, service):
        """Test vocabulary loading with missing files"""
        # Create mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Don't create any files
        result = await service.load_vocabulary_files()

        # Verify all levels return 0 for missing files
        assert result == {"A1": 0, "A2": 0, "B1": 0, "B2": 0}

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_load_vocabulary_files_mixed_scenario(self, mock_session_local, service):
        """Test vocabulary loading with some files present, some missing"""
        # Create mock session
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Create only A1 and B2 files
        (service.data_path / "a1.txt").write_text("word1\nword2\n", encoding="utf-8")
        (service.data_path / "b2.txt").write_text("word1\nword2\nword3\nword4\n", encoding="utf-8")

        # Mock the _load_level_vocabulary method
        async def mock_load_level(session, level, file_path):
            if level == "A1":
                return 2
            elif level == "B2":
                return 4
            return 0

        with patch.object(service, "_load_level_vocabulary", side_effect=mock_load_level):
            result = await service.load_vocabulary_files()

        # Verify results
        assert result == {"A1": 2, "A2": 0, "B1": 0, "B2": 4}


class TestLoadLevelVocabulary:
    """Test individual level vocabulary loading"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    @patch("builtins.open", new_callable=mock_open, read_data="word1\nword2\n\nword3\n")
    async def test_load_level_vocabulary_success(self, mock_file, service):
        """Test successful level vocabulary loading"""
        mock_session = AsyncMock()
        mock_file_path = Path("test_a1.txt")

        # Mock database operations
        mock_session.get.return_value = None  # No existing words
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()

        # Mock the actual database model creation to avoid NameError
        with patch("services.vocabulary_preload_service.VocabularyWord") as mock_vocab_concept:
            # Mock the constructor call
            mock_vocab_instance = Mock()
            mock_vocab_concept.return_value = mock_vocab_instance

            result = await service._load_level_vocabulary(mock_session, "A1", mock_file_path)

        # Verify data was persisted
        mock_session.commit.assert_called_once()

        # Result should be the number of words loaded
        assert result == 3
        # Removed mock_file.assert_called_once_with() - testing behavior (words loaded), not file opening details
        # Removed add.call_count assertion - testing behavior (result count), not implementation

    @patch("builtins.open", new_callable=mock_open, read_data="")
    async def test_load_level_vocabulary_empty_file(self, mock_file, service):
        """Test loading from empty file"""
        mock_session = AsyncMock()
        mock_file_path = Path("empty_test.txt")

        result = await service._load_level_vocabulary(mock_session, "A1", mock_file_path)

        # Empty file should result in 0 words loaded
        assert result == 0
        # Removed add.assert_not_called() - testing behavior (0 words loaded), not implementation

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    async def test_load_level_vocabulary_file_error(self, mock_file, service):
        """Test loading when file cannot be opened"""
        mock_session = AsyncMock()
        mock_file_path = Path("nonexistent.txt")

        with pytest.raises(Exception, match="Failed to load vocabulary from"):
            await service._load_level_vocabulary(mock_session, "A1", mock_file_path)

    @patch("builtins.open", new_callable=mock_open, read_data="word1\nword2\n")
    async def test_load_level_vocabulary_database_error(self, mock_file, service):
        """Test database error handling during vocabulary loading"""
        mock_session = AsyncMock()
        # Configure synchronous methods on AsyncSession
        mock_session.add = Mock()  # session.add() is synchronous even on AsyncSession
        mock_file_path = Path("test.txt")

        # Mock database error
        mock_session.get.return_value = None
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.rollback = AsyncMock()

        result = await service._load_level_vocabulary(mock_session, "A1", mock_file_path)

        # Should handle error gracefully and return 0
        assert result == 0
        mock_session.rollback.assert_called_once()


class TestGetLevelWords:
    """Test getting words for specific difficulty levels"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    async def test_get_level_words_with_session(self, service):
        """Test getting level words when session is provided"""
        mock_session = AsyncMock()

        with patch.object(
            service,
            "_execute_get_level_words",
            return_value=[
                {
                    "id": 1,
                    "word": "test",
                    "difficulty_level": "A1",
                    "word_type": "noun",
                    "part_of_speech": "noun",
                    "definition": "",
                }
            ],
        ):
            result = await service.get_level_words("A1", mock_session)

            assert len(result) == 1
            assert result[0]["word"] == "test"
            # Removed mock_execute.assert_called_once_with() - testing behavior (result), not internal method calls

    @patch("core.database.engine")
    async def test_get_level_words_without_session(self, mock_engine, service):
        """Test getting level words when no session is provided"""
        # Mock session maker and session
        mock_session = AsyncMock()

        with patch("sqlalchemy.ext.asyncio.async_sessionmaker") as mock_sessionmaker:
            mock_sessionmaker.return_value.return_value.__aenter__.return_value = mock_session

            with patch.object(service, "_execute_get_level_words", return_value=[]):
                result = await service.get_level_words("B1")

                assert result == []
                # Removed mock_execute.assert_called_once_with() - testing behavior (result), not internal method calls

    async def test_get_level_words_error_handling(self, service):
        """Test error handling in get_level_words"""
        mock_session = AsyncMock()

        with patch.object(service, "_execute_get_level_words", side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Failed to get B1 words"):
                await service.get_level_words("B1", mock_session)

    async def test_execute_get_level_words(self, service):
        """Test the actual database query execution"""
        mock_session = AsyncMock()

        # Mock concept and translation pairs (since we now use joins)
        Mock(id="concept-1", difficulty_level="A1", semantic_category="noun")
        Mock(word="test1")
        Mock(id="concept-2", difficulty_level="A1", semantic_category="verb")
        Mock(word="test2")
        Mock(id="concept-3", difficulty_level="A1", semantic_category=None)
        Mock(word="test3")

        # Mock database word objects
        mock_word1 = Mock(id="id1", word="test1", difficulty_level="A1", part_of_speech="noun")
        mock_word2 = Mock(id="id2", word="test2", difficulty_level="A1", part_of_speech="verb")
        mock_word3 = Mock(id="id3", word="test3", difficulty_level="A1", part_of_speech=None)

        # Mock scalars().all() pattern
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_word1, mock_word2, mock_word3]

        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args):
            return mock_result

        mock_session.execute.side_effect = mock_execute

        with patch("sqlalchemy.select"), patch("services.vocabulary_preload_service.VocabularyWord"):
            result = await service._execute_get_level_words(mock_session, "A1")

        # Verify result structure
        assert len(result) == 3
        assert result[0]["word"] == "test1"
        assert result[0]["word_type"] == "noun"
        assert result[1]["word"] == "test2"
        assert result[2]["part_of_speech"] == "noun"  # Default when word_type is None


class TestGetUserKnownWords:
    """Test getting user's known words"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    async def test_get_user_known_words_with_session(self, service):
        """Test getting user known words with provided session"""
        mock_session = AsyncMock()

        with patch.object(service, "_execute_get_user_known_words", return_value={"word1", "word2"}):
            result = await service.get_user_known_words(123, "A1", mock_session)

            assert result == {"word1", "word2"}
            # Removed mock_execute.assert_called_once_with() - testing behavior (result), not internal method calls

    @patch("core.database.engine")
    async def test_get_user_known_words_without_session(self, mock_engine, service):
        """Test getting user known words without session"""
        mock_session = AsyncMock()

        with patch("sqlalchemy.ext.asyncio.async_sessionmaker") as mock_sessionmaker:
            mock_sessionmaker.return_value.return_value.__aenter__.return_value = mock_session

            with patch.object(service, "_execute_get_user_known_words", return_value=set()):
                result = await service.get_user_known_words(123)

                assert result == set()
                # Removed mock_execute.assert_called_once_with() - testing behavior (result), not internal method calls

    async def test_get_user_known_words_error_handling(self, service):
        """Test error handling in get_user_known_words"""
        mock_session = AsyncMock()

        with patch.object(service, "_execute_get_user_known_words", side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Failed to get user known words"):
                await service.get_user_known_words(123, session=mock_session)

    async def test_execute_get_user_known_words_with_level(self, service):
        """Test executing user known words query with specific level"""
        mock_session = AsyncMock()

        mock_scalars = Mock()
        mock_scalars.all.return_value = ["word1", "word2", "word3"]

        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args):
            return mock_result

        mock_session.execute.side_effect = mock_execute

        with patch("sqlalchemy.select") as mock_select:
            mock_stmt = Mock()
            mock_select.return_value.join.return_value.where.return_value = mock_stmt

            with (
                patch("services.vocabulary_preload_service.VocabularyWord"),
                patch("database.models.UserVocabularyProgress"),
            ):
                result = await service._execute_get_user_known_words(mock_session, 123, "A1")

        assert result == {"word1", "word2", "word3"}
        # Removed execute.assert_called_once() - testing behavior (result), not query execution

    async def test_execute_get_user_known_words_without_level(self, service):
        """Test executing user known words query without specific level"""
        mock_session = AsyncMock()

        mock_scalars = Mock()
        mock_scalars.all.return_value = ["word1", "word2"]

        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args):
            return mock_result

        mock_session.execute.side_effect = mock_execute

        with patch("sqlalchemy.select") as mock_select:
            mock_stmt = Mock()
            mock_select.return_value.join.return_value.where.return_value = mock_stmt

            with (
                patch("services.vocabulary_preload_service.VocabularyWord"),
                patch("database.models.UserVocabularyProgress"),
            ):
                result = await service._execute_get_user_known_words(mock_session, 123, None)

        assert result == {"word1", "word2"}


class TestMarkUserWordKnown:
    """Test marking words as known/unknown for users"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_mark_user_word_known_success(self, mock_session_local, service):
        """Test successfully marking a word as known"""
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Configure synchronous methods on AsyncSession
        mock_session.add = Mock()  # session.add() is synchronous even on AsyncSession

        # Mock vocabulary translation lookup (first query)
        mock_vocab_translation = Mock()
        mock_vocab_translation.concept_id = "concept-123"
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = mock_vocab_translation

        # Mock existing progress lookup (second query) - simulating no existing progress
        mock_progress_result = Mock()
        mock_progress_result.scalar_one_or_none.return_value = None

        # Set up execute to return different results for different queries
        mock_session.execute.side_effect = [mock_vocab_result, mock_progress_result]

        with patch("sqlalchemy.select"), patch("database.models.VocabularyWord"):
            with patch("database.models.UserVocabularyProgress"):
                result = await service.mark_user_word_known(123, "test_word", True)

        assert result is True
        mock_session.commit.assert_called_once()

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_mark_user_word_known_word_not_found(self, mock_session_local, service):
        """Test marking word as known when word doesn't exist in vocabulary"""
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Mock vocabulary lookup returning None
        mock_vocab_result = Mock()
        mock_vocab_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_vocab_result

        with patch("sqlalchemy.select"):
            result = await service.mark_user_word_known(123, "nonexistent_word", True)

        assert result is False

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_mark_user_word_known_error_handling(self, mock_session_local, service):
        """Test error handling in mark_user_word_known"""
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Mock database error
        mock_session.execute.side_effect = Exception("Database error")

        result = await service.mark_user_word_known(123, "test_word", True)

        assert result is False


class TestBulkMarkLevelKnown:
    """Test bulk marking level words as known/unknown"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    async def test_bulk_mark_level_known_success(self, service):
        """Test successfully bulk marking level words"""
        mock_level_words = [{"word": "word1"}, {"word": "word2"}, {"word": "word3"}]

        with (
            patch.object(service, "get_level_words", return_value=mock_level_words),
            patch.object(service, "mark_user_word_known", return_value=True),
        ):
            result = await service.bulk_mark_level_known(123, "A1", True)

        assert result == 3
        # Removed mock_mark.call_count assertion - testing behavior (result count), not internal method calls

    async def test_bulk_mark_level_known_partial_success(self, service):
        """Test bulk marking with some failures"""
        mock_level_words = [{"word": "word1"}, {"word": "word2"}, {"word": "word3"}]

        # Mock mark_user_word_known to succeed for some words
        mark_results = [True, False, True]

        with (
            patch.object(service, "get_level_words", return_value=mock_level_words),
            patch.object(service, "mark_user_word_known", side_effect=mark_results),
        ):
            result = await service.bulk_mark_level_known(123, "A1", True)

        assert result == 2  # Only 2 successful

    async def test_bulk_mark_level_known_error(self, service):
        """Test error handling in bulk mark level known"""
        with patch.object(service, "get_level_words", side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Failed to bulk mark A1 words"):
                await service.bulk_mark_level_known(123, "A1", True)


class TestGetVocabularyStats:
    """Test vocabulary statistics retrieval"""

    @pytest.fixture
    def service(self):
        return VocabularyPreloadService()

    async def test_get_vocabulary_stats_with_session(self, service):
        """Test getting vocabulary stats with provided session"""
        mock_session = AsyncMock()

        # Mock database result
        mock_row1 = Mock()
        mock_row1.difficulty_level = "A1"
        mock_row1.total_words = 100
        mock_row1.has_definition = 0
        mock_row1.user_known = 25

        mock_row2 = Mock()
        mock_row2.difficulty_level = "A2"
        mock_row2.total_words = 150
        mock_row2.has_definition = 0
        mock_row2.user_known = 40

        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result

        with patch("sqlalchemy.text"):
            result = await service.get_vocabulary_stats(mock_session)

        expected = {
            "A1": {"total_words": 100, "has_definition": 0, "user_known": 25},
            "A2": {"total_words": 150, "has_definition": 0, "user_known": 40},
        }
        assert result == expected
        # Removed execute.assert_called_once() - testing behavior (result), not query execution

    @patch("services.vocabulary_preload_service.AsyncSessionLocal")
    async def test_get_vocabulary_stats_without_session(self, mock_session_local, service):
        """Test getting vocabulary stats without provided session"""
        mock_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Mock empty result
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        with patch("sqlalchemy.text"):
            result = await service.get_vocabulary_stats()

        assert result == {}
        # Removed execute.assert_called_once() - testing behavior (result), not query execution

    async def test_get_vocabulary_stats_error_handling(self, service):
        """Test error handling in get_vocabulary_stats"""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        with patch("sqlalchemy.text"), pytest.raises(Exception, match="Failed to get vocabulary stats"):
            await service.get_vocabulary_stats(mock_session)
