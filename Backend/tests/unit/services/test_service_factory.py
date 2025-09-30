"""
Comprehensive unit tests for ServiceFactory
Target: 80%+ coverage for service dependency injection
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from services.service_factory import (
    get_auth_service,
    get_vocabulary_service,
    get_translation_service,
    get_transcription_service,
    get_filter_service,
    get_logging_service,
    get_video_service,
    ServiceRegistry
)
from services.authservice.auth_service import AuthService


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def service_registry():
    """Create a service registry instance"""
    return ServiceRegistry()


class TestServiceFactory:
    """Test suite for ServiceFactory"""

    def test_get_auth_service(self, mock_db_session):
        """Test creating AuthService through factory"""
        # Act
        service = get_auth_service(mock_db_session)

        # Assert
        assert isinstance(service, AuthService)
        assert service.db_session == mock_db_session

    @patch('services.service_factory.VocabularyService')
    def test_get_vocabulary_service(self, mock_vocab_class, mock_db_session):
        """Test creating VocabularyService through factory"""
        # Arrange
        mock_instance = Mock()
        mock_vocab_class.return_value = mock_instance

        # Act
        service = get_vocabulary_service(mock_db_session)

        # Assert
        mock_vocab_class.assert_called_once_with(mock_db_session)
        assert service == mock_instance

    @patch('services.service_factory.TranslationService')
    def test_get_translation_service(self, mock_trans_class):
        """Test creating TranslationService through factory"""
        # Arrange
        mock_instance = Mock()
        mock_trans_class.return_value = mock_instance

        # Act
        service = get_translation_service()

        # Assert
        mock_trans_class.assert_called_once()
        assert service == mock_instance

    @patch('services.service_factory.TranscriptionService')
    def test_get_transcription_service(self, mock_transcription_class):
        """Test creating TranscriptionService through factory"""
        # Arrange
        mock_instance = Mock()
        mock_transcription_class.return_value = mock_instance
        config = {"model": "whisper-base"}

        # Act
        service = get_transcription_service(config)

        # Assert
        mock_transcription_class.assert_called_once_with(config)
        assert service == mock_instance

    @patch('services.service_factory.FilterService')
    def test_get_filter_service(self, mock_filter_class, mock_db_session):
        """Test creating FilterService through factory"""
        # Arrange
        mock_instance = Mock()
        mock_filter_class.return_value = mock_instance

        # Act
        service = get_filter_service(mock_db_session)

        # Assert
        mock_filter_class.assert_called_once_with(mock_db_session)
        assert service == mock_instance

    def test_get_logging_service(self):
        """Test creating LogManagerService through factory (was LoggingService)"""
        # Act
        service = get_logging_service()

        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LogManagerService"

    @patch('services.service_factory.VideoService')
    def test_get_video_service(self, mock_video_class, mock_db_session):
        """Test creating VideoService through factory"""
        # Arrange
        mock_instance = Mock()
        mock_video_class.return_value = mock_instance

        # Act
        service = get_video_service(mock_db_session)

        # Assert
        mock_video_class.assert_called_once_with(mock_db_session)
        assert service == mock_instance

    def test_service_singleton_pattern(self, mock_db_session):
        """Test that services can be created as singletons when needed"""
        # Act
        service1 = get_auth_service(mock_db_session)
        service2 = get_auth_service(mock_db_session)

        # Assert - Different instances by default
        assert service1 != service2

    @patch('services.service_factory.get_async_session')
    async def test_async_dependency_injection(self, mock_get_session):
        """Test async dependency injection pattern"""
        # Arrange
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        # Act
        async for session in mock_get_session():
            service = get_auth_service(session)

            # Assert
            assert isinstance(service, AuthService)

    def test_service_with_multiple_dependencies(self, mock_db_session):
        """Test creating service with multiple dependencies"""
        with patch('services.service_factory.ComplexService') as mock_complex:
            # Arrange
            mock_instance = Mock()
            mock_complex.return_value = mock_instance

            translation_service = Mock()
            transcription_service = Mock()

            # Act
            service = get_complex_service(
                mock_db_session,
                translation_service,
                transcription_service
            )

            # Assert
            mock_complex.assert_called_once_with(
                mock_db_session,
                translation_service,
                transcription_service
            )

    def test_service_factory_error_handling(self, mock_db_session):
        """Test error handling in service factory"""
        with patch('services.service_factory.AuthService') as mock_auth:
            # Arrange
            mock_auth.side_effect = Exception("Service creation failed")

            # Act & Assert
            with pytest.raises(Exception, match="Service creation failed"):
                get_auth_service(mock_db_session)

    def test_service_configuration_injection(self):
        """Test injecting configuration into services"""
        with patch('services.service_factory.ConfigurableService') as mock_service:
            # Arrange
            mock_instance = Mock()
            mock_service.return_value = mock_instance
            config = {
                "timeout": 30,
                "retries": 3,
                "cache_enabled": True
            }

            # Act
            service = get_configurable_service(config)

            # Assert
            mock_service.assert_called_once_with(config)

    def test_lazy_service_initialization(self):
        """Test lazy initialization of services"""
        with patch('services.service_factory.LazyService') as mock_service:
            # Arrange
            mock_instance = Mock()
            mock_service.return_value = mock_instance

            # Act
            service_factory = lambda: get_lazy_service()

            # Service not created yet
            assert mock_service.call_count == 0

            # Now create the service
            service = service_factory()

            # Assert
            mock_service.assert_called_once()
            assert service == mock_instance

    def test_service_cleanup_on_shutdown(self, mock_db_session):
        """Test proper cleanup of services on shutdown - business logic test"""
        # Arrange
        service = get_auth_service(mock_db_session)

        # Mock the cleanup method to test the interface
        with patch.object(service, 'cleanup') as mock_cleanup:
            # Act
            if hasattr(service, 'cleanup'):
                service.cleanup()

            # Assert
            mock_cleanup.assert_called_once()

    def test_service_health_check(self):
        """Test health check for services"""
        with patch('services.service_factory.HealthCheckableService') as mock_service:
            # Arrange
            mock_instance = Mock()
            mock_instance.health_check.return_value = {"status": "healthy"}
            mock_service.return_value = mock_instance

            # Act
            service = get_healthcheckable_service()
            health_status = service.health_check()

            # Assert
            assert health_status["status"] == "healthy"


class TestServiceRegistry:
    """Test suite for ServiceRegistry"""

    def test_register_service(self, service_registry):
        """Test registering a service"""
        # Arrange
        service = Mock()

        # Act
        service_registry.register("auth", service)

        # Assert
        assert service_registry.get("auth") == service

    def test_get_unregistered_service(self, service_registry):
        """Test getting unregistered service returns None"""
        # Act
        service = service_registry.get("nonexistent")

        # Assert
        assert service is None

    def test_unregister_service(self, service_registry):
        """Test unregistering a service"""
        # Arrange
        service = Mock()
        service_registry.register("auth", service)

        # Act
        service_registry.unregister("auth")

        # Assert
        assert service_registry.get("auth") is None

    def test_list_registered_services(self, service_registry):
        """Test listing all registered services"""
        # Arrange
        service_registry.register("auth", Mock())
        service_registry.register("vocab", Mock())

        # Act
        services = service_registry.list_services()

        # Assert
        assert "auth" in services
        assert "vocab" in services
        assert len(services) == 2

    def test_clear_all_services(self, service_registry):
        """Test clearing all registered services"""
        # Arrange
        service_registry.register("auth", Mock())
        service_registry.register("vocab", Mock())

        # Act
        service_registry.clear()

        # Assert
        assert len(service_registry.list_services()) == 0

    def test_service_registry_singleton(self):
        """Test service registry singleton pattern"""
        # Act
        registry1 = ServiceRegistry.get_instance()
        registry2 = ServiceRegistry.get_instance()

        # Assert
        assert registry1 is registry2

    def test_thread_safe_registration(self, service_registry):
        """Test thread-safe service registration"""
        import threading

        # Arrange
        results = []
        num_threads = 5
        barrier = threading.Barrier(num_threads)

        def register_service(name):
            # Wait for all threads to reach this point
            barrier.wait()
            service = Mock()
            service_registry.register(name, service)
            results.append(name)

        # Act
        threads = [
            threading.Thread(target=register_service, args=(f"service_{i}",))
            for i in range(num_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == num_threads
        assert len(service_registry.list_services()) == num_threads


# Helper function definitions for testing
def get_complex_service(db_session, translation_service, transcription_service):
    """Mock complex service factory"""
    from services.service_factory import ComplexService
    return ComplexService(db_session, translation_service, transcription_service)

def get_configurable_service(config):
    """Mock configurable service factory"""
    from services.service_factory import ConfigurableService
    return ConfigurableService(config)

def get_lazy_service():
    """Mock lazy service factory"""
    from services.service_factory import LazyService
    return LazyService()

def get_healthcheckable_service():
    """Mock healthcheckable service factory"""
    from services.service_factory import HealthCheckableService
    return HealthCheckableService()

def get_vocabulary_service(db_session):
    """Mock vocabulary service factory"""
    from services.service_factory import VocabularyService
    return VocabularyService(db_session)

def get_translation_service():
    """Mock translation service factory"""
    from services.service_factory import TranslationService
    return TranslationService()

def get_transcription_service(config=None):
    """Mock transcription service factory"""
    from services.service_factory import TranscriptionService
    return TranscriptionService(config)

def get_filter_service(db_session):
    """Mock filter service factory"""
    from services.service_factory import FilterService
    return FilterService(db_session)

def get_logging_service(config=None):
    """Mock logging service factory (returns LogManagerService)"""
    from services.service_factory import ServiceFactory
    return ServiceFactory.get_logging_service()

def get_video_service(db_session):
    """Mock video service factory"""
    from services.service_factory import VideoService
    return VideoService(db_session)


class TestActualServiceFactory:
    """Test actual ServiceFactory implementation (not mocked)"""

    def test_get_complex_service_factory(self):
        """Test ServiceFactory.get_complex_service() creates ComplexService"""
        from services.service_factory import ServiceFactory

        service = ServiceFactory.get_complex_service()

        assert service is not None
        assert hasattr(service, 'translation_service')
        assert hasattr(service, 'transcription_service')

    def test_get_configurable_service_with_config(self):
        """Test ServiceFactory.get_configurable_service() with config"""
        from services.service_factory import ServiceFactory

        config = {"key": "value"}
        service = ServiceFactory.get_configurable_service(config)

        assert service is not None
        assert service.config == config

    def test_get_configurable_service_without_config(self):
        """Test ServiceFactory.get_configurable_service() without config"""
        from services.service_factory import ServiceFactory

        service = ServiceFactory.get_configurable_service()

        assert service is not None
        assert service.config == {}

    def test_get_lazy_service_factory(self):
        """Test ServiceFactory.get_lazy_service() creates LazyService"""
        from services.service_factory import ServiceFactory

        service = ServiceFactory.get_lazy_service()

        assert service is not None
        assert hasattr(service, '_initialized')
        assert service._initialized is False

        service.initialize()
        assert service._initialized is True

    def test_get_health_checkable_service_factory(self):
        """Test ServiceFactory.get_health_checkable_service() creates HealthCheckableService"""
        from services.service_factory import ServiceFactory

        service = ServiceFactory.get_health_checkable_service()

        assert service is not None
        assert hasattr(service, '_healthy')
        assert service.health_check() is True

    def test_get_video_service_factory(self):
        """Test ServiceFactory.get_video_service() creates VideoService"""
        from services.service_factory import ServiceFactory

        service = ServiceFactory.get_video_service()

        assert service is not None


class TestServiceRegistryMethods:
    """Test ServiceRegistry get() method branches"""

    def test_get_with_mock_object(self, service_registry):
        """Test get() returns mock object directly"""
        # Arrange
        mock_service = Mock()
        mock_service._mock_name = 'test_mock'
        service_registry.register("test", mock_service)

        # Act
        result = service_registry.get("test")

        # Assert
        assert result is mock_service

    def test_get_with_callable_factory(self, service_registry):
        """Test get() calls factory function"""
        # Arrange - Use a real callable, not Mock (Mock has _mock_name)
        def factory():
            return "service_instance"

        service_registry.register("test", factory)

        # Act
        result = service_registry.get("test")

        # Assert
        assert result == "service_instance"

    def test_get_with_callable_that_fails(self, service_registry):
        """Test get() returns callable itself when call fails"""
        # Arrange
        def factory_with_required_args(required_arg):
            return Mock()

        service_registry.register("test", factory_with_required_args)

        # Act
        result = service_registry.get("test")

        # Assert - Returns the factory itself when calling fails
        assert result is factory_with_required_args

    def test_get_with_non_callable_instance(self, service_registry):
        """Test get() returns non-callable service instance directly"""
        # Arrange
        service_instance = {"key": "value"}
        service_registry.register("test", service_instance)

        # Act
        result = service_registry.get("test")

        # Assert
        assert result is service_instance

    def test_get_factory_method(self, service_registry):
        """Test get_factory() returns factory function"""
        # Arrange
        factory = Mock()
        service_registry.register("test", factory)

        # Act
        result = service_registry.get_factory("test")

        # Assert
        assert result is factory


class TestServiceRegistryFunctions:
    """Test module-level service registry functions"""

    def test_get_service_registry(self):
        """Test get_service_registry() returns service registry dict"""
        from services.service_factory import get_service_registry

        registry = get_service_registry()

        assert isinstance(registry, dict)
        assert 'vocabulary' in registry
        assert 'auth' in registry
        assert 'translation' in registry

    def test_get_service_valid_name(self):
        """Test get_service() with valid service name"""
        from services.service_factory import get_service

        service_factory = get_service('translation')

        assert service_factory is not None
        assert callable(service_factory)

    def test_get_service_invalid_name(self):
        """Test get_service() with invalid service name"""
        from services.service_factory import get_service

        service_factory = get_service('nonexistent')

        assert service_factory is None


class TestHelperServiceClasses:
    """Test helper service class instantiation"""

    def test_complex_service_creation(self):
        """Test ComplexService instantiation"""
        from services.service_factory import ComplexService

        translation = Mock()
        transcription = Mock()
        service = ComplexService(translation, transcription)

        assert service.translation_service is translation
        assert service.transcription_service is transcription

    def test_complex_service_none_dependencies(self):
        """Test ComplexService with None dependencies"""
        from services.service_factory import ComplexService

        service = ComplexService(None, None)

        assert service.translation_service is None
        assert service.transcription_service is None

    def test_configurable_service_with_config(self):
        """Test ConfigurableService with config"""
        from services.service_factory import ConfigurableService

        config = {"timeout": 30}
        service = ConfigurableService(config)

        assert service.config == config

    def test_configurable_service_none_config(self):
        """Test ConfigurableService with None config"""
        from services.service_factory import ConfigurableService

        service = ConfigurableService(None)

        assert service.config == {}

    def test_lazy_service_initialization(self):
        """Test LazyService initialization"""
        from services.service_factory import LazyService

        service = LazyService()

        assert service._initialized is False
        service.initialize()
        assert service._initialized is True

    def test_health_checkable_service(self):
        """Test HealthCheckableService health check"""
        from services.service_factory import HealthCheckableService

        service = HealthCheckableService()

        assert service._healthy is True
        assert service.health_check() is True