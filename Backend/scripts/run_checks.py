#!/usr/bin/env python3
"""
Unified cross-platform code quality checks script.
Replaces run_checks.bat and run_checks.sh with a single Python solution.

Usage:
    python run_checks.py [--lint-only] [--format-only] [--test-only] [--fix]

    --lint-only    Run only linting checks
    --format-only  Run only code formatting
    --test-only    Run only tests
    --fix          Automatically fix linting and formatting issues
"""

import argparse
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for cross-platform colored output."""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    @classmethod
    def info(cls, msg):
        pass

    @classmethod
    def success(cls, msg):
        pass

    @classmethod
    def warning(cls, msg):
        pass

    @classmethod
    def error(cls, msg):
        pass


class CodeQualityChecker:
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.failed_checks = []

    def run_command(self, cmd, description):
        """Run a command and track failures."""
        Colors.info(f"{description}...")
        try:
            subprocess.run(cmd, cwd=self.backend_dir, check=True, capture_output=True, text=True)
            Colors.success(f"{description} passed")
            return True
        except subprocess.CalledProcessError as e:
            Colors.error(f"{description} failed")
            if e.stdout:
                pass
            if e.stderr:
                pass
            self.failed_checks.append(description)
            return False
        except FileNotFoundError:
            Colors.error(f"{description} failed - command not found: {cmd[0]}")
            Colors.warning("Make sure the required tools are installed in your virtual environment")
            self.failed_checks.append(description)
            return False

    def run_linting(self, fix=False):
        """Run Ruff linting checks."""
        cmd = ["python", "-m", "ruff", "check", "."]
        if fix:
            cmd.append("--fix")
        return self.run_command(cmd, "Ruff linting")

    def run_formatting(self, fix=False):
        """Run Ruff code formatting."""
        if fix:
            cmd = ["python", "-m", "ruff", "format", "."]
            description = "Ruff formatting (applying fixes)"
        else:
            cmd = ["python", "-m", "ruff", "format", "--check", "."]
            description = "Ruff formatting (check only)"
        return self.run_command(cmd, description)

    def run_tests(self):
        """Run pytest with appropriate filters."""
        cmd = ["python", "-m", "pytest", "-q", "-m", "not slow and not performance"]
        return self.run_command(cmd, "Running tests")

    def run_type_checking(self):
        """Run mypy type checking if available."""
        cmd = ["python", "-m", "mypy", ".", "--ignore-missing-imports"]
        return self.run_command(cmd, "Type checking (mypy)")

    def print_summary(self):
        """Print summary of check results."""
        if not self.failed_checks:
            Colors.success("All code quality checks passed! ✅")
        else:
            Colors.error(f"Failed checks ({len(self.failed_checks)}):")
            for _check in self.failed_checks:
                pass
            Colors.warning("Please fix the issues above before committing.")


def main():
    parser = argparse.ArgumentParser(
        description="Run code quality checks for the backend", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--lint-only", action="store_true", help="Run only linting checks")
    parser.add_argument("--format-only", action="store_true", help="Run only code formatting checks")
    parser.add_argument("--test-only", action="store_true", help="Run only tests")
    parser.add_argument("--type-only", action="store_true", help="Run only type checking")
    parser.add_argument("--fix", action="store_true", help="Automatically fix linting and formatting issues")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")

    args = parser.parse_args()

    checker = CodeQualityChecker()

    try:
        # Determine what checks to run
        run_all = not any([args.lint_only, args.format_only, args.test_only, args.type_only])

        if args.lint_only or run_all:
            checker.run_linting(fix=args.fix)

        if args.format_only or run_all:
            checker.run_formatting(fix=args.fix)

        if args.type_only or run_all:
            # Type checking is optional - don't fail if mypy is not installed
            try:
                checker.run_type_checking()
            except Exception:
                Colors.warning("Type checking skipped (mypy not available)")

        if (args.test_only or run_all) and not args.no_tests:
            checker.run_tests()

        checker.print_summary()

        # Exit with error code if any checks failed
        if checker.failed_checks:
            sys.exit(1)

    except KeyboardInterrupt:
        Colors.warning("Checks interrupted by user")
        sys.exit(1)
    except Exception as e:
        Colors.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
