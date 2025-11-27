"""
Translation Service Factory
Creates and manages translation service instances with lazy imports to avoid
pulling heavy ML dependencies at import time.

WHY THIS FACTORY PATTERN IS NECESSARY (Not a YAGNI violation):

1. **Multiple Active Implementations**:
   - NLLB (Meta) - Multilingual, 5 variants (600M-54B params)
   - OPUS-MT (Helsinki-NLP) - Language-pair specific, fast
   - Selection via environment variable: LANGPLUG_TRANSLATION_SERVICE

2. **Lazy Loading Required**:
   - Translation models are 500MB-20GB in size
   - Import time would be 10-60 seconds if loaded at module import
   - Factory defers import until first use

3. **Instance Caching**:
   - Models take 10-30 seconds to load into memory
   - Caching prevents reloading on every request
   - Critical performance improvement (30s → 0.2s per request)

4. **Language Pair Optimization**:
   - Test: opus-de-es (245MB, fast)
   - Production: nllb-distilled-600m (multilingual support)
   - Configuration via env var, not code changes

DO NOT simplify to direct instantiation without addressing these requirements.
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
        # OPUS-MT CTranslate2 - 37x faster, 75% less memory (RECOMMENDED)
        "opus": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-ct2": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-de-en": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-de-es": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-de-es-big": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-es-de": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-en-es": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-en-es-big": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-es-en": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-en-zh": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-zh-en": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-de-fr": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        "opus-fr-de": "services.translationservice.opus_ct2_implementation.OpusCT2TranslationService",
        # OPUS-MT standard Transformers (fallback)
        "opus-hf": "services.translationservice.opus_implementation.OpusTranslationService",
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
        # OPUS-MT CTranslate2 configurations (37x faster)
        "opus": {"model_name": "Helsinki-NLP/opus-mt-de-en"},
        "opus-ct2": {"model_name": "Helsinki-NLP/opus-mt-de-en"},
        "opus-de-en": {"model_name": "Helsinki-NLP/opus-mt-de-en"},
        "opus-de-es": {"model_name": "Helsinki-NLP/opus-mt-de-es"},
        "opus-de-es-big": {"model_name": "Helsinki-NLP/opus-mt-tc-big-de-es"},
        "opus-es-de": {"model_name": "Helsinki-NLP/opus-mt-es-de"},
        "opus-en-es": {"model_name": "Helsinki-NLP/opus-mt-en-es"},
        "opus-en-es-big": {"model_name": "Helsinki-NLP/opus-mt-tc-big-en-es"},
        "opus-es-en": {"model_name": "Helsinki-NLP/opus-mt-es-en"},
        "opus-en-zh": {"model_name": "Helsinki-NLP/opus-mt-en-zh"},
        "opus-zh-en": {"model_name": "Helsinki-NLP/opus-mt-zh-en"},
        "opus-de-fr": {"model_name": "Helsinki-NLP/opus-mt-de-fr"},
        "opus-fr-de": {"model_name": "Helsinki-NLP/opus-mt-fr-de"},
        # OPUS-MT Transformers fallback
        "opus-hf": {"model_name": "Helsinki-NLP/opus-mt-de-en"},
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
            # OPUS-MT CTranslate2 - 37x faster on GPU, 75% less memory
            "opus": "OPUS-CT2 - CTranslate2 optimized, 37x faster",
            "opus-ct2": "OPUS-CT2 - CTranslate2 optimized, 37x faster",
            "opus-de-en": "OPUS-CT2 DE-EN - German to English",
            "opus-de-es": "OPUS-CT2 DE-ES - German to Spanish",
            "opus-de-es-big": "OPUS-CT2 DE-ES Big - High quality German to Spanish",
            "opus-es-de": "OPUS-CT2 ES-DE - Spanish to German",
            "opus-en-es": "OPUS-CT2 EN-ES - English to Spanish",
            "opus-en-es-big": "OPUS-CT2 EN-ES Big - High quality English to Spanish",
            "opus-es-en": "OPUS-CT2 ES-EN - Spanish to English",
            "opus-en-zh": "OPUS-CT2 EN-ZH - English to Chinese",
            "opus-zh-en": "OPUS-CT2 ZH-EN - Chinese to English",
            "opus-de-fr": "OPUS-CT2 DE-FR - German to French",
            "opus-fr-de": "OPUS-CT2 FR-DE - French to German",
            # OPUS-MT Transformers fallback
            "opus-hf": "OPUS-MT HuggingFace - Standard Transformers (slower)",
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
