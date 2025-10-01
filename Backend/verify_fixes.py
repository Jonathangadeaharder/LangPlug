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

        # Check that the enum values we fixed exist
        assert hasattr(WordStatus, "FILTERED_INVALID"), "FILTERED_INVALID missing"
        assert hasattr(WordStatus, "FILTERED_OTHER"), "FILTERED_OTHER missing"

        # Test DirectSubtitleProcessor import
        # Test database imports
        from core.database import AsyncSessionLocal
        from database.models import UserLearningProgress, Vocabulary
        from services.filterservice.direct_subtitle_processor import DirectSubtitleProcessor

        return True

    except ImportError:
        return False
    except AttributeError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
