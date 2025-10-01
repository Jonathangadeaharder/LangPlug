"""
Translation Service Factory
Creates and manages translation service instances with lazy imports to avoid
pulling heavy ML dependencies at import time.
"""

from importlib import import_module

from .interface import ITranslationService


class TranslationServiceFactory:
    """
    Factory for creating translation service instances
    Manages service registration and instantiation
    """

    # Registry of available translation services
    _services: dict[str, str | type[ITranslationService]] = {
        # NLLB models - heavy but high quality
        "nllb": "services.translationservice.nllb_implementation.NLLBTranslationService",
        "nllb-600m": "services.translationservice.nllb_implementation.NLLBTranslationService",
        "nllb-1.3b": "services.translationservice.nllb_implementation.NLLBTranslationService",
        "nllb-3.3b": "services.translationservice.nllb_implementation.NLLBTranslationService",
        "nllb-54b": "services.translationservice.nllb_implementation.NLLBTranslationService",
        "nllb-distilled-600m": "services.translationservice.nllb_implementation.NLLBTranslationService",
        # OPUS-MT models - fast and efficient for specific language pairs
        "opus": "services.translationservice.opus_implementation.OpusTranslationService",
        "opus-de-en": "services.translationservice.opus_implementation.OpusTranslationService",
        "opus-de-es": "services.translationservice.opus_implementation.OpusTranslationService",
        "opus-de-es-big": "services.translationservice.opus_implementation.OpusTranslationService",
    }

    # Default configurations for each service variant
    _default_configs = {
        # NLLB configurations
        "nllb": {"model_name": "facebook/nllb-200-distilled-600M"},
        "nllb-600m": {"model_name": "facebook/nllb-200-distilled-600M"},
        "nllb-1.3b": {"model_name": "facebook/nllb-200-1.3B"},
        "nllb-3.3b": {"model_name": "facebook/nllb-200-3.3B"},
        "nllb-54b": {"model_name": "facebook/nllb-moe-54b"},
        "nllb-distilled-600m": {"model_name": "facebook/nllb-200-distilled-600M"},
        # OPUS-MT configurations
        "opus": {"model_name": "Helsinki-NLP/opus-mt-de-en"},  # Fast default
        "opus-de-en": {"model_name": "Helsinki-NLP/opus-mt-de-en"},
        "opus-de-es": {"model_name": "Helsinki-NLP/opus-mt-de-es"},  # For testing
        "opus-de-es-big": {"model_name": "Helsinki-NLP/opus-mt-tc-big-de-es"},  # For production
    }

    # Cache of instantiated services
    _instances: dict[str, ITranslationService] = {}

    @classmethod
    def register_service(cls, name: str, service_class: type[ITranslationService]) -> None:
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
    def create_service(cls, service_name: str = "nllb", **kwargs) -> ITranslationService:
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
            raise ValueError(f"Unknown translation service: {service_name}. Available services: {available}")

        # Resolve class lazily if necessary
        cls_or_path = cls._services[service_name]
        if isinstance(cls_or_path, str):
            module_path, class_name = cls_or_path.rsplit(".", 1)
            module = import_module(module_path)
            service_class = getattr(module, class_name)
            # Cache resolved class to avoid repeated imports
            cls._services[service_name] = service_class
        else:
            service_class = cls_or_path

        # Merge default config with provided kwargs
        if service_name in cls._default_configs:
            config = cls._default_configs[service_name].copy()
            config.update(kwargs)
        else:
            config = kwargs

        # Filter out parameters that are not constructor arguments
        # source_lang and target_lang are used at translation time, not init time
        filtered_config = {k: v for k, v in config.items() if k not in ("source_lang", "target_lang", "quality")}

        # Check if we already have an instance
        cache_key = f"{service_name}_{filtered_config!s}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # Create new instance
        service_class = cls._services[service_name]
        instance = service_class(**filtered_config)

        # Cache the instance
        cls._instances[cache_key] = instance

        return instance

    @classmethod
    def get_available_services(cls) -> dict[str, str]:
        """
        Get dictionary of available services

        Returns:
            Dictionary mapping service names to descriptions
        """
        return {
            # NLLB models - multilingual, heavy
            "nllb": "NLLB-200 Distilled 600M - Multilingual, balanced",
            "nllb-600m": "NLLB-200 Distilled 600M - Multilingual, balanced",
            "nllb-1.3b": "NLLB-200 1.3B - Better quality, slower",
            "nllb-3.3b": "NLLB-200 3.3B - High quality, slow",
            "nllb-54b": "NLLB-MoE 54B - Highest quality, very slow",
            "nllb-distilled-600m": "NLLB-200 Distilled 600M - Fast inference",
            # OPUS-MT models - language-pair specific, fast
            "opus": "OPUS-MT DE-EN - Fast, efficient",
            "opus-de-en": "OPUS-MT DE-EN - Fast German to English",
            "opus-de-es": "OPUS-MT DE-ES - Fast German to Spanish (testing)",
            "opus-de-es-big": "OPUS-MT DE-ES Big - High quality German to Spanish (production)",
        }

    @classmethod
    def cleanup_all(cls) -> None:
        """Clean up all cached service instances"""
        for instance in cls._instances.values():
            instance.cleanup()

        cls._instances.clear()


# Convenience function for quick service creation
def get_translation_service(name: str = "nllb", **kwargs) -> ITranslationService:
    """
    Get a translation service instance

    Args:
        name: Name of the service
        **kwargs: Service-specific configuration

    Returns:
        Translation service instance
    """
    return TranslationServiceFactory.create_service(name, **kwargs)
