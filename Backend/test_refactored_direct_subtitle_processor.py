"""
Verification script for refactored DirectSubtitleProcessor
Tests basic functionality and service integration
"""

import asyncio
import sys
from pathlib import Path

# Add Backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_imports():
    """Test all service imports work"""

    try:
        from services.filterservice.subtitle_processing import (
            SRTFileHandler,
            SubtitleProcessor,
            UserDataLoader,
            WordFilter,
            WordValidator,
            srt_file_handler,
            subtitle_processor,
            user_data_loader,
            word_filter,
            word_validator,
        )

        return True
    except ImportError:
        return False


def test_facade_instantiation():
    """Test facade can be instantiated"""

    try:
        from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

        processor = DirectSubtitleProcessor()

        # Verify services are initialized
        assert processor.data_loader is not None
        assert processor.validator is not None
        assert processor.filter is not None
        assert processor.processor is not None
        assert processor.file_handler is not None
        assert processor.vocab_service is not None

        return True
    except Exception:
        return False


def test_service_singletons():
    """Test singleton instances work"""

    try:
        from services.filterservice.subtitle_processing import (
            srt_file_handler,
            subtitle_processor,
            user_data_loader,
            word_filter,
            word_validator,
        )

        # Test each singleton
        assert user_data_loader is not None
        assert word_validator is not None
        assert word_filter is not None
        assert subtitle_processor is not None
        assert srt_file_handler is not None

        return True
    except Exception:
        return False


def test_word_validator_basic():
    """Test word validator basic functionality"""

    try:
        from services.filterservice.subtitle_processing import WordValidator

        validator = WordValidator()

        # Test valid vocabulary word (longer word)
        result = validator.is_valid_vocabulary_word("schwierig", "de")
        assert result, f"Expected 'schwierig' to be valid, got {result}"

        # Test invalid words
        result = validator.is_valid_vocabulary_word("123", "de")
        assert not result, f"Expected '123' to be invalid, got {result}"

        result = validator.is_valid_vocabulary_word("oh", "de")
        assert not result, f"Expected 'oh' to be invalid, got {result}"

        # Test interjection detection
        assert validator.is_interjection("hallo", "de")
        assert not validator.is_interjection("schwierig", "de")

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def test_word_filter_basic():
    """Test word filter basic functionality"""

    try:
        from services.filterservice.interface import FilteredWord, WordStatus
        from services.filterservice.subtitle_processing import WordFilter

        word_filter_service = WordFilter()

        # Create test word
        test_word = FilteredWord(
            text="schwierig",
            start_time=0.0,
            end_time=1.0,
            status=WordStatus.ACTIVE,
            filter_reason=None,
            confidence=None,
            metadata={},
        )

        # Test filtering (should mark as active since not in known words)
        user_known_words = set()
        result = word_filter_service.filter_word(test_word, user_known_words, "A1", "de", word_info=None)

        assert result.status == WordStatus.ACTIVE
        assert "lemma" in result.metadata

        return True
    except Exception:
        return False


async def test_facade_process_subtitles():
    """Test facade process_subtitles method"""

    try:
        from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
        from services.filterservice.interface import FilteredSubtitle, FilteredWord, WordStatus

        processor = DirectSubtitleProcessor()

        # Create test subtitle
        word = FilteredWord(
            text="hallo",
            start_time=0.0,
            end_time=1.0,
            status=WordStatus.ACTIVE,
            filter_reason=None,
            confidence=None,
            metadata={},
        )

        subtitle = FilteredSubtitle(original_text="Hallo Welt", start_time=0.0, end_time=2.0, words=[word])

        # Process (using test user_id that won't be in database)
        result = await processor.process_subtitles(
            [subtitle], user_id="test_user_12345", user_level="A1", language="de"
        )

        # Verify result structure
        assert result.learning_subtitles is not None
        assert result.blocker_words is not None
        assert result.empty_subtitles is not None
        assert result.statistics is not None
        assert "total_subtitles" in result.statistics
        assert result.statistics["user_id"] == "test_user_12345"

        return True
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""

    results = []

    # Synchronous tests
    results.append(("Imports", test_imports()))
    results.append(("Facade Instantiation", test_facade_instantiation()))
    results.append(("Service Singletons", test_service_singletons()))
    results.append(("WordValidator", test_word_validator_basic()))
    results.append(("WordFilter", test_word_filter_basic()))

    # Async tests
    results.append(("Facade Process", asyncio.run(test_facade_process_subtitles())))

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
