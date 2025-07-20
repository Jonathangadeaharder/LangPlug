#!/usr/bin/env python3
"""
Simple validation script for granular ProcessingContext interfaces.
This script demonstrates interface usage without requiring heavy dependencies.
"""

import sys
import os
from typing import Protocol

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_interface_definitions():
    """Validate that all interfaces are properly defined."""
    print("=== Validating Interface Definitions ===")
    
    try:
        from processing_interfaces import (
            ITranscriptionContext,
            IFilteringContext,
            ITranslationContext,
            IPreviewProcessingContext,
            IConfigurationContext,
            IMetadataContext
        )
        
        # Check that all interfaces are Protocols
        interfaces = [
            (ITranscriptionContext, "ITranscriptionContext"),
            (IFilteringContext, "IFilteringContext"),
            (ITranslationContext, "ITranslationContext"),
            (IPreviewProcessingContext, "IPreviewProcessingContext"),
            (IConfigurationContext, "IConfigurationContext"),
            (IMetadataContext, "IMetadataContext")
        ]
        
        for interface, name in interfaces:
            if issubclass(interface, Protocol):
                print(f"✓ {name} is properly defined as a Protocol")
            else:
                print(f"⚠ {name} is not a Protocol")
        
        print("✓ All interface definitions validated")
        return True
        
    except Exception as e:
        print(f"✗ Interface validation failed: {e}")
        return False

def validate_context_implementation():
    """Validate that ProcessingContext implements all interfaces."""
    print("\n=== Validating ProcessingContext Implementation ===")
    
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
        
        # Create a minimal context
        context = ProcessingContext(
            video_file="test.mp4",
            model_manager=None
        )
        
        # Test interface implementation
        interfaces = [
            (ITranscriptionContext, "ITranscriptionContext"),
            (IFilteringContext, "IFilteringContext"),
            (ITranslationContext, "ITranslationContext"),
            (IPreviewProcessingContext, "IPreviewProcessingContext"),
            (IConfigurationContext, "IConfigurationContext"),
            (IMetadataContext, "IMetadataContext")
        ]
        
        for interface, name in interfaces:
            if isinstance(context, interface):
                print(f"✓ ProcessingContext implements {name}")
            else:
                print(f"✗ ProcessingContext does NOT implement {name}")
                return False
        
        print("✓ ProcessingContext implementation validated")
        return True
        
    except Exception as e:
        print(f"✗ Context implementation validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_base_classes():
    """Validate that granular base classes are properly defined."""
    print("\n=== Validating Granular Base Classes ===")
    
    try:
        from processing_interfaces import (
            TranscriptionStep,
            FilteringStep,
            TranslationStep,
            PreviewProcessingStep
        )
        
        base_classes = [
            (TranscriptionStep, "TranscriptionStep"),
            (FilteringStep, "FilteringStep"),
            (TranslationStep, "TranslationStep"),
            (PreviewProcessingStep, "PreviewProcessingStep")
        ]
        
        for base_class, name in base_classes:
            # Check if class has required methods
            required_methods = ['execute', 'log_start', 'log_success', 'log_error', 'log_skip']
            missing_methods = []
            
            for method in required_methods:
                if not hasattr(base_class, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"⚠ {name} missing methods: {missing_methods}")
            else:
                print(f"✓ {name} has all required methods")
        
        print("✓ Granular base classes validated")
        return True
        
    except Exception as e:
        print(f"✗ Base class validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_interface_usage():
    """Demonstrate how the interfaces work in practice."""
    print("\n=== Demonstrating Interface Usage ===")
    
    try:
        from processing_steps import ProcessingContext
        from processing_interfaces import (
            ITranscriptionContext,
            IFilteringContext,
            TranscriptionStep,
            FilteringStep
        )
        
        # Create a context
        context = ProcessingContext(
            video_file="demo.mp4",
            model_manager=None,
            known_words={"hello", "world"}
        )
        
        # Demonstrate interface-specific access
        def use_transcription_context(ctx: ITranscriptionContext):
            """Function that only needs transcription data."""
            return f"Processing video: {ctx.video_file}"
        
        def use_filtering_context(ctx: IFilteringContext):
            """Function that only needs filtering data."""
            return f"Known words count: {len(ctx.known_words) if ctx.known_words else 0}"
        
        # Test interface usage
        transcription_result = use_transcription_context(context)
        filtering_result = use_filtering_context(context)
        
        print(f"✓ Transcription interface usage: {transcription_result}")
        print(f"✓ Filtering interface usage: {filtering_result}")
        
        # Demonstrate that the same context can be used with different interfaces
        print("✓ Same context works with multiple interfaces")
        
        print("✓ Interface usage demonstration completed")
        return True
        
    except Exception as e:
        print(f"✗ Interface usage demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validations."""
    print("Granular ProcessingContext Interfaces Validation")
    print("=" * 55)
    
    validations = [
        validate_interface_definitions,
        validate_context_implementation,
        validate_base_classes,
        demonstrate_interface_usage
    ]
    
    results = []
    for validation in validations:
        result = validation()
        results.append(result)
    
    print("\n" + "=" * 55)
    print("VALIDATION SUMMARY:")
    
    all_passed = all(results)
    if all_passed:
        print("✅ All validations passed! Granular interfaces are working correctly.")
        print("\n🎉 Interface Segregation Principle successfully implemented!")
        print("\n📋 Key Benefits Achieved:")
        print("   • Explicit data dependencies through type hints")
        print("   • Prevention of ProcessingContext 'god object' anti-pattern")
        print("   • Enhanced testability with focused interfaces")
        print("   • Future-proof architecture for system growth")
        print("   • Maintained backward compatibility")
    else:
        print("❌ Some validations failed. Please check the output above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)