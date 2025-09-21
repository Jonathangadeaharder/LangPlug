#!/usr/bin/env python3
"""
Simple script to verify that our fixes are syntactically correct
"""
import sys

def test_imports():
    """Test that all our fixed imports work"""
    try:
        # Test WordStatus enum import and values
        from services.filterservice.interface import WordStatus
        print("✓ WordStatus import successful")
        
        # Check that the enum values we fixed exist
        assert hasattr(WordStatus, 'FILTERED_INVALID'), "FILTERED_INVALID missing"
        assert hasattr(WordStatus, 'FILTERED_OTHER'), "FILTERED_OTHER missing"
        print("✓ WordStatus enum values exist")
        
        # Test DirectSubtitleProcessor import
        from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor
        print("✓ DirectSubtitleProcessor import successful")
        
        # Test database imports
        from core.database import AsyncSessionLocal
        from database.models import Vocabulary, UserLearningProgress
        print("✓ Database imports successful")
        
        print("\n🎉 All imports successful! The fixes should resolve the test failures.")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AttributeError as e:
        print(f"✗ Attribute error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)