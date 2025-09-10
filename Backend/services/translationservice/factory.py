"""
Translation Service Factory
Creates and manages translation service instances
"""

from typing import Dict, Type
from .interface import ITranslationService
from .nllb_implementation import NLLBTranslationService


class TranslationServiceFactory:
    """
    Factory for creating translation service instances
    Manages service registration and instantiation
    """
    
    # Registry of available translation services
    _services: Dict[str, Type[ITranslationService]] = {
        "nllb": NLLBTranslationService,
        "nllb-200": NLLBTranslationService,
    }
    
    # Cache of instantiated services
    _instances: Dict[str, ITranslationService] = {}
    
    @classmethod
    def register_service(
        cls,
        name: str,
        service_class: Type[ITranslationService]
    ) -> None:
        """
        Register a new translation service
        
        Args:
            name: Name to register the service under
            service_class: Class implementing ITranslationService
        """
        if not issubclass(service_class, ITranslationService):
            raise ValueError(f"{service_class} must implement ITranslationService")
        
        cls._services[name.lower()] = service_class
    
    @classmethod
    def create_service(
        cls,
        service_name: str = "nllb",
        **kwargs
    ) -> ITranslationService:
        """
        Create a translation service instance
        
        Args:
            service_name: Name of the service to create
            **kwargs: Additional arguments to pass to the service constructor
            
        Returns:
            Instance of the requested translation service
            
        Raises:
            ValueError: If service_name is not registered
        """
        service_name = service_name.lower()
        
        if service_name not in cls._services:
            available = ", ".join(cls._services.keys())
            raise ValueError(
                f"Unknown translation service: {service_name}. "
                f"Available services: {available}"
            )
        
        # Check if we already have an instance
        cache_key = f"{service_name}_{str(kwargs)}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Create new instance
        service_class = cls._services[service_name]
        instance = service_class(**kwargs)
        
        # Cache the instance
        cls._instances[cache_key] = instance
        
        return instance
    
    @classmethod
    def get_available_services(cls) -> Dict[str, str]:
        """
        Get dictionary of available services
        
        Returns:
            Dictionary mapping service names to descriptions
        """
        services = {}
        for name, service_class in cls._services.items():
            # Create temporary instance to get service name
            temp_instance = service_class()
            services[name] = temp_instance.service_name
            # Don't keep the temporary instance
            del temp_instance
        
        return services
    
    @classmethod
    def cleanup_all(cls) -> None:
        """Clean up all cached service instances"""
        for instance in cls._instances.values():
            instance.cleanup()
        
        cls._instances.clear()


# Convenience function for quick service creation
def get_translation_service(
    name: str = "nllb",
    **kwargs
) -> ITranslationService:
    """
    Get a translation service instance
    
    Args:
        name: Name of the service
        **kwargs: Service-specific configuration
        
    Returns:
        Translation service instance
    """
    return TranslationServiceFactory.create_service(name, **kwargs)