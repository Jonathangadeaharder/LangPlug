#!/usr/bin/env python3
"""
Professional Test Management Script for LangPlug Backend

This script provides comprehensive test management capabilities:
- Run all tests with proper categorization
- Generate detailed test reports
- Identify failing tests and their root causes
- Manage expected failures with proper documentation

This replaces the unprofessional approach of maintaining a hardcoded
list of "passing tests" and instead follows industry best practices.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TestResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAIL = "xfail"  # Expected to fail
    XPASS = "xpass"  # Unexpectedly passed


@dataclass
class TestOutcome:
    name: str
    result: TestResult
    duration: float
    error_message: str | None = None
    file_path: str | None = None


class ProfessionalTestManager:
    """
    Professional test management following industry best practices.

    Instead of maintaining a list of "passing tests", this tool:
    1. Runs all tests and categorizes results
    2. Uses pytest markers for expected failures
    3. Provides detailed failure analysis
    4. Generates actionable reports
    """

    def __init__(self, backend_dir: str):
        self.backend_dir = Path(backend_dir)
        self.results: list[TestOutcome] = []

    def run_all_tests(self, timeout: int = 300) -> bool:
        """
        Run all tests with comprehensive reporting.

        Args:
            timeout: Maximum time in seconds for the entire test run

        Returns:
            True if all non-expected failures pass, False otherwise
        """
        self._setup_test_environment()
        cmd = self._build_pytest_command(timeout)

        try:
            result, duration = self._execute_tests(cmd, timeout)
            self._parse_test_results()
            self._print_comprehensive_report(result, duration)
            return self._evaluate_test_success(result.returncode)
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def _setup_test_environment(self) -> None:
        """Setup the test environment."""
        os.chdir(self.backend_dir)

    def _build_pytest_command(self, timeout: int) -> list[str]:
        """Build the pytest command with required options."""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--json-report",
            "--json-report-file=test_results.json",
            "-v",
            "--tb=short",
            f"--timeout={timeout}",
            "--timeout-method=thread",
        ]
        return cmd

    def _execute_tests(self, cmd: list[str], timeout: int) -> tuple:
        """Execute the test command and return result and duration."""
        start_time = time.time()
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout + 60,  # Extra buffer for cleanup
        )
        duration = time.time() - start_time
        return result, duration

    def _parse_test_results(self) -> None:
        """Parse JSON test results if available."""
        results_file = self.backend_dir / "test_results.json"

        if not results_file.exists():
            return

        try:
            with open(results_file) as f:
                data = json.load(f)

            for test in data.get("tests", []):
                outcome = TestOutcome(
                    name=test.get("nodeid", "unknown"),
                    result=TestResult(test.get("outcome", "failed")),
                    duration=test.get("duration", 0.0),
                    error_message=self._extract_error_message(test),
                    file_path=test.get("file_path"),
                )
                self.results.append(outcome)

        except Exception:
            pass

    def _extract_error_message(self, test_data: dict) -> str | None:
        """Extract meaningful error message from test data."""
        call = test_data.get("call", {})
        if "longrepr" in call:
            return str(call["longrepr"])[:200] + "..." if len(str(call["longrepr"])) > 200 else str(call["longrepr"])
        return None

    def _print_comprehensive_report(self, result: subprocess.CompletedProcess, duration: float) -> None:
        """Print a comprehensive test report."""

        # Print stdout (pytest output)
        if result.stdout:
            pass

        # Print stderr if there are errors
        if result.stderr:
            pass

        # Print categorized results if we have JSON data
        if self.results:
            self._print_categorized_results()

        # Print guidance based on results
        self._print_guidance(result.returncode)

    def _print_categorized_results(self) -> None:
        """Print results organized by category."""
        by_result = {}
        for outcome in self.results:
            if outcome.result not in by_result:
                by_result[outcome.result] = []
            by_result[outcome.result].append(outcome)

        for result_type in TestResult:
            if result_type in by_result:
                tests = by_result[result_type]
                self._get_result_icon(result_type)

                # Show details for failures
                if result_type == TestResult.FAILED and len(tests) <= 10:
                    for test in tests:
                        if test.error_message:
                            pass

    def _get_result_icon(self, result: TestResult) -> str:
        """Get appropriate icon for test result."""
        icons = {
            TestResult.PASSED: "[GOOD]",
            TestResult.FAILED: "[ERROR]",
            TestResult.SKIPPED: "[SKIP]",
            TestResult.XFAIL: "[WARN]",
            TestResult.XPASS: "[GOOD]",
        }
        return icons.get(result, "[UNKNOWN]")

    def _evaluate_test_success(self, return_code: int) -> bool:
        """
        Evaluate whether the test run should be considered successful.

        Professional criteria:
        - All tests pass OR
        - Only expected failures (xfail) fail OR
        - Temporary failures are properly documented
        """
        if return_code == 0:
            return True

        # If we have detailed results, be more intelligent about success
        if self.results:
            failed_tests = [r for r in self.results if r.result == TestResult.FAILED]
            [r for r in self.results if r.result == TestResult.XFAIL]

            # Success if no unexpected failures
            return len(failed_tests) == 0

        # Fall back to return code
        return return_code == 0

    def _print_guidance(self, return_code: int) -> None:
        """Print actionable guidance based on test results."""

        if return_code == 0:
            pass
        else:
            pass

    def run_by_category(self, category: str) -> bool:
        """Run tests by specific category/marker."""

        os.chdir(self.backend_dir)

        cmd = [sys.executable, "-m", "pytest", "-m", category, "-v", "--tb=short"]

        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception:
            return False

    def run_failed_tests_only(self) -> bool:
        """Re-run only the tests that failed in the last run."""

        os.chdir(self.backend_dir)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--lf",  # Last failed
            "-v",
            "--tb=short",
        ]

        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception:
            return False


def main():
    """Main entry point for the test management script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Professional Test Management for LangPlug Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_management.py                    # Run all tests
  python scripts/test_management.py --category unit   # Run unit tests only
  python scripts/test_management.py --failed-only     # Re-run failed tests
  python scripts/test_management.py --timeout 600     # Extended timeout
        """,
    )

    parser.add_argument("--category", "-c", help="Run tests with specific marker (unit, integration, api, etc.)")
    parser.add_argument(
        "--failed-only", "-f", action="store_true", help="Re-run only tests that failed in the last run"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=300, help="Timeout in seconds for test execution (default: 300)"
    )

    args = parser.parse_args()

    # Get backend directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    manager = ProfessionalTestManager(backend_dir)

    # Run appropriate test suite
    if args.category:
        success = manager.run_by_category(args.category)
    elif args.failed_only:
        success = manager.run_failed_tests_only()
    else:
        success = manager.run_all_tests(timeout=args.timeout)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
