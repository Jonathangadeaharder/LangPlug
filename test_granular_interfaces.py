#!/usr/bin/env python3
"""
Simple test script to verify the granular ProcessingContext interfaces implementation.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all interface modules can be imported."""
    print("=== Testing Imports ===")
    
    try:
        from processing_interfaces import (
            ITranscriptionContext,
            IFilteringContext,
            ITranslationContext,
            IPreviewProcessingContext,
            IConfigurationContext,
            IMetadataContext
        )
        print("✓ All interfaces imported successfully")
        
        from processing_steps import ProcessingContext
        print("✓ ProcessingContext imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_interface_implementation():
    """Test that ProcessingContext implements all granular interfaces."""
    print("\n=== Testing Interface Implementation ===")
    
    try:
        from processing_steps import ProcessingContext
        from processing_interfaces import (
            ITranscriptionContext,
            IFilteringContext,
            ITranslationContext,
            IPreviewProcessingContext,
            IConfigurationContext,
            IMetadataContext
        )
        
        # Create ProcessingContext instance with minimal required parameters
        context = ProcessingContext(
            video_file="test.mp4",
            model_manager=None  # Using None for simplicity
        )
        
        # Test that context implements all interfaces
        interfaces_to_test = [
            (ITranscriptionContext, "ITranscriptionContext"),
            (IFilteringContext, "IFilteringContext"),
            (ITranslationContext, "ITranslationContext"),
            (IPreviewProcessingContext, "IPreviewProcessingContext"),
            (IConfigurationContext, "IConfigurationContext"),
            (IMetadataContext, "IMetadataContext")
        ]
        
        for interface, name in interfaces_to_test:
            if isinstance(context, interface):
                print(f"✓ ProcessingContext implements {name}")
            else:
                print(f"✗ ProcessingContext does NOT implement {name}")
                return False
        
        print("✓ All interface implementations verified")
        return True
        
    except Exception as e:
        print(f"✗ Interface implementation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_imports():
    """Test that processing steps can be imported with new interfaces."""
    print("\n=== Testing Step Imports ===")
    
    try:
        from concrete_processing_steps import (
            PreviewTranscriptionStep,
            FullTranscriptionStep,
            A1FilterStep,
            TranslationStep,
            PreviewProcessingStep
        )
        print("✓ All processing steps imported successfully")
        
        # Test step instantiation
        steps = [
            (PreviewTranscriptionStep, "PreviewTranscriptionStep"),
            (FullTranscriptionStep, "FullTranscriptionStep"),
            (A1FilterStep, "A1FilterStep"),
            (TranslationStep, "TranslationStep"),
            (PreviewProcessingStep, "PreviewProcessingStep")
        ]
        
        for step_class, step_name in steps:
            try:
                step = step_class()
                print(f"✓ {step_name} instantiated successfully")
            except Exception as e:
                print(f"✗ {step_name} instantiation failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Step import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing Granular ProcessingContext Interfaces")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_interface_implementation,
        test_step_imports
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    all_passed = all(results)
    if all_passed:
        print("✓ All tests passed! Granular interfaces are working correctly.")
    else:
        print("✗ Some tests failed. Please check the output above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)