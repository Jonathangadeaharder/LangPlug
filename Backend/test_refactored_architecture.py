"""
Standalone test to verify refactored vocabulary service architecture
Run with: python test_refactored_architecture.py
"""

import sys

from services.vocabulary.vocabulary_progress_service import VocabularyProgressService
from services.vocabulary.vocabulary_query_service import VocabularyQueryService
from services.vocabulary.vocabulary_stats_service import VocabularyStatsService
from services.vocabulary_service import VocabularyService, vocabulary_service


def test_architecture_structure():
    """Verify the service architecture is correctly structured"""

    # Test 1: Facade initialization
    service = VocabularyService()
    assert service.query_service is not None, "Query service not initialized"
    assert service.progress_service is not None, "Progress service not initialized"
    assert service.stats_service is not None, "Stats service not initialized"

    # Test 2: Sub-service types
    assert isinstance(service.query_service, VocabularyQueryService)
    assert isinstance(service.progress_service, VocabularyProgressService)
    assert isinstance(service.stats_service, VocabularyStatsService)

    # Test 3: Global instance
    assert vocabulary_service is not None
    assert isinstance(vocabulary_service, VocabularyService)

    # Test 4: Facade exposes all methods
    methods = [
        "get_word_info",
        "get_vocabulary_library",
        "search_vocabulary",
        "mark_word_known",
        "bulk_mark_level",
        "get_user_vocabulary_stats",
        "get_vocabulary_stats",
        "get_user_progress_summary",
        "get_supported_languages",
        "get_vocabulary_level",
        "mark_concept_known",
    ]
    for method in methods:
        assert hasattr(service, method), f"Missing method: {method}"


def test_sub_service_independence():
    """Verify sub-services can be used independently"""

    # Test 5: Query service standalone
    query = VocabularyQueryService()
    assert hasattr(query, "get_word_info")
    assert hasattr(query, "get_vocabulary_library")
    assert hasattr(query, "search_vocabulary")

    # Test 6: Progress service standalone
    progress = VocabularyProgressService()
    assert hasattr(progress, "mark_word_known")
    assert hasattr(progress, "bulk_mark_level")

    # Test 7: Stats service standalone
    stats = VocabularyStatsService()
    assert hasattr(stats, "get_vocabulary_stats")
    assert hasattr(stats, "get_supported_languages")


def test_service_metrics():
    """Verify architectural improvements are measurable"""

    import inspect

    # Test 8: Service line counts

    facade_lines = len(inspect.getsource(VocabularyService).split("\n"))
    assert facade_lines < 200, f"Facade too large: {facade_lines} lines"

    query_lines = len(inspect.getsource(VocabularyQueryService).split("\n"))
    assert query_lines < 400, f"Query service too large: {query_lines} lines"

    progress_lines = len(inspect.getsource(VocabularyProgressService).split("\n"))
    assert progress_lines < 300, f"Progress service too large: {progress_lines} lines"

    stats_lines = len(inspect.getsource(VocabularyStatsService).split("\n"))
    assert stats_lines < 300, f"Stats service too large: {stats_lines} lines"

    facade_lines + query_lines + progress_lines + stats_lines

    # Test 9: Method counts per service

    query_service = VocabularyQueryService()
    [m for m in dir(query_service) if not m.startswith("_") and callable(getattr(query_service, m))]

    progress_service = VocabularyProgressService()
    [m for m in dir(progress_service) if not m.startswith("_") and callable(getattr(progress_service, m))]

    stats_service = VocabularyStatsService()
    [m for m in dir(stats_service) if not m.startswith("_") and callable(getattr(stats_service, m))]


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
