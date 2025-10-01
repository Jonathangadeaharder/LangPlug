"""Simple architecture test runner that bypasses pytest conftest"""

import sys
from pathlib import Path

# Add Backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import test classes
from tests.unit.services.test_direct_subtitle_processor_architecture import (
    TestDirectSubtitleProcessorArchitecture,
    TestServiceSingletons,
    TestSRTFileHandlerService,
    TestSubtitleProcessorService,
    TestUserDataLoaderService,
    TestWordFilterService,
    TestWordValidatorService,
)


def run_sync_test(test_class, test_method):
    """Run a synchronous test"""
    try:
        instance = test_class()
        method = getattr(instance, test_method)
        method()
        return True, None
    except Exception as e:
        return False, str(e)


async def run_async_test(test_class, test_method):
    """Run an async test"""
    try:
        instance = test_class()
        method = getattr(instance, test_method)
        await method()
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    """Run all architecture tests"""

    results = []

    # Facade tests
    results.append(
        (
            "Facade imports all services",
            *run_sync_test(TestDirectSubtitleProcessorArchitecture, "test_facade_imports_all_services"),
        )
    )
    results.append(
        (
            "Facade does not contain implementation",
            *run_sync_test(
                TestDirectSubtitleProcessorArchitecture, "test_facade_does_not_contain_implementation_logic"
            ),
        )
    )

    # UserDataLoader tests
    results.append(("UserDataLoader exists", *run_sync_test(TestUserDataLoaderService, "test_user_data_loader_exists")))
    results.append(
        ("UserDataLoader has caching", *run_sync_test(TestUserDataLoaderService, "test_user_data_loader_has_caching"))
    )

    # WordValidator tests
    results.append(("WordValidator exists", *run_sync_test(TestWordValidatorService, "test_word_validator_exists")))
    results.append(
        (
            "WordValidator validates words",
            *run_sync_test(TestWordValidatorService, "test_word_validator_validates_vocabulary_words"),
        )
    )
    results.append(
        (
            "WordValidator detects interjections",
            *run_sync_test(TestWordValidatorService, "test_word_validator_detects_interjections"),
        )
    )
    results.append(
        (
            "WordValidator supports multiple languages",
            *run_sync_test(TestWordValidatorService, "test_word_validator_supports_multiple_languages"),
        )
    )
    results.append(
        (
            "WordValidator provides validation reasons",
            *run_sync_test(TestWordValidatorService, "test_word_validator_provides_validation_reasons"),
        )
    )

    # WordFilter tests
    results.append(("WordFilter exists", *run_sync_test(TestWordFilterService, "test_word_filter_exists")))
    results.append(
        ("WordFilter filters words", *run_sync_test(TestWordFilterService, "test_word_filter_filters_words"))
    )
    results.append(
        (
            "WordFilter checks user knowledge",
            *run_sync_test(TestWordFilterService, "test_word_filter_checks_user_knowledge"),
        )
    )
    results.append(
        (
            "WordFilter has level comparison",
            *run_sync_test(TestWordFilterService, "test_word_filter_has_level_comparison"),
        )
    )

    # SubtitleProcessor tests
    results.append(
        ("SubtitleProcessor exists", *run_sync_test(TestSubtitleProcessorService, "test_subtitle_processor_exists"))
    )
    results.append(
        (
            "SubtitleProcessor has dependencies",
            *run_sync_test(TestSubtitleProcessorService, "test_subtitle_processor_has_dependencies"),
        )
    )

    # SRTFileHandler tests
    results.append(("SRTFileHandler exists", *run_sync_test(TestSRTFileHandlerService, "test_srt_file_handler_exists")))
    results.append(
        (
            "SRTFileHandler extracts words",
            *run_sync_test(TestSRTFileHandlerService, "test_srt_file_handler_extracts_words"),
        )
    )
    results.append(
        (
            "SRTFileHandler formats results",
            *run_sync_test(TestSRTFileHandlerService, "test_srt_file_handler_formats_results"),
        )
    )

    # Singleton tests
    results.append(("All singletons exist", *run_sync_test(TestServiceSingletons, "test_all_singletons_exist")))
    results.append(
        (
            "Singletons are correct instances",
            *run_sync_test(TestServiceSingletons, "test_singletons_are_service_instances"),
        )
    )

    # Summary

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for _test_name, success, error in results:
        if error and not success:
            pass

    if passed == total:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
