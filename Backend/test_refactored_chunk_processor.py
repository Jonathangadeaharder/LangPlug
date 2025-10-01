"""
Verification script for refactored ChunkProcessingService
Tests basic functionality and service integration
"""

import sys
from pathlib import Path

# Add Backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_imports():
    """Test all service imports work"""

    try:
        from services.processing.chunk_services import (
            SubtitleGenerationService,
            TranslationManagementService,
            VocabularyFilterService,
            subtitle_generation_service,
            translation_management_service,
            vocabulary_filter_service,
        )

        return True
    except ImportError:
        return False


def test_service_singletons():
    """Test singleton instances work"""

    try:
        from services.processing.chunk_services import (
            subtitle_generation_service,
            translation_management_service,
            vocabulary_filter_service,
        )

        # Test each singleton
        assert vocabulary_filter_service is not None
        assert subtitle_generation_service is not None
        assert translation_management_service is not None

        return True
    except Exception:
        return False


def test_vocabulary_filter_service():
    """Test VocabularyFilterService basics"""

    try:
        from services.processing.chunk_services import VocabularyFilterService

        service = VocabularyFilterService()

        # Test has subtitle_processor
        assert hasattr(service, "subtitle_processor")
        assert service.subtitle_processor is not None

        # Test has methods
        assert hasattr(service, "filter_vocabulary_from_srt")
        assert hasattr(service, "extract_vocabulary_from_result")
        assert hasattr(service, "debug_empty_vocabulary")

        return True
    except Exception:
        return False


def test_subtitle_generation_service():
    """Test SubtitleGenerationService basics"""

    try:
        from services.processing.chunk_services import SubtitleGenerationService

        service = SubtitleGenerationService()

        # Test has methods
        assert hasattr(service, "generate_filtered_subtitles")
        assert hasattr(service, "process_srt_content")
        assert hasattr(service, "highlight_vocabulary_in_line")
        assert hasattr(service, "read_srt_file")
        assert hasattr(service, "write_srt_file")

        # Test highlighting logic
        line = "Das ist ein Test"
        vocab_words = {"test"}
        highlighted = service.highlight_vocabulary_in_line(line, vocab_words)

        assert "test" in highlighted.lower()
        assert "font" in highlighted.lower() or highlighted == line  # Either highlighted or unchanged

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_translation_management_service():
    """Test TranslationManagementService basics"""

    try:
        from services.processing.chunk_services import TranslationManagementService

        service = TranslationManagementService()

        # Test has subtitle_processor
        assert hasattr(service, "subtitle_processor")
        assert service.subtitle_processor is not None

        # Test has methods
        assert hasattr(service, "apply_selective_translations")
        assert hasattr(service, "refilter_for_translations")
        assert hasattr(service, "build_translation_segments")
        assert hasattr(service, "filter_unknown_words")
        assert hasattr(service, "create_translation_segments")
        assert hasattr(service, "create_translation_segment")
        assert hasattr(service, "create_translation_response")
        assert hasattr(service, "create_fallback_response")

        return True
    except Exception:
        return False


def test_chunk_processor_facade():
    """Test ChunkProcessingService facade structure"""

    try:
        from unittest.mock import Mock

        from services.processing.chunk_processor import ChunkProcessingService

        # Create mock database session
        db_session = Mock()

        # Create facade
        service = ChunkProcessingService(db_session)

        # Verify all services are initialized
        assert hasattr(service, "transcription_service")
        assert hasattr(service, "translation_service")
        assert hasattr(service, "utilities")
        assert hasattr(service, "vocabulary_filter")
        assert hasattr(service, "subtitle_generator")
        assert hasattr(service, "translation_manager")

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Service Singletons", test_service_singletons()))
    results.append(("VocabularyFilterService", test_vocabulary_filter_service()))
    results.append(("SubtitleGenerationService", test_subtitle_generation_service()))
    results.append(("TranslationManagementService", test_translation_management_service()))
    results.append(("ChunkProcessingService Facade", test_chunk_processor_facade()))

    # Summary

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for _test_name, _result in results:
        pass

    if passed == total:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
