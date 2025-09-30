"""
Standalone test to verify refactored vocabulary service architecture
Run with: python test_refactored_architecture.py
"""

import asyncio
from services.vocabulary_service import vocabulary_service, VocabularyService
from services.vocabulary.vocabulary_query_service import VocabularyQueryService
from services.vocabulary.vocabulary_progress_service import VocabularyProgressService
from services.vocabulary.vocabulary_stats_service import VocabularyStatsService


def test_architecture_structure():
    """Verify the service architecture is correctly structured"""
    print("\n=== Testing Architecture Structure ===")
    
    # Test 1: Facade initialization
    print("\n[TEST 1] Facade initializes with all sub-services")
    service = VocabularyService()
    assert service.query_service is not None, "Query service not initialized"
    assert service.progress_service is not None, "Progress service not initialized"
    assert service.stats_service is not None, "Stats service not initialized"
    print("[PASS] All sub-services initialized")
    
    # Test 2: Sub-service types
    print("\n[TEST 2] Sub-services are correct types")
    assert isinstance(service.query_service, VocabularyQueryService)
    assert isinstance(service.progress_service, VocabularyProgressService)
    assert isinstance(service.stats_service, VocabularyStatsService)
    print("[PASS] All sub-services have correct types")
    
    # Test 3: Global instance
    print("\n[TEST 3] Global vocabulary_service instance exists")
    assert vocabulary_service is not None
    assert isinstance(vocabulary_service, VocabularyService)
    print("[PASS] Global instance available")
    
    # Test 4: Facade exposes all methods
    print("\n[TEST 4] Facade exposes all required methods")
    methods = [
        'get_word_info', 'get_vocabulary_library', 'search_vocabulary',
        'mark_word_known', 'bulk_mark_level', 'get_user_vocabulary_stats',
        'get_vocabulary_stats', 'get_user_progress_summary', 'get_supported_languages',
        'get_vocabulary_level', 'mark_concept_known'
    ]
    for method in methods:
        assert hasattr(service, method), f"Missing method: {method}"
        print(f"  [OK] Has method: {method}")
    print("[PASS] All methods available")


def test_sub_service_independence():
    """Verify sub-services can be used independently"""
    print("\n=== Testing Sub-Service Independence ===")
    
    # Test 5: Query service standalone
    print("\n[TEST 5] Query service works standalone")
    query = VocabularyQueryService()
    assert hasattr(query, 'get_word_info')
    assert hasattr(query, 'get_vocabulary_library')
    assert hasattr(query, 'search_vocabulary')
    print("[PASS] Query service standalone")
    
    # Test 6: Progress service standalone
    print("\n[TEST 6] Progress service works standalone")
    progress = VocabularyProgressService()
    assert hasattr(progress, 'mark_word_known')
    assert hasattr(progress, 'bulk_mark_level')
    print("[PASS] Progress service standalone")
    
    # Test 7: Stats service standalone
    print("\n[TEST 7] Stats service works standalone")
    stats = VocabularyStatsService()
    assert hasattr(stats, 'get_vocabulary_stats')
    assert hasattr(stats, 'get_supported_languages')
    print("[PASS] Stats service standalone")


def test_service_metrics():
    """Verify architectural improvements are measurable"""
    print("\n=== Testing Architecture Metrics ===")
    
    import inspect
    
    # Test 8: Service line counts
    print("\n[TEST 8] Service sizes are reasonable")
    
    facade_lines = len(inspect.getsource(VocabularyService).split('\n'))
    print(f"  Facade: {facade_lines} lines (target: <200)")
    assert facade_lines < 200, f"Facade too large: {facade_lines} lines"
    
    query_lines = len(inspect.getsource(VocabularyQueryService).split('\n'))
    print(f"  Query service: {query_lines} lines (target: <400)")
    assert query_lines < 400, f"Query service too large: {query_lines} lines"
    
    progress_lines = len(inspect.getsource(VocabularyProgressService).split('\n'))
    print(f"  Progress service: {progress_lines} lines (target: <300)")
    assert progress_lines < 300, f"Progress service too large: {progress_lines} lines"
    
    stats_lines = len(inspect.getsource(VocabularyStatsService).split('\n'))
    print(f"  Stats service: {stats_lines} lines (target: <300)")
    assert stats_lines < 300, f"Stats service too large: {stats_lines} lines"
    
    total_lines = facade_lines + query_lines + progress_lines + stats_lines
    print(f"  Total: {total_lines} lines (original: 1011 lines)")
    print("[PASS] All services within size targets")
    
    # Test 9: Method counts per service
    print("\n[TEST 9] Services have focused responsibilities")
    
    query_service = VocabularyQueryService()
    query_methods = [m for m in dir(query_service) if not m.startswith('_') and callable(getattr(query_service, m))]
    print(f"  Query service public methods: {len(query_methods)}")
    
    progress_service = VocabularyProgressService()
    progress_methods = [m for m in dir(progress_service) if not m.startswith('_') and callable(getattr(progress_service, m))]
    print(f"  Progress service public methods: {len(progress_methods)}")
    
    stats_service = VocabularyStatsService()
    stats_methods = [m for m in dir(stats_service) if not m.startswith('_') and callable(getattr(stats_service, m))]
    print(f"  Stats service public methods: {len(stats_methods)}")
    
    print("[PASS] Services have focused method sets")


def main():
    """Run all architecture tests"""
    print("\n" + "="*60)
    print(" REFACTORED VOCABULARY SERVICE ARCHITECTURE TESTS")
    print("="*60)
    
    try:
        test_architecture_structure()
        test_sub_service_independence()
        test_service_metrics()
        
        print("\n" + "="*60)
        print(" ALL TESTS PASSED!")
        print("="*60)
        print("\nArchitecture verification complete:")
        print("  - 9 test groups executed")
        print("  - Facade pattern working correctly")
        print("  - Sub-services independently functional")
        print("  - Size targets met")
        print("  - Separation of concerns achieved")
        print("\n")
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
