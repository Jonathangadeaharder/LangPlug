#!/usr/bin/env python3
"""Simple test to check if pytest works without venv_activator interference."""

import sys
import subprocess

def test_pytest():
    try:
        # Try to run pytest --version
        result = subprocess.run([sys.executable, '-m', 'pytest', '--version'],
                              capture_output=True, text=True, timeout=30)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

if __name__ == "__main__":
    success = test_pytest()
    print(f"Pytest test {'PASSED' if success else 'FAILED'}")