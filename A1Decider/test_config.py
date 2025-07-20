#!/usr/bin/env python3
"""
Simple test script to verify the centralized configuration system.
"""

import os
from config import get_config

def test_configuration():
    """Test the configuration system."""
    print("Testing A1Decider Centralized Configuration...")
    
    # Load configuration
    config = get_config()
    print("✓ Configuration loaded successfully")
    
    # Test basic properties
    print(f"Base directory: {config.file_paths.base_dir}")
    print(f"API endpoint: http://{config.api.host}:{config.api.port}")
    print(f"Processing batch size: {config.processing.batch_size}")
    
    # Test word list files
    word_files = config.word_lists.get_all_files()
    existing_files = [f for f in word_files if os.path.exists(f)]
    print(f"Word lists found: {len(existing_files)} of {len(word_files)}")
    
    # Test core word lists
    core_files = config.word_lists.get_core_files()
    existing_core = [f for f in core_files if os.path.exists(f)]
    print(f"Core word lists found: {len(existing_core)} of {len(core_files)}")
    
    # Test validation
    validation = config.validate_config()
    passed = sum(1 for status in validation.values() if status)
    total = len(validation)
    print(f"Validation: {passed}/{total} components passed")
    
    if passed == total:
        print("\n✓ All tests passed! Configuration system is working correctly.")
        return True
    else:
        print(f"\n⚠ Some components failed validation:")
        for component, status in validation.items():
            if not status:
                print(f"  ✗ {component}")
        return False

if __name__ == "__main__":
    success = test_configuration()
    exit(0 if success else 1)