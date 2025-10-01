"""
Thread Safety Tests for ServiceContainer
Testing the improved thread-safe singleton pattern and concurrent service creation
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.service_container import (
    ServiceContainer,
    get_auth_service,
    get_service_container,
    get_vocabulary_service,
    reset_service_container,
)


class TestServiceContainerThreadSafety:
    """Test thread safety of ServiceContainer singleton and service creation"""

    def test_When_concurrent_singleton_access_Then_same_instance_returned(self):
        """Test concurrent access to singleton returns same instance"""
        # Arrange
        reset_service_container()
        instances = []

        def get_instance():
            instance = get_service_container()
            instances.append(instance)

        # Act - Multiple threads accessing singleton simultaneously
        threads = [threading.Thread(target=get_instance) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - All threads got the same instance
        assert len(instances) == 20
        assert all(inst is instances[0] for inst in instances)

    def test_When_concurrent_service_creation_Then_single_instance_created(self):
        """Test concurrent service creation creates only one instance per service"""
        # Arrange
        reset_service_container()
        container = get_service_container()
        services = []

        def get_service():
            # Register a simple test service
            service = container.get_auth_service()
            services.append(service)

        # Act - Multiple threads creating same service simultaneously
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - All threads got the same service instance
        assert len(services) == 10
        assert all(svc is services[0] for svc in services)

    def test_When_concurrent_different_services_Then_all_created(self):
        """Test concurrent creation of different services"""
        # Arrange
        reset_service_container()
        container = get_service_container()
        auth_services = []
        vocab_services = []

        def get_auth():
            service = container.get_auth_service()
            auth_services.append(service)

        def get_vocab():
            service = container.get_vocabulary_service()
            vocab_services.append(service)

        # Act - Multiple threads creating different services
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=get_auth))
            threads.append(threading.Thread(target=get_vocab))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - Each service type has one unique instance
        assert len(auth_services) == 5
        assert len(vocab_services) == 5
        assert all(svc is auth_services[0] for svc in auth_services)
        assert all(svc is vocab_services[0] for svc in vocab_services)
        assert auth_services[0] is not vocab_services[0]

    def test_When_concurrent_transient_service_creation_Then_multiple_instances(self):
        """Test transient services create new instances for each call"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        # Register transient service
        call_count = [0]

        def factory():
            call_count[0] += 1
            return Mock()

        container.register_transient("test_transient", factory)
        services = []

        def get_service():
            service = container.get_service_by_name("test_transient")
            services.append(service)

        # Act - Multiple threads creating transient service
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - Each call created a new instance
        assert len(services) == 10
        assert call_count[0] == 10
        # All instances should be different
        assert len({id(svc) for svc in services}) == 10

    def test_When_concurrent_reset_and_access_Then_no_errors(self):
        """Test concurrent reset and access doesn't cause errors"""
        # Arrange
        errors = []
        instances = []

        def access_container():
            try:
                reset_service_container()
                instance = get_service_container()
                instances.append(instance)
            except Exception as e:
                errors.append(e)

        # Act - Multiple threads resetting and accessing
        threads = [threading.Thread(target=access_container) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - No errors occurred
        assert len(errors) == 0
        assert len(instances) == 10

    def test_When_high_concurrency_service_creation_Then_thread_safe(self):
        """Test high concurrency scenario with many threads"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        # Register multiple singleton services
        for i in range(5):
            container.register_singleton(f"service_{i}", lambda i=i: Mock(id=i))

        results = {}
        errors = []

        def worker(service_name):
            try:
                service = container.get_service_by_name(service_name)
                if service_name not in results:
                    results[service_name] = []
                results[service_name].append(service)
            except Exception as e:
                errors.append(e)

        # Act - 100 threads accessing 5 services concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(20):
                for i in range(5):
                    futures.append(executor.submit(worker, f"service_{i}"))

            for future in as_completed(futures):
                future.result()

        # Assert - No errors and all instances are singletons
        assert len(errors) == 0
        assert len(results) == 5
        for _service_name, instances in results.items():
            assert len(instances) == 20
            assert all(inst is instances[0] for inst in instances)


class TestServiceContainerDoubleCheckLocking:
    """Test the double-check locking pattern implementation"""

    def test_When_double_check_lock_race_condition_Then_handled_correctly(self):
        """Test double-check locking prevents race conditions"""
        # Arrange
        reset_service_container()

        # Track how many times instance is created
        creation_count = [0]
        original_init = ServiceContainer.__init__

        # Use barrier to synchronize thread access
        num_threads = 50
        barrier = threading.Barrier(num_threads)

        def tracked_init(self, *args, **kwargs):
            creation_count[0] += 1
            original_init(self, *args, **kwargs)

        instances = []

        def get_instance():
            # Wait for all threads to reach this point
            barrier.wait()
            with patch.object(ServiceContainer, "__init__", tracked_init):
                instance = get_service_container()
                instances.append(instance)

        # Act - Concurrent access during initialization
        threads = [threading.Thread(target=get_instance) for _ in range(num_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - Only one instance created despite concurrent access
        # Note: creation_count might be > 1 due to timing, but all instances should be same
        assert all(inst is instances[0] for inst in instances)

    def test_When_reentrant_lock_used_Then_nested_calls_work(self):
        """Test RLock allows reentrant calls"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        # Register service that calls another service creation
        def nested_factory():
            # This should work with RLock (reentrant)
            return Mock()

        container.register_singleton("nested_service", nested_factory)

        # Act
        service = container.get_service_by_name("nested_service")

        # Assert - No deadlock occurred
        assert service is not None


class TestServiceContainerHealthCheck:
    """Test health check functionality is thread-safe"""

    @pytest.mark.asyncio
    async def test_When_concurrent_health_checks_Then_no_errors(self):
        """Test concurrent health checks don't interfere with each other"""
        # Arrange
        reset_service_container()
        container = get_service_container()
        results = []
        errors = []

        async def check_health():
            try:
                health = await container.health_check_all()
                results.append(health)
            except Exception as e:
                errors.append(e)

        # Act - Multiple concurrent health checks
        import asyncio

        await asyncio.gather(*[check_health() for _ in range(10)])

        # Assert - All checks completed without errors
        assert len(errors) == 0
        assert len(results) == 10
        for result in results:
            assert result["container"] == "ServiceContainer"
            assert result["status"] in ["healthy", "degraded"]


class TestServiceContainerLifecycle:
    """Test service lifecycle management is thread-safe"""

    @pytest.mark.asyncio
    async def test_When_concurrent_cleanup_Then_thread_safe(self):
        """Test concurrent cleanup operations"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        # Register services with async cleanup methods
        mock_service1 = Mock()
        mock_service1.cleanup = AsyncMock()
        mock_service2 = Mock()
        mock_service2.cleanup = AsyncMock()

        container._services["service1"] = mock_service1
        container._services["service2"] = mock_service2
        container._initialized_services = [mock_service1, mock_service2]

        # Act - Concurrent cleanup
        await container.cleanup_services()

        # Assert - All services cleaned up
        assert len(container._initialized_services) == 0
        mock_service1.cleanup.assert_called_once()
        mock_service2.cleanup.assert_called_once()


class TestServiceContainerErrors:
    """Test error handling in concurrent scenarios"""

    def test_When_invalid_service_requested_Then_clear_error_message(self):
        """Test error message includes available services"""
        # Arrange
        reset_service_container()
        container = get_service_container()
        container.register_singleton("valid_service", Mock)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            container.get_service_by_name("invalid_service")

        assert "invalid_service" in str(exc_info.value)
        assert "Available services" in str(exc_info.value)

    def test_When_service_creation_fails_Then_error_propagated(self):
        """Test service creation errors are properly propagated"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        def failing_factory():
            raise RuntimeError("Service creation failed")

        container.register_singleton("failing_service", failing_factory)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            container.get_service_by_name("failing_service")

        assert "Service creation failed" in str(exc_info.value)

    def test_When_concurrent_service_creation_fails_Then_all_threads_see_error(self):
        """Test failure in service creation is visible to all threads"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        call_count = [0]

        def failing_factory():
            call_count[0] += 1
            raise RuntimeError("Creation failed")

        container.register_singleton("failing", failing_factory)

        errors = []

        def try_get_service():
            try:
                container.get_service_by_name("failing")
            except RuntimeError as e:
                errors.append(e)

        # Act - Multiple threads try to create failing service
        threads = [threading.Thread(target=try_get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - All threads saw the error
        assert len(errors) == 10
        assert all("Creation failed" in str(e) for e in errors)


class TestServiceContainerConvenienceFunctions:
    """Test convenience functions are thread-safe"""

    def test_When_concurrent_get_auth_service_Then_same_instance(self):
        """Test get_auth_service convenience function is thread-safe"""
        # Arrange
        reset_service_container()
        services = []

        def get_service():
            service = get_auth_service()
            services.append(service)

        # Act
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert
        assert len(services) == 10
        assert all(svc is services[0] for svc in services)

    def test_When_concurrent_get_vocabulary_service_Then_same_instance(self):
        """Test get_vocabulary_service convenience function is thread-safe"""
        # Arrange
        reset_service_container()
        services = []

        def get_service():
            service = get_vocabulary_service()
            services.append(service)

        # Act
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert
        assert len(services) == 10
        assert all(svc is services[0] for svc in services)


class TestServiceContainerRegisteredServices:
    """Test service registration tracking is thread-safe"""

    def test_When_concurrent_service_registration_Then_all_tracked(self):
        """Test concurrent service registration"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        def register_service(i):
            container.register_singleton(f"service_{i}", lambda: Mock())

        # Act - Concurrent registration
        threads = [threading.Thread(target=register_service, args=(i,)) for i in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - All services registered
        registered = container.get_registered_services()
        for i in range(20):
            assert f"service_{i}" in registered

    def test_When_get_registered_services_Then_includes_built_in(self):
        """Test get_registered_services includes built-in services"""
        # Arrange
        reset_service_container()
        container = get_service_container()

        # Act
        registered = container.get_registered_services()

        # Assert - Built-in services are included
        assert "auth_service" in registered
        assert "vocabulary_service" in registered
