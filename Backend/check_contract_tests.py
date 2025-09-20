#!/usr/bin/env python3
"""
Simple script to check if contract tests can be imported and run
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("Checking contract tests...")
    try:
        import tests.run_contract_tests
        print("Contract tests module imported successfully")
        print("Attempting to run main function...")
        result = tests.run_contract_tests.main()
        print(f"Contract tests completed with result: {result}")
        return result
    except Exception as e:
        print(f"Error running contract tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())