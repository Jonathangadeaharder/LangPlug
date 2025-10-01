#!/usr/bin/env python3
"""Analyze test coverage to identify low-coverage files"""

import json

# Load coverage data
with open("coverage.json") as f:
    data = json.load(f)

# Print overall coverage
overall_coverage = data["totals"]["percent_covered"]

# Get files sorted by coverage
files = [(k, v["summary"]["percent_covered"]) for k, v in data["files"].items()]
files.sort(key=lambda x: x[1])

# Print lowest coverage production files
count = 0
for filepath, percent in files:
    # Skip test files and focus on production code
    if "test" not in filepath.lower() and percent < 60:
        filename = filepath.split("/")[-1]
        count += 1
        if count >= 25:
            break
