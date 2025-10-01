"""
Integration tests for refactored vocabulary services
Verifies that the facade correctly delegates to sub-services
"""

from unittest.mock import AsyncMock

import pytest

from services.vocabulary.vocabulary_progress_service import VocabularyProgressService
from services.vocabulary.vocabulary_query_service import VocabularyQueryService
from services.vocabulary.vocabulary_stats_service import VocabularyStatsService
from services.vocabulary_service import VocabularyService, vocabulary_service


class TestVocabularyServiceArchitecture:
    """Test the refactored service architecture"""

    def test_service_initialization(self):
        """Test that facade initializes with all sub-services"""
        service = VocabularyService()

        assert service.query_service is not None
        assert service.progress_service is not None
        assert service.stats_service is not None

        assert isinstance(service.query_service, VocabularyQueryService)
        assert isinstance(service.progress_service, VocabularyProgressService)
        assert isinstance(service.stats_service, VocabularyStatsService)

    def test_global_instance_available(self):
        """Test that global vocabulary_service instance exists"""
        assert vocabulary_service is not None
        assert isinstance(vocabulary_service, VocabularyService)

    def test_facade_has_all_public_methods(self):
        """Test that facade exposes all required public methods"""
        service = VocabularyService()

        # Query service methods
        assert hasattr(service, "get_word_info")
        assert hasattr(service, "get_vocabulary_library")
        assert hasattr(service, "search_vocabulary")

        # Progress service methods
        assert hasattr(service, "mark_word_known")
        assert hasattr(service, "bulk_mark_level")
        assert hasattr(service, "get_user_vocabulary_stats")

        # Stats service methods
        assert hasattr(service, "get_vocabulary_stats")
        assert hasattr(service, "get_user_progress_summary")
        assert hasattr(service, "get_supported_languages")

        # Legacy methods
        assert hasattr(service, "get_vocabulary_level")
        assert hasattr(service, "mark_concept_known")

    @pytest.mark.asyncio
    async def test_facade_delegates_to_query_service(self):
        """Test that query methods delegate to query service"""
        service = VocabularyService()
        mock_db = AsyncMock()

        # Mock the query service method
        service.query_service.get_word_info = AsyncMock(return_value={"found": True, "word": "test", "lemma": "test"})

        result = await service.get_word_info("test", "de", mock_db)

        assert result["found"] is True
        service.query_service.get_word_info.assert_called_once_with("test", "de", mock_db)

    @pytest.mark.asyncio
    async def test_facade_delegates_to_progress_service(self):
        """Test that progress methods delegate to progress service"""
        service = VocabularyService()
        mock_db = AsyncMock()

        # Mock the progress service method
        service.progress_service.mark_word_known = AsyncMock(
            return_value={"success": True, "word": "test", "is_known": True}
        )

        result = await service.mark_word_known(123, "test", "de", True, mock_db)

        assert result["success"] is True
        service.progress_service.mark_word_known.assert_called_once_with(123, "test", "de", True, mock_db)

    @pytest.mark.asyncio
    async def test_facade_delegates_to_stats_service(self):
        """Test that stats methods delegate to stats service"""
        service = VocabularyService()

        # Mock the stats service method
        service.stats_service.get_vocabulary_stats = AsyncMock(
            return_value={"target_language": "de", "levels": {}, "total_words": 100, "total_known": 50}
        )

        result = await service.get_vocabulary_stats("de", 123)

        assert result["total_words"] == 100
        service.stats_service.get_vocabulary_stats.assert_called_once()


class TestSubServiceIndependence:
    """Test that sub-services can be used independently"""

    def test_query_service_standalone(self):
        """Test VocabularyQueryService can be instantiated independently"""
        from services.vocabulary.vocabulary_query_service import VocabularyQueryService

        service = VocabularyQueryService()
        assert service is not None
        assert hasattr(service, "get_word_info")
        assert hasattr(service, "get_vocabulary_library")
        assert hasattr(service, "search_vocabulary")

    def test_progress_service_standalone(self):
        """Test VocabularyProgressService can be instantiated independently"""
        from services.vocabulary.vocabulary_progress_service import VocabularyProgressService

        service = VocabularyProgressService()
        assert service is not None
        assert hasattr(service, "mark_word_known")
        assert hasattr(service, "bulk_mark_level")
        assert hasattr(service, "get_user_vocabulary_stats")

    def test_stats_service_standalone(self):
        """Test VocabularyStatsService can be instantiated independently"""
        from services.vocabulary.vocabulary_stats_service import VocabularyStatsService

        service = VocabularyStatsService()
        assert service is not None
        assert hasattr(service, "get_vocabulary_stats")
        assert hasattr(service, "get_user_progress_summary")
        assert hasattr(service, "get_supported_languages")


class TestBackwardCompatibility:
    """Test that refactored service maintains backward compatibility"""

    def test_same_import_path_works(self):
        """Test that original import path still works"""
        from services.vocabulary_service import get_vocabulary_service, vocabulary_service

        assert vocabulary_service is not None
        service = get_vocabulary_service()
        assert service is not None

    @pytest.mark.asyncio
    async def test_legacy_method_signatures_work(self):
        """Test that legacy method signatures are maintained"""
        service = VocabularyService()

        # Mock the underlying service
        service.query_service.get_vocabulary_library = AsyncMock(
            return_value={
                "words": [{"word": "test", "is_known": False}],
                "total_count": 1,
                "limit": 50,
                "offset": 0,
                "language": "de",
                "level": "A1",
            }
        )

        # Test legacy method with old signature
        result = await service.get_vocabulary_level("A1", "de", "en", None, 50, 0)

        assert "level" in result
        assert "target_language" in result
        assert "translation_language" in result
        assert "words" in result
        assert "total_count" in result
        assert "known_count" in result

    @pytest.mark.asyncio
    async def test_legacy_concept_method_works(self):
        """Test that legacy concept-based method is maintained"""
        service = VocabularyService()

        result = await service.mark_concept_known(123, "concept-id-123", True)

        assert result["success"] is True
        assert result["concept_id"] == "concept-id-123"
        assert result["known"] is True


class TestServiceArchitectureMetrics:
    """Test that architecture improvements are measurable"""

    def test_service_line_counts_reasonable(self):
        """Test that each service is reasonably sized"""
        import inspect

        # Facade should be small (just delegation)
        facade_lines = len(inspect.getsource(VocabularyService).split("\n"))
        assert facade_lines < 200, "Facade should be < 200 lines"

        # Sub-services should be focused (< 400 lines each)
        query_lines = len(inspect.getsource(VocabularyQueryService).split("\n"))
        assert query_lines < 400, "Query service should be < 400 lines"

        progress_lines = len(inspect.getsource(VocabularyProgressService).split("\n"))
        assert progress_lines < 300, "Progress service should be < 300 lines"

        stats_lines = len(inspect.getsource(VocabularyStatsService).split("\n"))
        assert stats_lines < 300, "Stats service should be < 300 lines"

    def test_services_have_focused_responsibilities(self):
        """Test that each service has a clear, focused responsibility"""
        query_service = VocabularyQueryService()
        progress_service = VocabularyProgressService()
        stats_service = VocabularyStatsService()

        # Query service should have query methods
        query_methods = [m for m in dir(query_service) if not m.startswith("_") and callable(getattr(query_service, m))]
        assert "get_word_info" in query_methods
        assert "search_vocabulary" in query_methods
        assert "get_vocabulary_library" in query_methods

        # Progress service should have progress methods
        progress_methods = [
            m for m in dir(progress_service) if not m.startswith("_") and callable(getattr(progress_service, m))
        ]
        assert "mark_word_known" in progress_methods
        assert "bulk_mark_level" in progress_methods

        # Stats service should have stats methods
        stats_methods = [m for m in dir(stats_service) if not m.startswith("_") and callable(getattr(stats_service, m))]
        assert "get_vocabulary_stats" in stats_methods
        assert "get_supported_languages" in stats_methods
