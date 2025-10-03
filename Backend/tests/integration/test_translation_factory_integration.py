"""
Integration tests for TranslationServiceFactory
Tests actual service instantiation with various parameter combinations
"""

import pytest

from services.translationservice.factory import TranslationServiceFactory
from services.translationservice.interface import ITranslationService

# Check if PyTorch is available
try:
    import torch  # noqa: F401

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

skip_if_no_torch = pytest.mark.skipif(
    not TORCH_AVAILABLE, reason="PyTorch not installed (required for translation models)"
)


@skip_if_no_torch
class TestTranslationFactoryParameterVariations:
    """Test factory service creation with all parameter variations"""

    def test_factory_creates_nllb_with_default_params(self):
        """Factory should create NLLB service with default parameters"""
        service = TranslationServiceFactory.create_service("nllb")

        assert service is not None
        assert isinstance(service, ITranslationService)
        assert service.model_name == "facebook/nllb-200-distilled-600M"

    def test_factory_creates_opus_with_default_params(self):
        """Factory should create OPUS service with default parameters"""
        service = TranslationServiceFactory.create_service("opus-de-es")

        assert service is not None
        assert isinstance(service, ITranslationService)
        assert "opus-mt-de-es" in service.model_name

    def test_factory_filters_source_lang_parameter(self):
        """Factory should filter out source_lang parameter - doesn't belong in __init__"""
        # This test reproduces the bug we just fixed
        service = TranslationServiceFactory.create_service("nllb", source_lang="de", target_lang="es")

        # Should succeed without TypeError
        assert service is not None
        assert isinstance(service, ITranslationService)

    def test_factory_filters_quality_parameter(self):
        """Factory should filter out quality parameter - doesn't belong in __init__"""
        service = TranslationServiceFactory.create_service(
            "opus-de-es", quality="standard", source_lang="de", target_lang="es"
        )

        # Should succeed without TypeError
        assert service is not None
        assert isinstance(service, ITranslationService)

    def test_factory_caches_instances_correctly(self):
        """Factory should cache instances with same config"""
        service1 = TranslationServiceFactory.create_service("nllb")
        service2 = TranslationServiceFactory.create_service("nllb")

        # Should return same instance
        assert service1 is service2

    def test_factory_creates_different_instances_for_different_configs(self):
        """Factory should create different instances for different configs"""
        service1 = TranslationServiceFactory.create_service("nllb")
        service2 = TranslationServiceFactory.create_service("opus-de-es")

        # Should return different instances
        assert service1 is not service2

    def test_factory_accepts_custom_model_name(self):
        """Factory should allow overriding default model_name"""
        custom_model = "facebook/nllb-200-1.3B"
        service = TranslationServiceFactory.create_service("nllb", model_name=custom_model)

        assert service.model_name == custom_model

    def test_factory_accepts_device_parameter(self):
        """Factory should pass device parameter to service"""
        service = TranslationServiceFactory.create_service("nllb", device="cpu")

        assert service.device_str == "cpu"

    def test_factory_accepts_max_length_parameter(self):
        """Factory should pass max_length parameter to service"""
        service = TranslationServiceFactory.create_service("nllb", max_length=256)

        assert service.max_length == 256

    def test_factory_raises_on_unknown_service(self):
        """Factory should raise ValueError for unknown service"""
        with pytest.raises(ValueError, match="Unknown translation service"):
            TranslationServiceFactory.create_service("unknown-service")

    def test_factory_handles_all_nllb_variants(self):
        """Factory should handle all NLLB model variants"""
        variants = ["nllb", "nllb-600m", "nllb-1.3b", "nllb-distilled-600m"]

        for variant in variants:
            service = TranslationServiceFactory.create_service(variant)
            assert service is not None
            assert isinstance(service, ITranslationService)

    def test_factory_handles_all_opus_variants(self):
        """Factory should handle all OPUS model variants"""
        variants = ["opus", "opus-de-en", "opus-de-es", "opus-de-es-big"]

        for variant in variants:
            service = TranslationServiceFactory.create_service(variant)
            assert service is not None
            assert isinstance(service, ITranslationService)


@skip_if_no_torch
class TestTranslationFactoryChunkProcessingScenario:
    """Test factory usage as it appears in chunk processing"""

    def test_factory_handles_chunk_translation_service_call(self):
        """
        Reproduce exact factory call from chunk_translation_service.py line 54
        This is the call that was failing before the fix
        """
        # Exact call from chunk_translation_service.py:54-58
        service = TranslationServiceFactory.create_service(source_lang="de", target_lang="es", quality="standard")

        assert service is not None
        assert isinstance(service, ITranslationService)
        # Default service when no service_name specified should be "nllb"
        assert "nllb" in service.model_name.lower()

    def test_factory_handles_multiple_language_pairs(self):
        """Factory should handle creation of services for different language pairs"""
        # Simulate creating multiple translation services for different pairs
        pairs = [("de", "en"), ("de", "es"), ("en", "de"), ("fr", "en")]

        services = []
        for source, target in pairs:
            service = TranslationServiceFactory.create_service(
                source_lang=source, target_lang=target, quality="standard"
            )
            services.append(service)

        # All should be created successfully
        assert len(services) == 4
        assert all(isinstance(s, ITranslationService) for s in services)


@skip_if_no_torch
class TestTranslationFactoryServiceRegistry:
    """Test service registry functionality"""

    def test_get_available_services(self):
        """Factory should list available services"""
        available = TranslationServiceFactory.get_available_services()

        assert isinstance(available, dict)
        assert "nllb" in available
        assert "opus-de-es" in available

    def test_all_registered_services_can_be_instantiated(self):
        """All registered services should be instantiable"""
        available = TranslationServiceFactory.get_available_services()

        # Try to create each service
        for service_name in available:
            service = TranslationServiceFactory.create_service(service_name)
            assert service is not None
            assert isinstance(service, ITranslationService)
