#!/usr/bin/env python3
"""
Unified Backend Test Runner

Provides single entry point for all backend tests with structured reporting.
Replaces ad-hoc test scripts with proper test orchestration.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add Backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@dataclass
class TestResult:
    """Structured test result"""

    name: str
    status: str  # "passed", "failed", "skipped"
    duration: float
    details: str | None = None
    error: str | None = None


@dataclass
class TestSuite:
    """Test suite configuration"""

    name: str
    path: str
    pattern: str
    description: str
    required: bool = True


class BackendTestRunner:
    """Unified backend test runner with structured reporting"""

    def __init__(self, verbose: bool = False, output_format: str = "console"):
        self.verbose = verbose
        self.output_format = output_format
        self.results: list[TestResult] = []
        self.start_time = 0.0

        # Define test suites
        self.test_suites = [
            TestSuite(
                name="unit",
                path="tests/unit",
                pattern="test_*.py",
                description="Unit tests - isolated component testing",
                required=True,
            ),
            TestSuite(
                name="api",
                path="tests/api",
                pattern="test_*.py",
                description="API endpoint tests - request/response validation",
                required=True,
            ),
            TestSuite(
                name="integration",
                path="tests/integration",
                pattern="test_*.py",
                description="Integration tests - component interaction testing",
                required=False,
            ),
            TestSuite(
                name="security",
                path="tests/security",
                pattern="test_*.py",
                description="Security tests - vulnerability and access control testing",
                required=False,
            ),
            TestSuite(
                name="performance",
                path="tests/performance",
                pattern="test_*.py",
                description="Performance tests - load and response time testing",
                required=False,
            ),
        ]

    def run_all_tests(self, suites: list[str] | None = None, coverage: bool = False) -> bool:
        """Run all test suites and return overall success status"""
        self.start_time = time.time()

        print("[INFO] Starting Backend Test Suite")
        print("=" * 60)

        # Determine which suites to run
        suites_to_run = self.test_suites
        if suites:
            suites_to_run = [s for s in self.test_suites if s.name in suites]

        overall_success = True

        for suite in suites_to_run:
            print(f"\n[RUN] {suite.name.upper()}: {suite.description}")
            success = self.run_test_suite(suite, coverage)

            if not success:
                overall_success = False
                if suite.required:
                    print(f"[ERROR] Required test suite '{suite.name}' failed")

        # Generate reports
        self.generate_summary_report()

        if self.output_format == "junit":
            self.generate_junit_report()
        elif self.output_format == "json":
            self.generate_json_report()

        return overall_success

    def run_test_suite(self, suite: TestSuite, coverage: bool = False) -> bool:
        """Run a specific test suite"""
        suite_path = Path(backend_path) / suite.path

        if not suite_path.exists():
            print(f"[WARN] Test suite path does not exist: {suite_path}")
            self.results.append(
                TestResult(name=suite.name, status="skipped", duration=0.0, details=f"Path not found: {suite_path}")
            )
            return True  # Not a failure if optional

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add coverage if requested
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=json:coverage.json"])

        # Add verbose output if requested
        if self.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Add test path
        cmd.append(str(suite_path))

        # Add structured output
        cmd.extend(["--tb=short", "--disable-warnings"])

        try:
            start_time = time.time()

            if self.verbose:
                print(f"[DEBUG] Running: {' '.join(cmd)}")

            # Run pytest
            result = subprocess.run(
                cmd,
                check=False,
                cwd=backend_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per suite
            )

            duration = time.time() - start_time

            # Parse pytest output
            success = result.returncode == 0
            status = "passed" if success else "failed"

            # Extract test counts from pytest output
            output_lines = result.stdout.split("\n")
            summary_line = ""
            for line in output_lines:
                if "failed" in line or "passed" in line or "error" in line:
                    if any(word in line for word in ["failed,", "passed,", "error,"]):
                        summary_line = line.strip()
                        break

            details = summary_line or f"Suite completed in {duration:.2f}s"
            error = result.stderr if result.stderr and not success else None

            self.results.append(
                TestResult(name=suite.name, status=status, duration=duration, details=details, error=error)
            )

            # Print immediate feedback
            status_symbol = "PASS" if success else "FAIL"
            print(f"[{status_symbol}] {suite.name}: {details}")

            if not success and self.verbose:
                print(f"[DEBUG] STDOUT:\n{result.stdout}")
                print(f"[DEBUG] STDERR:\n{result.stderr}")

            return success

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Test suite '{suite.name}' timed out after 5 minutes")
            self.results.append(
                TestResult(name=suite.name, status="failed", duration=300.0, error="Test suite timed out")
            )
            return False

        except Exception as e:
            print(f"[ERROR] Failed to run test suite '{suite.name}': {e}")
            self.results.append(TestResult(name=suite.name, status="failed", duration=0.0, error=str(e)))
            return False

    def generate_summary_report(self) -> None:
        """Generate human-readable summary report"""
        total_duration = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("BACKEND TEST SUMMARY")
        print("=" * 60)

        # Count results by status
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        total = len(self.results)

        print(f"Total Suites: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Duration: {total_duration:.2f}s")

        # Show details for each suite
        print("\nSUITE DETAILS:")
        for result in self.results:
            status_symbol = {"passed": "[PASS]", "failed": "[FAIL]", "skipped": "[SKIP]"}[result.status]
            print(f"  {status_symbol} {result.name:12} | {result.duration:6.2f}s | {result.details or 'No details'}")

            if result.error and self.verbose:
                print(f"    Error: {result.error}")

        # Overall status
        overall_status = "PASSED" if failed == 0 else "FAILED"
        print(f"\nOVERALL STATUS: {overall_status}")

    def generate_junit_report(self) -> None:
        """Generate JUnit XML report for CI integration"""
        try:
            from xml.dom.minidom import parseString
            from xml.etree.ElementTree import Element, SubElement, tostring

            # Create root element
            testsuites = Element("testsuites")
            testsuites.set("name", "backend-tests")
            testsuites.set("tests", str(len(self.results)))
            testsuites.set("failures", str(sum(1 for r in self.results if r.status == "failed")))
            testsuites.set("time", f"{time.time() - self.start_time:.3f}")

            # Add each test suite
            for result in self.results:
                testsuite = SubElement(testsuites, "testsuite")
                testsuite.set("name", result.name)
                testsuite.set("tests", "1")
                testsuite.set("failures", "1" if result.status == "failed" else "0")
                testsuite.set("time", f"{result.duration:.3f}")

                testcase = SubElement(testsuite, "testcase")
                testcase.set("name", result.name)
                testcase.set("classname", f"backend.{result.name}")
                testcase.set("time", f"{result.duration:.3f}")

                if result.status == "failed":
                    failure = SubElement(testcase, "failure")
                    failure.set("message", result.details or "Test suite failed")
                    failure.text = result.error or "No error details"
                elif result.status == "skipped":
                    skipped = SubElement(testcase, "skipped")
                    skipped.set("message", result.details or "Test suite skipped")

            # Write to file
            rough_string = tostring(testsuites, "utf-8")
            reparsed = parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            with open("test-results-backend.xml", "w") as f:
                f.write(pretty_xml)

            print("[INFO] JUnit report written to test-results-backend.xml")

        except Exception as e:
            print(f"[WARN] Could not generate JUnit report: {e}")

    def generate_json_report(self) -> None:
        """Generate JSON report for programmatic consumption"""
        try:
            report = {
                "timestamp": time.time(),
                "duration": time.time() - self.start_time,
                "summary": {
                    "total": len(self.results),
                    "passed": sum(1 for r in self.results if r.status == "passed"),
                    "failed": sum(1 for r in self.results if r.status == "failed"),
                    "skipped": sum(1 for r in self.results if r.status == "skipped"),
                },
                "suites": [
                    {"name": r.name, "status": r.status, "duration": r.duration, "details": r.details, "error": r.error}
                    for r in self.results
                ],
            }

            with open("test-results-backend.json", "w") as f:
                json.dump(report, f, indent=2)

            print("[INFO] JSON report written to test-results-backend.json")

        except Exception as e:
            print(f"[WARN] Could not generate JSON report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run backend test suites")
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["unit", "api", "integration", "security", "performance"],
        help="Test suites to run (default: all)",
    )
    parser.add_argument("--coverage", action="store_true", help="Generate test coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--format", choices=["console", "junit", "json"], default="console", help="Output format")

    args = parser.parse_args()

    # Create and run test runner
    runner = BackendTestRunner(verbose=args.verbose, output_format=args.format)
    success = runner.run_all_tests(suites=args.suites, coverage=args.coverage)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
