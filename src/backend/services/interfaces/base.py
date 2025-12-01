"""
Base service interfaces for the LangPlug application.
Provides common patterns and base classes for all services.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from core.config.logging_config import get_logger

T = TypeVar("T")


class IService(ABC):
    """Base interface for all services with standard patterns"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the service"""
        pass

    def get_service_name(self) -> str:
        """Get the service name for identification"""
        return self.__class__.__name__

    def get_service_metadata(self) -> dict[str, Any]:
        """Get service metadata for monitoring and diagnostics"""
        return {
            "service": self.get_service_name(),
            "module": self.__class__.__module__,
            "version": getattr(self, "__version__", "1.0.0"),
        }


class IAsyncService(IService):
    """Base interface for services that require async operations"""

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._dependencies: list[IService] = []

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass

    async def ensure_initialized(self) -> None:
        """Ensure service is initialized before use"""
        if not self._initialized:
            await self.initialize()
            self._initialized = True
            self.logger.info("Service initialized", service=self.get_service_name())

    def add_dependency(self, service: "IService") -> None:
        """Add a service dependency for lifecycle management"""
        if service not in self._dependencies:
            self._dependencies.append(service)

    async def initialize_dependencies(self) -> None:
        """Initialize all service dependencies"""
        for dependency in self._dependencies:
            if isinstance(dependency, IAsyncService):
                await dependency.ensure_initialized()

    async def cleanup_dependencies(self) -> None:
        """Cleanup all service dependencies"""
        for dependency in reversed(self._dependencies):
            if isinstance(dependency, IAsyncService):
                try:
                    await dependency.cleanup()
                except Exception as e:
                    self.logger.error(
                        "Error cleaning up dependency", service=dependency.get_service_name(), error=str(e)
                    )

    async def health_check(self) -> dict[str, Any]:
        """Enhanced health check with dependency status"""
        base_health = {
            "service": self.get_service_name(),
            "status": "healthy" if self._initialized else "not_initialized",
            "dependencies": [],
        }

        for dependency in self._dependencies:
            try:
                dep_health = await dependency.health_check()
                base_health["dependencies"].append(dep_health)
            except Exception as e:
                base_health["dependencies"].append(
                    {"service": dependency.get_service_name(), "status": "error", "error": str(e)}
                )

        return base_health


class IRepositoryService(IAsyncService, Generic[T]):
    """Base interface for services that work with repositories"""

    @abstractmethod
    async def get_by_id(self, db: AsyncSession, id: Any) -> T | None:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def create(self, db: AsyncSession, **kwargs) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, id: Any, **kwargs) -> T:
        """Update existing entity"""
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, id: Any) -> bool:
        """Delete entity by ID"""
        pass


class ServiceError(Exception):
    """Base exception for service layer errors"""

    def __init__(self, message: str, service_name: str | None = None):
        self.message = message
        self.service_name = service_name
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Raised when service validation fails"""

    pass


class NotFoundError(ServiceError):
    """Raised when requested entity is not found"""

    pass


class PermissionError(ServiceError):
    """Raised when user lacks required permissions"""

    pass
