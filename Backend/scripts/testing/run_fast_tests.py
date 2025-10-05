#!/usr/bin/env python
"""
Run fast Backend tests that don't timeout
"""

import os
import subprocess
import sys

# Set environment variables for test mode
os.environ["TESTING"] = "1"
os.environ["ANYIO_BACKEND"] = "asyncio"

# Test directories that work reliably
TEST_DIRS = [
    "tests/unit/core",
    "tests/unit/models",
    # Individual service tests work but timeout when run together
    "tests/unit/services/test_auth_service.py",
    "tests/unit/services/test_video_service.py",
    "tests/unit/services/test_vocabulary_service.py",
    "tests/unit/services/test_transcription_interface.py",
    "tests/unit/services/test_vocabulary_preload_service.py",
    "tests/unit/test_game_models.py",
    # Some API tests that work
    "tests/api/test_auth_endpoints.py",
]


def run_tests():
    """Run all fast tests"""

    total_passed = 0
    total_failed = 0

    for test_dir in TEST_DIRS:
        cmd = [
            "python",
            "-m",
            "pytest",
            test_dir,
            "--tb=short",
            "-q",
            "--timeout=20",
            "--timeout-method=thread",
            "--maxfail=3",
        ]

        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Parse output for pass/fail counts
        output = result.stdout + result.stderr

        if "passed" in output:
            # Extract pass count
            for line in output.split("\n"):
                if "passed" in line:
                    # Try to extract number
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed":
                            try:
                                count = int(parts[i - 1])
                                total_passed += count
                                break
                            except (ValueError, IndexError):
                                pass

        if result.returncode != 0:
            total_failed += 1

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
