"""
Transcription Service Factory
Creates and manages transcription service instances
"""

from typing import Dict, Type, Optional
from .interface import ITranscriptionService
from .whisper_implementation import WhisperTranscriptionService
from .parakeet_implementation import ParakeetTranscriptionService


class TranscriptionServiceFactory:
    """
    Factory for creating transcription service instances
    Manages service registration and instantiation
    """
    
    # Registry of available transcription services
    _services: Dict[str, Type[ITranscriptionService]] = {
        "whisper": WhisperTranscriptionService,
        "whisper-tiny": WhisperTranscriptionService,
        "whisper-base": WhisperTranscriptionService,
        "whisper-small": WhisperTranscriptionService,
        "whisper-medium": WhisperTranscriptionService,
        "whisper-large": WhisperTranscriptionService,
        "parakeet": ParakeetTranscriptionService,
        "parakeet-tdt-1.1b": ParakeetTranscriptionService,
        "parakeet-ctc-1.1b": ParakeetTranscriptionService,
        "parakeet-ctc-0.6b": ParakeetTranscriptionService,
        "parakeet-tdt-0.6b": ParakeetTranscriptionService,
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
    _instances: Dict[str, ITranscriptionService] = {}
    
    @classmethod
    def register_service(
        cls,
        name: str,
        service_class: Type[ITranscriptionService],
        default_config: Optional[Dict] = None
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
    def create_service(
        cls,
        service_name: str = "whisper",
        **kwargs
    ) -> ITranscriptionService:
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
        
        # Determine the service class
        if service_name.startswith("whisper"):
            service_class = WhisperTranscriptionService
        elif service_name.startswith("parakeet"):
            service_class = ParakeetTranscriptionService
        elif service_name in cls._services:
            service_class = cls._services[service_name]
        else:
            available = ", ".join(cls._services.keys())
            raise ValueError(
                f"Unknown transcription service: {service_name}. "
                f"Available services: {available}"
            )
        
        # Merge default config with provided kwargs
        if service_name in cls._default_configs:
            config = cls._default_configs[service_name].copy()
            config.update(kwargs)
        else:
            config = kwargs
        
        # Check if we already have an instance
        cache_key = f"{service_name}_{str(config)}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Create new instance
        instance = service_class(**config)
        
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
def get_transcription_service(
    name: str = "whisper",
    **kwargs
) -> ITranscriptionService:
    """
    Get a transcription service instance
    
    Args:
        name: Name of the service
        **kwargs: Service-specific configuration
        
    Returns:
        Transcription service instance
    """
    return TranscriptionServiceFactory.create_service(name, **kwargs)