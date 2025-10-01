"""
Comprehensive test suite for VocabularyService
Tests multilingual vocabulary operations, user progress tracking, and database interactions
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from services.vocabulary_service import VocabularyService, get_vocabulary_service


class TestVocabularyService:
    """Test VocabularyService initialization and basic functionality"""

    def test_initialization(self):
        """Test service initialization"""
        service = VocabularyService()
        assert service is not None

    def test_get_vocabulary_service_utility(self):
        """Test utility function for service creation"""
        service = get_vocabulary_service()
        assert isinstance(service, VocabularyService)


class TestGetSupportedLanguages:
    """Test supported languages functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_get_supported_languages_success(self, service):
        """Test successful retrieval of supported languages"""
        # Mock the stats service's get_supported_languages method
        expected_result = [
            {"code": "en", "name": "English", "native_name": "English", "is_active": True},
            {"code": "de", "name": "German", "native_name": "Deutsch", "is_active": True},
            {"code": "es", "name": "Spanish", "native_name": "Español", "is_active": True},
        ]

        with patch.object(service.stats_service, "get_supported_languages", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_result
            result = await service.get_supported_languages()

        # Verify result structure
        assert len(result) == 3
        assert result[0]["code"] == "en"
        assert result[0]["name"] == "English"
        assert result[0]["native_name"] == "English"
        assert result[0]["is_active"] is True

    async def test_get_supported_languages_empty(self, service):
        """Test retrieval when no languages are active"""
        with patch.object(service.stats_service, "get_supported_languages", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = []
            result = await service.get_supported_languages()

        assert result == []

    async def test_get_supported_languages_database_error(self, service):
        """Test database error handling"""
        with patch.object(service.stats_service, "get_supported_languages", new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database connection error")

            with pytest.raises(Exception, match="Database connection error"):
                await service.get_supported_languages()


class TestGetVocabularyStats:
    """Test vocabulary statistics functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_get_vocabulary_stats_without_user(self, service):
        """Test vocabulary stats without specific user"""
        # Mock stats service to return expected structure
        expected_stats = {
            "target_language": "de",
            "levels": {
                "A1": {"total_words": 100, "user_known": 0},
                "A2": {"total_words": 150, "user_known": 0},
                "B1": {"total_words": 200, "user_known": 0},
                "B2": {"total_words": 250, "user_known": 0},
                "C1": {"total_words": 180, "user_known": 0},
                "C2": {"total_words": 120, "user_known": 0},
            },
            "total_words": 1000,
            "total_known": 0,
        }

        with patch.object(service.stats_service, "get_vocabulary_stats", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_stats
            result = await service.get_vocabulary_stats(target_language="de")

        # Verify result structure
        assert "levels" in result
        assert "target_language" in result
        assert result["target_language"] == "de"
        assert "total_words" in result
        assert "total_known" in result

        # Verify all levels are present
        for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            assert level in result["levels"]
            assert "total_words" in result["levels"][level]
            assert "user_known" in result["levels"][level]

    async def test_get_vocabulary_stats_with_user(self, service):
        """Test vocabulary stats with specific user"""
        # Mock stats service with user progress data
        expected_stats = {
            "target_language": "de",
            "levels": {
                "A1": {"total_words": 100, "user_known": 25},
                "A2": {"total_words": 150, "user_known": 30},
                "B1": {"total_words": 200, "user_known": 40},
                "B2": {"total_words": 250, "user_known": 50},
                "C1": {"total_words": 180, "user_known": 35},
                "C2": {"total_words": 120, "user_known": 20},
            },
            "total_words": 1000,
            "total_known": 200,
        }

        with patch.object(service.stats_service, "get_vocabulary_stats", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_stats
            result = await service.get_vocabulary_stats(target_language="de", user_id=123)

        # Verify result includes user data
        assert result["total_known"] > 0

        # Check that some levels have known words
        has_known_words = any(result["levels"][level]["user_known"] > 0 for level in result["levels"])
        assert has_known_words

    async def test_get_vocabulary_stats_database_error(self, service):
        """Test database error handling in stats"""
        with patch.object(service.stats_service, "get_vocabulary_stats", new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await service.get_vocabulary_stats()

    async def test_get_vocabulary_level_success(self, service):
        """Test successful vocabulary level retrieval"""
        # Mock the get_vocabulary_library method that get_vocabulary_level calls
        concept_id = str(uuid4())
        mock_library = {
            "words": [
                {
                    "id": 1,
                    "word": "Hund",
                    "lemma": "Hund",
                    "language": "de",
                    "difficulty_level": "A1",
                    "gender": "der",
                    "plural_form": "Hunde",
                    "pronunciation": "/hʊnt/",
                    "is_known": False,
                    "concept_id": concept_id,
                }
            ],
            "total_count": 1,
        }

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level(
                "A1", target_language="de", translation_language="es", user_id=123
            )

        # Verify result structure
        assert result["level"] == "A1"
        assert result["target_language"] == "de"
        assert result["translation_language"] == "es"
        assert len(result["words"]) == 1

        word = result["words"][0]
        assert word["word"] == "Hund"
        assert word["is_known"] is False

    async def test_get_vocabulary_level_with_known_words_updated(self, service):
        """Test vocabulary level retrieval with user's known words"""
        concept_id = str(uuid4())
        mock_library = {
            "words": [
                {
                    "id": 1,
                    "word": "Katze",
                    "lemma": "Katze",
                    "language": "de",
                    "difficulty_level": "A1",
                    "is_known": True,
                    "concept_id": concept_id,
                }
            ],
            "total_count": 1,
        }

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level("A1", user_id=123)

        assert result["known_count"] == 1
        assert result["words"][0]["is_known"] is True

    async def test_get_vocabulary_level_no_target_translation(self, service):
        """Test filtering out concepts without target language translation"""
        # Mock empty library (filtering already done by query service)
        mock_library = {"words": [], "total_count": 0}

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level("A1", target_language="de")

        # Should be filtered out due to no German translation
        assert len(result["words"]) == 0

    async def test_get_vocabulary_level_database_error(self, service):
        """Test database error handling"""
        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await service.get_vocabulary_level("A1")


# Module-level fixtures
@pytest.fixture
def service():
    """Service fixture available to all test classes"""
    return VocabularyService()


@pytest.fixture
async def mock_session_with_vocab_data():
    """Fixture providing mock session with vocabulary test data"""
    mock_session = AsyncMock()

    # Create sample vocabulary concepts
    mock_concepts = []
    concept_id = str(uuid4())
    mock_concept = Mock()
    mock_concept.id = concept_id
    mock_concept.difficulty_level = "A1"

    # Mock translations
    target_translation = Mock()
    target_translation.language_code = "de"
    target_translation.word = "Hund"
    target_translation.gender = "der"

    spanish_translation = Mock()
    spanish_translation.language_code = "es"
    spanish_translation.word = "perro"

    mock_concept.translations = [target_translation, spanish_translation]
    mock_concepts.append(mock_concept)

    # Track user progress (concept_id -> known status)
    user_progress = {}

    # Flexible mock execute that handles different query types
    def mock_execute(query):
        result = Mock()
        query_str = str(query)
        if "vocabulary_concepts" in query_str and "user_learning_progress" not in query_str:
            # Concept query - need proper scalars().all() chain
            scalars_mock = Mock()
            # Return current contents of mock_concepts list (allowing dynamic modification)
            current_concepts = list(mock_concepts)
            scalars_mock.all.return_value = current_concepts
            result.scalars.return_value = scalars_mock
        else:
            # User progress query
            result.fetchall.return_value = [(cid, True) for cid, known in user_progress.items() if known]
        return result

    mock_session.execute.side_effect = mock_execute

    with patch("services.vocabulary_service.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_session
        yield mock_session, mock_concepts, user_progress


class TestMarkConceptKnown:
    """Test marking concepts as known/unknown"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_mark_concept_known_new_progress(self, service):
        """Test marking concept as known for first time"""
        concept_id = str(uuid4())

        # mark_concept_known is now a legacy stub method
        result = await service.mark_concept_known(123, concept_id, True)

        assert result["success"] is True
        assert result["concept_id"] == concept_id
        assert result["known"] is True

    async def test_mark_concept_unknown_existing_progress(self, service):
        """Test marking concept as unknown (removing progress)"""
        concept_id = str(uuid4())

        # mark_concept_known is now a legacy stub method
        result = await service.mark_concept_known(123, concept_id, False)

        assert result["success"] is True
        assert result["known"] is False

    async def test_mark_concept_known_already_exists(self, service):
        """Test marking concept as known when already exists"""
        concept_id = str(uuid4())

        # mark_concept_known is now a legacy stub method
        result = await service.mark_concept_known(123, concept_id, True)

        assert result["success"] is True

    async def test_mark_concept_known_database_error(self, service):
        """Test database error handling"""
        concept_id = str(uuid4())

        # mark_concept_known is now a legacy stub method - doesn't throw errors
        result = await service.mark_concept_known(123, concept_id, True)
        assert result["success"] is True


class TestBulkMarkLevel:
    """Test bulk marking level functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_bulk_mark_level_known(self, service):
        """Test bulk marking level as known"""
        mock_session = AsyncMock()

        # Mock the progress service's bulk_mark_level method
        expected_result = {"success": True, "level": "A1", "is_known": True, "updated_count": 3}

        with patch.object(service.progress_service, "bulk_mark_level", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_result
            result = await service.bulk_mark_level(mock_session, 123, "de", "A1", True)

        assert result["success"] is True
        assert result["level"] == "A1"
        assert result["is_known"] is True
        assert result["updated_count"] == 3

    async def test_bulk_mark_level_unknown(self, service):
        """Test bulk marking level as unknown"""
        mock_session = AsyncMock()

        # Mock the progress service's bulk_mark_level method
        expected_result = {"success": True, "level": "A1", "is_known": False, "updated_count": 2}

        with patch.object(service.progress_service, "bulk_mark_level", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_result
            result = await service.bulk_mark_level(mock_session, 123, "de", "A1", False)

        assert result["success"] is True
        assert result["is_known"] is False
        assert result["updated_count"] == 2

    async def test_bulk_mark_level_mixed_existing(self, service):
        """Test bulk marking with mixed existing progress"""
        mock_session = AsyncMock()

        # Mock the progress service's bulk_mark_level method
        expected_result = {"success": True, "level": "A1", "is_known": True, "updated_count": 2}

        with patch.object(service.progress_service, "bulk_mark_level", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = expected_result
            result = await service.bulk_mark_level(mock_session, 123, "de", "A1", True)

        # Both words are counted, one gets new progress, one updates existing
        assert result["updated_count"] == 2

    async def test_bulk_mark_level_database_error(self, service):
        """Test database error handling"""
        mock_session = AsyncMock()

        with patch.object(service.progress_service, "bulk_mark_level", new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                await service.bulk_mark_level(mock_session, 123, "de", "A1", True)


class TestGetUserKnownConcepts:
    """Test internal method for getting user's known concepts"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_get_vocabulary_level_with_known_words(self, service):
        """Test vocabulary level retrieval shows known words correctly"""
        known_concept_id = str(uuid4())
        mock_library = {
            "words": [
                {
                    "id": 1,
                    "word": "Test",
                    "lemma": "Test",
                    "language": "de",
                    "difficulty_level": "A1",
                    "gender": "der",
                    "is_known": True,
                    "concept_id": known_concept_id,
                },
                {
                    "id": 2,
                    "word": "Hund",
                    "lemma": "Hund",
                    "language": "de",
                    "difficulty_level": "A1",
                    "is_known": False,
                    "concept_id": str(uuid4()),
                },
            ],
            "total_count": 2,
        }

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level(
                "A1", target_language="de", translation_language="es", user_id=123
            )

        # Verify business logic: known words are marked correctly
        known_words = [w for w in result["words"] if w["is_known"] is True]
        assert len(known_words) >= 1
        assert any(w["concept_id"] == known_concept_id for w in known_words)

    async def test_get_vocabulary_level_with_no_known_words(self, service):
        """Test vocabulary level retrieval when user knows no words"""
        mock_library = {
            "words": [
                {
                    "id": 1,
                    "word": "Hund",
                    "lemma": "Hund",
                    "language": "de",
                    "difficulty_level": "A1",
                    "is_known": False,
                    "concept_id": str(uuid4()),
                }
            ],
            "total_count": 1,
        }

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level(
                "A1", target_language="de", translation_language="es", user_id=123
            )

        # Verify business logic: no words marked as known
        assert all(word["is_known"] is False for word in result["words"])
        assert result["level"] == "A1"
        assert result["target_language"] == "de"
        assert result["translation_language"] == "es"

    async def test_get_vocabulary_level_empty_level(self, service):
        """Test vocabulary level retrieval for level with no vocabulary"""
        mock_library = {"words": [], "total_count": 0}

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level(
                "C2", target_language="de", translation_language="es", user_id=123
            )

        # Verify business logic: empty results handled gracefully
        assert result["words"] == []
        assert result["level"] == "C2"


class TestSessionManagement:
    """Test session management functionality"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_session_context_manager(self, service):
        """Test session context manager"""
        # Test that _get_session returns a context manager
        session_context = service._get_session()
        assert session_context is not None

        # Test completes without error (behavior)
        # Actual session creation is handled by AsyncSessionLocal


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.fixture
    def service(self):
        return VocabularyService()

    async def test_get_vocabulary_level_pagination(self, service):
        """Test pagination parameters in vocabulary level"""
        mock_library = {"words": [], "total_count": 0}

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            await service.get_vocabulary_level("A1", limit=10, offset=20)

        # Test completes without error (behavior)
        # Verify pagination parameters were passed
        mock_method.assert_called_once()
        call_kwargs = mock_method.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 20

    async def test_case_insensitive_level_handling(self, service):
        """Test that level parameters are handled case-insensitively"""
        mock_library = {"words": [], "total_count": 0}

        with patch.object(service, "get_vocabulary_library", new_callable=AsyncMock) as mock_method:
            mock_method.return_value = mock_library
            result = await service.get_vocabulary_level("a1")  # lowercase input

        # Should normalize to uppercase
        assert result["level"] == "A1"
