#!/usr/bin/env python3
"""
Test Script for Stateless Processing Steps Configuration

This script tests that the centralized configuration can be properly loaded
and passed to ProcessingContext for stateless processing steps.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from config import get_config
    from shared_utils.subtitle_utils import load_word_list
    from processing_steps import ProcessingContext
except ImportError as e:
    print(f"Import error: {e}")
    print("Some dependencies may be missing, but we can still test configuration loading.")

def test_configuration_loading():
    """Test that configuration can be loaded and prepared for ProcessingContext."""
    print("Testing centralized configuration loading...")
    
    try:
        # Load centralized configuration
        config = get_config()
        print("✓ Centralized configuration loaded successfully")
        
        # Test word list configuration
        print(f"\nWord List Configuration:")
        print(f"  - A1 words: {config.word_lists.a1_words}")
        print(f"  - Charaktere words: {config.word_lists.charaktere_words}")
        print(f"  - Giuliwords: {config.word_lists.giuliwords}")
        print(f"  - Brands: {config.word_lists.brands}")
        print(f"  - Onomatopoeia: {config.word_lists.onomatopoeia}")
        print(f"  - Interjections: {config.word_lists.interjections}")
        
        # Test processing configuration
        print(f"\nProcessing Configuration:")
        print(f"  - Batch size: {config.processing.batch_size}")
        print(f"  - Default language: {config.processing.default_language}")
        print(f"  - Supported languages: {config.processing.supported_languages}")
        print(f"  - Subtitle formats: {config.processing.subtitle_formats}")
        
        # Test API configuration
        print(f"\nAPI Configuration:")
        print(f"  - Host: {config.api.host}")
        print(f"  - Port: {config.api.port}")
        print(f"  - Debug: {config.api.debug}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_word_list_loading():
    """Test loading word lists from centralized configuration."""
    print("\nTesting word list loading...")
    
    try:
        config = get_config()
        
        # Load known words from centralized configuration
        known_words = set()
        core_word_lists = [
            config.word_lists.a1_words,
            config.word_lists.charaktere_words,
            config.word_lists.giuliwords
        ]
        
        for word_list_path in core_word_lists:
            if os.path.exists(word_list_path):
                try:
                    words = load_word_list(word_list_path)
                    known_words.update(words)
                    print(f"✓ Loaded {len(words)} words from {os.path.basename(word_list_path)}")
                except Exception as e:
                    print(f"✗ Failed to load {word_list_path}: {e}")
            else:
                print(f"⚠ Word list not found: {word_list_path}")
        
        print(f"\n✓ Total known words loaded: {len(known_words)}")
        return len(known_words) > 0
        
    except Exception as e:
        print(f"✗ Word list loading failed: {e}")
        return False

def test_processing_context_creation():
    """Test creating ProcessingContext with centralized configuration."""
    print("\nTesting ProcessingContext creation with configuration...")
    
    try:
        config = get_config()
        
        # Prepare configuration data
        known_words = {"test", "word", "list"}  # Mock data for testing
        
        word_list_files = {
            'a1_words': config.word_lists.a1_words,
            'charaktere_words': config.word_lists.charaktere_words,
            'giuliwords': config.word_lists.giuliwords,
            'brands': config.word_lists.brands,
            'onomatopoeia': config.word_lists.onomatopoeia,
            'interjections': config.word_lists.interjections
        }
        
        processing_config = {
            'batch_size': config.processing.batch_size,
            'default_language': config.processing.default_language,
            'supported_languages': config.processing.supported_languages,
            'subtitle_formats': config.processing.subtitle_formats
        }
        
        # Create ProcessingContext with configuration
        context = ProcessingContext(
            video_file="test_video.mp4",
            model_manager=None,  # Mock for testing
            language="de",
            src_lang="de",
            tgt_lang="es",
            known_words=known_words,
            word_list_files=word_list_files,
            processing_config=processing_config
        )
        
        print("✓ ProcessingContext created successfully")
        print(f"  - Known words: {len(context.known_words)} words")
        print(f"  - Word list files: {len(context.word_list_files)} files")
        print(f"  - Processing config keys: {list(context.processing_config.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ ProcessingContext creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("=" * 70)
    print("Testing Stateless Processing Steps Configuration")
    print("=" * 70)
    
    tests = [
        test_configuration_loading,
        test_word_list_loading,
        test_processing_context_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("Test Results:")
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {i+1}. {test.__name__}: {status}")
    
    all_passed = all(results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Configuration refactoring successful!")
        print("   - Centralized configuration is working")
        print("   - ProcessingSteps can now be stateless")
        print("   - Configuration is passed via ProcessingContext")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())