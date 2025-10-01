#!/usr/bin/env python
"""Capture actual test error for vocabulary routes test."""

import subprocess
import sys

# Run the full suite and capture the failure
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/",
        "--ignore=tests/unit/services/test_log_handlers.py",
        "--ignore=tests/unit/services/test_log_manager.py",
        "--ignore=tests/unit/services/test_log_formatter.py",
        "--ignore=tests/unit/services/test_logging_service_complete.py",
        "-x",  # Stop on first failure
        "--tb=long",
        "--log-cli-level=DEBUG",
        "-v",
    ],
    check=False,
    capture_output=True,
    text=True,
)

# Find the failure section
output = result.stdout + result.stderr
lines = output.split("\n")

# Find debug logging for vocabulary stats
for _i, line in enumerate(lines):
    if "get_vocabulary_stats called" in line or "Taking session path" in line or "Taking original path" in line:
        pass

# Find FAILED line and print context
for _i, line in enumerate(lines):
    if "FAILED" in line and "test_vocabulary_routes" in line:
        # Print 50 lines after the failure
        break
