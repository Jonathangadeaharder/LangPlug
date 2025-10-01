"""
Standalone test to verify refactored filtering handler architecture
Run with: python test_refactored_filtering.py
"""

import inspect
import sys

from services.processing.filtering import (
    FilteringCoordinatorService,
    ProgressTrackerService,
    ResultProcessorService,
    SubtitleLoaderService,
    VocabularyBuilderService,
)
from services.processing.filtering_handler import FilteringHandler


def test_architecture_structure():
    """Verify the service architecture is correctly structured"""

    # Test 1: Facade initialization
    handler = FilteringHandler()
    assert handler.progress_tracker is not None, "Progress tracker not initialized"
    assert handler.loader is not None, "Loader not initialized"
    assert handler.vocab_builder is not None, "Vocab builder not initialized"
    assert handler.result_processor is not None, "Result processor not initialized"
    assert handler.coordinator is not None, "Coordinator not initialized"

    # Test 2: Sub-service types
    assert isinstance(handler.progress_tracker, ProgressTrackerService)
    assert isinstance(handler.loader, SubtitleLoaderService)
    assert isinstance(handler.vocab_builder, VocabularyBuilderService)
    assert isinstance(handler.result_processor, ResultProcessorService)
    assert isinstance(handler.coordinator, FilteringCoordinatorService)

    # Test 3: Facade exposes required methods
    methods = [
        "health_check",
        "handle",
        "validate_parameters",
        "filter_subtitles",
        "extract_blocking_words",
        "refilter_for_translations",
        "estimate_duration",
    ]
    for method in methods:
        assert hasattr(handler, method), f"Missing method: {method}"


def test_sub_service_independence():
    """Verify sub-services can be used independently"""

    # Test 4: Progress tracker standalone
    tracker = ProgressTrackerService()
    assert hasattr(tracker, "initialize")
    assert hasattr(tracker, "update_progress")
    assert hasattr(tracker, "mark_complete")
    assert hasattr(tracker, "mark_failed")

    # Test 5: Subtitle loader standalone
    loader = SubtitleLoaderService()
    assert hasattr(loader, "load_and_parse")
    assert hasattr(loader, "extract_words_from_text")
    assert hasattr(loader, "estimate_duration")

    # Test 6: Vocabulary builder standalone
    builder = VocabularyBuilderService()
    assert hasattr(builder, "build_vocabulary_words")
    assert hasattr(builder, "generate_candidate_forms")

    # Test 7: Result processor standalone
    processor = ResultProcessorService()
    assert hasattr(processor, "process_filtering_results")
    assert hasattr(processor, "format_results")
    assert hasattr(processor, "save_to_file")

    # Test 8: Filtering coordinator standalone
    coordinator = FilteringCoordinatorService()
    assert hasattr(coordinator, "extract_blocking_words")
    assert hasattr(coordinator, "refilter_for_translations")


def test_service_metrics():
    """Verify architectural improvements are measurable"""

    # Test 9: Service line counts

    facade_lines = len(inspect.getsource(FilteringHandler).split("\n"))
    assert facade_lines < 300, f"Facade too large: {facade_lines} lines"

    tracker_lines = len(inspect.getsource(ProgressTrackerService).split("\n"))
    assert tracker_lines < 100, f"Progress tracker too large: {tracker_lines} lines"

    loader_lines = len(inspect.getsource(SubtitleLoaderService).split("\n"))
    assert loader_lines < 150, f"Subtitle loader too large: {loader_lines} lines"

    builder_lines = len(inspect.getsource(VocabularyBuilderService).split("\n"))
    assert builder_lines < 300, f"Vocabulary builder too large: {builder_lines} lines"

    processor_lines = len(inspect.getsource(ResultProcessorService).split("\n"))
    assert processor_lines < 150, f"Result processor too large: {processor_lines} lines"

    coordinator_lines = len(inspect.getsource(FilteringCoordinatorService).split("\n"))
    assert coordinator_lines < 250, f"Filtering coordinator too large: {coordinator_lines} lines"

    (facade_lines + tracker_lines + loader_lines + builder_lines + processor_lines + coordinator_lines)

    # Test 10: Method counts per service

    tracker = ProgressTrackerService()
    tracker_methods = [m for m in dir(tracker) if not m.startswith("_") and callable(getattr(tracker, m))]
    assert len(tracker_methods) <= 5, "Progress tracker has too many methods"

    loader = SubtitleLoaderService()
    loader_methods = [m for m in dir(loader) if not m.startswith("_") and callable(getattr(loader, m))]
    assert len(loader_methods) <= 5, "Subtitle loader has too many methods"

    builder = VocabularyBuilderService()
    builder_methods = [m for m in dir(builder) if not m.startswith("_") and callable(getattr(builder, m))]
    assert len(builder_methods) <= 5, "Vocabulary builder has too many methods"


def main():
    """Run all architecture tests"""

    try:
        test_architecture_structure()
        test_sub_service_independence()
        test_service_metrics()

        return 0

    except AssertionError:
        return 1
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
