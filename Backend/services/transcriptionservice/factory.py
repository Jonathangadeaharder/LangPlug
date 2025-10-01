"""
Transcription Service Factory
Creates and manages transcription service instances.
Uses lazy imports to avoid importing heavy ML dependencies at module import time.
"""

from importlib import import_module

from .interface import ITranscriptionService


class TranscriptionServiceFactory:
    """
    Factory for creating transcription service instances
    Manages service registration and instantiation
    """

    # Registry of available transcription services
    _services: dict[str, str | type[ITranscriptionService]] = {
        # Lazy string paths for heavy services
        "whisper": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "whisper-tiny": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "whisper-base": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "whisper-small": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "whisper-medium": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "whisper-large": "services.transcriptionservice.whisper_implementation.WhisperTranscriptionService",
        "parakeet": "services.transcriptionservice.parakeet_implementation.ParakeetTranscriptionService",
        "parakeet-tdt-1.1b": "services.transcriptionservice.parakeet_implementation.ParakeetTranscriptionService",
        "parakeet-ctc-1.1b": "services.transcriptionservice.parakeet_implementation.ParakeetTranscriptionService",
        "parakeet-ctc-0.6b": "services.transcriptionservice.parakeet_implementation.ParakeetTranscriptionService",
        "parakeet-tdt-0.6b": "services.transcriptionservice.parakeet_implementation.ParakeetTranscriptionService",
    }

    # Default configurations for each service
    _default_configs = {
        "whisper": {"model_size": "large-v3-turbo"},
        "whisper-tiny": {"model_size": "tiny"},
        "whisper-base": {"model_size": "base"},
        "whisper-small": {"model_size": "small"},
        "whisper-medium": {"model_size": "medium"},
        "whisper-large": {"model_size": "large"},
        "whisper-large-v3-turbo": {"model_size": "large-v3-turbo"},
        "parakeet": {"model_name": "parakeet-tdt-1.1b"},
        "parakeet-tdt-1.1b": {"model_name": "parakeet-tdt-1.1b"},
        "parakeet-ctc-1.1b": {"model_name": "parakeet-ctc-1.1b"},
        "parakeet-ctc-0.6b": {"model_name": "parakeet-ctc-0.6b"},
        "parakeet-tdt-0.6b": {"model_name": "parakeet-tdt-0.6b"},
    }

    # Cache of instantiated services
    _instances: dict[str, ITranscriptionService] = {}

    @classmethod
    def register_service(
        cls, name: str, service_class: type[ITranscriptionService], default_config: dict | None = None
    ) -> None:
        """
        Register a new transcription service

        Args:
            name: Name to register the service under
            service_class: Class implementing ITranscriptionService
            default_config: Default configuration for this service
        """
        if not issubclass(service_class, ITranscriptionService):
            raise ValueError(f"{service_class} must implement ITranscriptionService")

        cls._services[name.lower()] = service_class
        if default_config:
            cls._default_configs[name.lower()] = default_config

    @classmethod
    def create_service(cls, service_name: str = "whisper", **kwargs) -> ITranscriptionService:
        """
        Create a transcription service instance

        Args:
            service_name: Name of the service to create
            **kwargs: Additional arguments to pass to the service constructor

        Returns:
            Instance of the requested transcription service

        Raises:
            ValueError: If service_name is not registered
        """
        service_name = service_name.lower()

        # Determine the service class (resolve lazily)
        if service_name in cls._services:
            cls_or_path = cls._services[service_name]
            if isinstance(cls_or_path, str):
                module_path, class_name = cls_or_path.rsplit(".", 1)
                module = import_module(module_path)
                service_class = getattr(module, class_name)
                cls._services[service_name] = service_class
            else:
                service_class = cls_or_path
        else:
            available = ", ".join(cls._services.keys())
            raise ValueError(f"Unknown transcription service: {service_name}. Available services: {available}")

        # Merge default config with provided kwargs
        if service_name in cls._default_configs:
            config = cls._default_configs[service_name].copy()
            config.update(kwargs)
        else:
            config = kwargs

        # Check if we already have an instance
        cache_key = f"{service_name}_{config!s}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # Create new instance
        instance = service_class(**config)

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
            "whisper": "OpenAI Whisper - Multi-language ASR",
            "whisper-tiny": "Whisper Tiny (39M params) - Fastest",
            "whisper-base": "Whisper Base (74M params) - Good balance",
            "whisper-small": "Whisper Small (244M params) - Better accuracy",
            "whisper-medium": "Whisper Medium (769M params) - High accuracy",
            "whisper-large": "Whisper Large (1550M params) - Best accuracy",
            "parakeet": "NVIDIA Parakeet - Fast English ASR",
            "parakeet-tdt-1.1b": "Parakeet TDT 1.1B - Transducer model",
            "parakeet-ctc-1.1b": "Parakeet CTC 1.1B - CTC model",
            "parakeet-ctc-0.6b": "Parakeet CTC 0.6B - Smaller CTC",
            "parakeet-tdt-0.6b": "Parakeet TDT 0.6B - Smaller transducer",
        }

    @classmethod
    def cleanup_all(cls) -> None:
        """Clean up all cached service instances"""
        for instance in cls._instances.values():
            instance.cleanup()

        cls._instances.clear()


# Convenience function for quick service creation
def get_transcription_service(name: str = "whisper", **kwargs) -> ITranscriptionService:
    """
    Get a transcription service instance

    Args:
        name: Name of the service
        **kwargs: Service-specific configuration

    Returns:
        Transcription service instance
    """
    return TranscriptionServiceFactory.create_service(name, **kwargs)
