#!/usr/bin/env python3
"""
Automated script to convert f-string logging to structured logging.

Converts patterns like:
    logger.info(f"Message {var}")
To:
    logger.info("Message", var=var)

Run from project root:
    python scripts/fix_logging.py --dry-run  # Preview changes
    python scripts/fix_logging.py             # Apply changes
"""

import argparse
import re
from pathlib import Path


def fix_logging_in_file(file_path: Path, dry_run: bool = True) -> int:
    """Fix f-string logging in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] Could not read {file_path}: {e}")
        return 0

    original = content
    changes = 0

    # Pattern 1: Simple f-string with single variable
    # logger.info(f"Message {var}") -> logger.info("Message", var=var)
    pattern1 = re.compile(
        r'logger\.(info|debug|warning|error)\(f"([^"]*)\{(\w+)\}([^"]*)"\)'
    )

    def replace_simple(match):
        level, prefix, var, suffix = match.groups()
        # Clean up the message
        message = f"{prefix}{suffix}".strip()
        if message.endswith(":"):
            message = message[:-1].strip()
        return f'logger.{level}("{message}", {var}={var})'

    # Pattern 2: Remove [BRACKET PREFIXES]
    pattern2 = re.compile(r'\[[\w\s_-]+\]\s*')

    def replace_brackets(match):
        return ""

    # Apply fixes
    new_content = pattern1.sub(replace_simple, content)
    
    # Remove bracket prefixes from log messages
    bracket_pattern = re.compile(
        r'(logger\.\w+\()"(\[[A-Z_\s]+\])\s*([^"]*)"'
    )
    new_content = bracket_pattern.sub(r'\1"\3"', new_content)

    if new_content != original:
        changes = 1
        if not dry_run:
            file_path.write_text(new_content, encoding="utf-8")
            print(f"  [FIXED] {file_path}")
        else:
            print(f"  [WOULD FIX] {file_path}")

    return changes


def main():
    parser = argparse.ArgumentParser(description="Fix f-string logging")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    backend_path = Path(__file__).parent.parent / "src" / "backend"
    
    if not backend_path.exists():
        print(f"Backend path not found: {backend_path}")
        return

    print(f"Scanning {backend_path}...")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY CHANGES'}")
    print()

    total_files = 0
    fixed_files = 0

    for py_file in backend_path.rglob("*.py"):
        # Skip test files and data scripts
        if "tests" in str(py_file) or "data" in str(py_file):
            continue
        
        total_files += 1
        fixed_files += fix_logging_in_file(py_file, args.dry_run)

    print()
    print(f"Total files scanned: {total_files}")
    print(f"Files {'would be ' if args.dry_run else ''}fixed: {fixed_files}")

    if args.dry_run:
        print()
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
