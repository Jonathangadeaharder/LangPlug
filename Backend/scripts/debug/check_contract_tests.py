#!/usr/bin/env python3
"""
Simple script to check if contract tests can be imported and run
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    try:
        import tests.run_contract_tests

        result = tests.run_contract_tests.main()
        return result
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
