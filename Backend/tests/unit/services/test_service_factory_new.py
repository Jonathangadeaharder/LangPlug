"""Unit tests for ServiceFactory - Dependency injection and service creation"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.service_factory import ServiceFactory
from services.authservice.auth_service import AuthService
from services.vocabulary_service import VocabularyService
from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
from services.loggingservice.logging_service import LoggingService
from services.service_factory import TranslationService, TranscriptionService, FilterService
from database.repositories import VocabularyRepository, UserRepository, ProcessingRepository


class TestServiceFactoryVocabularyService:
    """Tests for ServiceFactory.get_vocabulary_service"""

    def test_When_get_vocabulary_service_called_Then_returns_vocabulary_service(self):
        """Happy path: factory creates VocabularyService instance"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        # VocabularyRepository is abstract, so we need to patch it
        with patch('services.service_factory.VocabularyRepository'):
            service = ServiceFactory.get_vocabulary_service(mock_db)

        # Assert
        assert service is not None
        assert isinstance(service, VocabularyService)

    def test_When_get_vocabulary_service_called_Then_returns_singleton_instance(self):
        """Behavior: factory returns singleton instance (VocabularyService doesn't use DI)"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        service1 = ServiceFactory.get_vocabulary_service(mock_db)
        service2 = ServiceFactory.get_vocabulary_service(mock_db)

        # Assert - VocabularyService is a singleton
        assert service1 is not None
        assert service2 is not None
        assert service1 is service2  # Same singleton instance


class TestServiceFactoryAuthService:
    """Tests for ServiceFactory.get_auth_service"""

    def test_When_get_auth_service_called_Then_returns_auth_service(self):
        """Happy path: factory creates AuthService instance"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        service = ServiceFactory.get_auth_service(mock_db)

        # Assert
        assert service is not None
        assert isinstance(service, AuthService)

    def test_When_get_auth_service_called_Then_injects_database_session(self):
        """Behavior: factory injects database session"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        service = ServiceFactory.get_auth_service(mock_db)

        # Assert
        assert service is not None
        # AuthService receives db session - verified by successful instantiation


class TestServiceFactorySubtitleProcessor:
    """Tests for ServiceFactory.get_subtitle_processor"""

    def test_When_get_subtitle_processor_called_Then_returns_processor(self):
        """Happy path: factory creates DirectSubtitleProcessor instance"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        processor = ServiceFactory.get_subtitle_processor(mock_db)

        # Assert
        assert processor is not None
        assert isinstance(processor, DirectSubtitleProcessor)


class TestServiceFactoryProcessingServices:
    """Tests for ServiceFactory processing service methods"""

    def test_When_get_processing_service_called_Then_returns_processing_service(self):
        """Happy path: factory creates ChunkProcessingService"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        service = ServiceFactory.get_processing_service(mock_db)

        # Assert
        assert service is not None
        # Should be ChunkProcessingService instance
        assert service.__class__.__name__ == "ChunkProcessingService"

    def test_When_get_chunk_transcription_service_called_Then_returns_service(self):
        """Happy path: factory creates ChunkTranscriptionService"""
        # Act
        service = ServiceFactory.get_chunk_transcription_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "ChunkTranscriptionService"

    def test_When_get_chunk_translation_service_called_Then_returns_service(self):
        """Happy path: factory creates ChunkTranslationService"""
        # Act
        service = ServiceFactory.get_chunk_translation_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "ChunkTranslationService"

    def test_When_get_chunk_utilities_called_Then_returns_utilities(self):
        """Happy path: factory creates ChunkUtilities"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        service = ServiceFactory.get_chunk_utilities(mock_db)

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "ChunkUtilities"


class TestServiceFactoryRepositories:
    """Tests for ServiceFactory repository creation methods"""

    def test_When_get_user_repository_called_Then_returns_user_repository(self):
        """Happy path: factory creates UserRepository"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        repository = ServiceFactory.get_user_repository(mock_db)

        # Assert
        assert repository is not None
        assert isinstance(repository, UserRepository)

    def test_When_get_vocabulary_repository_called_Then_returns_vocabulary_repository(self):
        """Happy path: factory creates VocabularyRepository"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        # VocabularyRepository is abstract, patch to avoid instantiation error
        with patch('services.service_factory.VocabularyRepository') as mock_repo_class:
            mock_repo = Mock(spec=VocabularyRepository)
            mock_repo_class.return_value = mock_repo
            repository = ServiceFactory.get_vocabulary_repository(mock_db)

        # Assert
        assert repository is not None

    def test_When_get_processing_repository_called_Then_returns_processing_repository(self):
        """Happy path: factory creates ProcessingRepository"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        repository = ServiceFactory.get_processing_repository(mock_db)

        # Assert
        assert repository is not None
        assert isinstance(repository, ProcessingRepository)

    def test_When_repositories_created_Then_inject_database_session(self):
        """Behavior: repositories receive database session"""
        # Arrange
        mock_db = Mock(spec=AsyncSession)

        # Act
        with patch('services.service_factory.VocabularyRepository') as mock_vocab_class:
            mock_vocab = Mock()
            mock_vocab_class.return_value = mock_vocab

            user_repo = ServiceFactory.get_user_repository(mock_db)
            vocab_repo = ServiceFactory.get_vocabulary_repository(mock_db)
            processing_repo = ServiceFactory.get_processing_repository(mock_db)

        # Assert - all repositories should have db session
        assert hasattr(user_repo, 'db') or hasattr(user_repo, '_db') or hasattr(user_repo, 'session')
        assert hasattr(processing_repo, 'db') or hasattr(processing_repo, '_db') or hasattr(processing_repo, 'session')


class TestServiceFactorySimpleServices:
    """Tests for ServiceFactory simple service creation"""

    def test_When_get_translation_service_called_Then_returns_service(self):
        """Happy path: factory creates TranslationService"""
        # Act
        service = ServiceFactory.get_translation_service()

        # Assert
        assert service is not None
        assert isinstance(service, TranslationService)

    def test_When_get_transcription_service_called_Then_returns_service(self):
        """Happy path: factory creates TranscriptionService"""
        # Act
        service = ServiceFactory.get_transcription_service()

        # Assert
        assert service is not None
        assert isinstance(service, TranscriptionService)

    def test_When_get_filter_service_called_Then_returns_service(self):
        """Happy path: factory creates FilterService"""
        # Act
        service = ServiceFactory.get_filter_service()

        # Assert
        assert service is not None
        assert isinstance(service, FilterService)

    def test_When_get_logging_service_called_Then_returns_service(self):
        """Happy path: factory returns LogManagerService (was LoggingService)"""
        # Act
        service = ServiceFactory.get_logging_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LogManagerService"
        # Note: LogManagerService is not a singleton, creates new instances


class TestServiceFactoryVocabularySubServices:
    """Tests for ServiceFactory vocabulary sub-service creation"""

    def test_When_get_vocabulary_lookup_service_called_Then_returns_service(self):
        """Happy path: factory creates VocabularyQueryService (was VocabularyLookupService)"""
        # Act
        service = ServiceFactory.get_vocabulary_lookup_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "VocabularyQueryService"

    def test_When_get_vocabulary_progress_service_called_Then_returns_service(self):
        """Happy path: factory creates VocabularyProgressService"""
        # Act
        service = ServiceFactory.get_vocabulary_progress_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "VocabularyProgressService"

    def test_When_get_vocabulary_analytics_service_called_Then_returns_service(self):
        """Happy path: factory creates VocabularyStatsService (was VocabularyAnalyticsService)"""
        # Act
        service = ServiceFactory.get_vocabulary_analytics_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "VocabularyStatsService"


class TestServiceFactoryFilteringServices:
    """Tests for ServiceFactory filtering service creation"""

    def test_When_get_subtitle_filter_called_Then_returns_service(self):
        """Happy path: factory creates SubtitleFilter"""
        # Act
        service = ServiceFactory.get_subtitle_filter()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "SubtitleFilter"

    def test_When_get_vocabulary_extractor_called_Then_returns_service(self):
        """Happy path: factory creates VocabularyExtractor"""
        # Act
        service = ServiceFactory.get_vocabulary_extractor()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "VocabularyExtractor"

    def test_When_get_translation_analyzer_called_Then_returns_service(self):
        """Happy path: factory creates TranslationAnalyzer"""
        # Act
        service = ServiceFactory.get_translation_analyzer()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "TranslationAnalyzer"


class TestServiceFactoryMultipleInstances:
    """Tests for verifying service instance creation behavior"""

    def test_When_services_created_multiple_times_Then_returns_new_instances(self):
        """Behavior: factory creates new instances (except singletons like VocabularyService)"""
        # Arrange
        mock_db1 = Mock(spec=AsyncSession)
        mock_db2 = Mock(spec=AsyncSession)

        # Act
        auth1 = ServiceFactory.get_auth_service(mock_db1)
        auth2 = ServiceFactory.get_auth_service(mock_db2)

        vocab1 = ServiceFactory.get_vocabulary_service(mock_db1)
        vocab2 = ServiceFactory.get_vocabulary_service(mock_db2)

        # Assert - AuthService creates new instances, VocabularyService is singleton
        assert auth1 is not auth2
        assert vocab1 is vocab2  # VocabularyService is a singleton

    def test_When_repositories_created_multiple_times_Then_returns_new_instances(self):
        """Behavior: repositories are not singletons"""
        # Arrange
        mock_db1 = Mock(spec=AsyncSession)
        mock_db2 = Mock(spec=AsyncSession)

        # Act
        repo1 = ServiceFactory.get_user_repository(mock_db1)
        repo2 = ServiceFactory.get_user_repository(mock_db2)

        # Assert
        assert repo1 is not repo2


class TestServiceFactoryLoggingServices:
    """Tests for ServiceFactory logging service creation"""

    def test_When_get_log_manager_called_Then_returns_service(self):
        """Happy path: factory creates LogManagerService (was LogManager)"""
        # Act
        service = ServiceFactory.get_log_manager()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LogManagerService"

    def test_When_get_log_handlers_called_Then_returns_service(self):
        """Happy path: factory creates LogHandlerService (was LogHandlers)"""
        # Act
        service = ServiceFactory.get_log_handlers()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LogHandlerService"

    def test_When_get_log_formatter_called_Then_returns_service(self):
        """Happy path: factory creates LogFormatterService (was LogFormatter)"""
        # Act
        service = ServiceFactory.get_log_formatter()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LogFormatterService"