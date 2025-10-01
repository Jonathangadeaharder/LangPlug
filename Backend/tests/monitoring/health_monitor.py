"""
Test Health Metrics Dashboard System
Provides automated test execution monitoring and health tracking
"""

import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class TestResult:
    """Individual test execution result"""

    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: str | None = None
    service_name: str | None = None


@dataclass
class TestRunMetrics:
    """Complete test run metrics"""

    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_duration: float
    success_rate: float
    test_results: list[TestResult]
    service_breakdown: dict[str, dict[str, int]]  # service -> {passed, failed, etc}
    slow_tests: list[TestResult]  # tests over threshold
    pollution_detected: bool
    mock_isolation_issues: list[str]


@dataclass
class HealthTrend:
    """Health trend analysis"""

    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # up, down, stable


class TestHealthMonitor:
    """Automated test execution monitoring and health dashboard system"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(self.project_root) / "tests" / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Performance thresholds
        self.slow_test_threshold = 2.0  # seconds
        self.success_rate_threshold = 95.0  # percentage
        self.max_test_duration = 30.0  # seconds

        # Critical services for monitoring
        self.critical_services = [
            "AuthService",
            "VideoService",
            "UserVocabularyService",
            "LoggingService",
            "DirectSubtitleProcessor",
        ]

    def run_tests_with_monitoring(self) -> TestRunMetrics:
        """Execute tests with comprehensive monitoring"""
        print("[INFO] Starting monitored test execution...")

        start_time = time.time()

        # Run tests with detailed output
        cmd = [
            "powershell.exe",
            "-Command",
            "api_venv\\Scripts\\python.exe -m pytest -v --tb=short --durations=0 --junit-xml=tests/reports/junit_results.xml tests/unit/",
        ]

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
            )

            total_duration = time.time() - start_time

            # Parse test output
            test_results = self._parse_pytest_output(result.stdout)

            # Check for pollution and isolation issues
            pollution_detected, isolation_issues = self._check_test_pollution(result.stdout)

            # Calculate metrics
            metrics = self._calculate_test_metrics(test_results, total_duration, pollution_detected, isolation_issues)

            print(f"[INFO] Test execution completed in {total_duration:.2f}s")
            return metrics

        except subprocess.TimeoutExpired:
            print("[WARN] Test execution timed out")
            return self._create_timeout_metrics()
        except Exception as e:
            print(f"[ERROR] Test execution failed: {e}")
            return self._create_error_metrics()

    def _parse_pytest_output(self, output: str) -> list[TestResult]:
        """Parse pytest verbose output to extract test results"""
        test_results = []

        # Look for test result lines like:
        # tests/unit/services/test_auth_service.py::TestAuthServiceRegistration::test_register_user_success PASSED [  5%]
        test_pattern = r"([^:]+)::([\w:]+)\s+(PASSED|FAILED|SKIPPED|ERROR)\s+\[.*?\](?:\s+(.+))?"

        for match in re.finditer(test_pattern, output, re.MULTILINE):
            file_path, test_class_method, status, error_msg = match.groups()

            # Extract service name from file path
            service_name = self._extract_service_from_path(file_path)

            # Extract test name
            test_name = f"{test_class_method}"

            test_results.append(
                TestResult(
                    test_name=test_name,
                    status=status.lower(),
                    duration=0.0,  # Will be updated if duration info is found
                    error_message=error_msg.strip() if error_msg else None,
                    service_name=service_name,
                )
            )

        return test_results

    def _extract_service_from_path(self, file_path: str) -> str | None:
        """Extract service name from test file path"""
        if "test_auth_service" in file_path:
            return "AuthService"
        elif "test_video_service" in file_path:
            return "VideoService"
        elif "test_user_vocabulary" in file_path:
            return "UserVocabularyService"
        elif "test_logging" in file_path:
            return "LoggingService"
        elif "test_subtitle" in file_path:
            return "DirectSubtitleProcessor"
        return None

    def _check_test_pollution(self, output: str) -> tuple[bool, list[str]]:
        """Check for test pollution and mock isolation issues"""
        pollution_indicators = [
            "database is locked",
            "transaction already closed",
            "session already closed",
            "mock object leaked",
            "fixture teardown failed",
        ]

        issues = []
        for indicator in pollution_indicators:
            if indicator.lower() in output.lower():
                issues.append(indicator)

        return len(issues) > 0, issues

    def _calculate_test_metrics(
        self, test_results: list[TestResult], duration: float, pollution: bool, isolation_issues: list[str]
    ) -> TestRunMetrics:
        """Calculate comprehensive test metrics"""

        # Count by status
        passed = sum(1 for t in test_results if t.status == "passed")
        failed = sum(1 for t in test_results if t.status == "failed")
        skipped = sum(1 for t in test_results if t.status == "skipped")
        errors = sum(1 for t in test_results if t.status == "error")

        total = len(test_results)
        success_rate = (passed / total * 100) if total > 0 else 0

        # Service breakdown
        service_breakdown = {}
        for service in self.critical_services:
            service_tests = [t for t in test_results if t.service_name == service]
            if service_tests:
                service_breakdown[service] = {
                    "passed": sum(1 for t in service_tests if t.status == "passed"),
                    "failed": sum(1 for t in service_tests if t.status == "failed"),
                    "skipped": sum(1 for t in service_tests if t.status == "skipped"),
                    "errors": sum(1 for t in service_tests if t.status == "error"),
                    "total": len(service_tests),
                }

        # Identify slow tests (placeholder - actual duration parsing would be more complex)
        slow_tests = [t for t in test_results if t.duration > self.slow_test_threshold]

        return TestRunMetrics(
            timestamp=datetime.now().isoformat(),
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            total_duration=duration,
            success_rate=success_rate,
            test_results=test_results,
            service_breakdown=service_breakdown,
            slow_tests=slow_tests,
            pollution_detected=pollution,
            mock_isolation_issues=isolation_issues,
        )

    def _create_timeout_metrics(self) -> TestRunMetrics:
        """Create metrics for timeout scenario"""
        return TestRunMetrics(
            timestamp=datetime.now().isoformat(),
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            total_duration=300.0,
            success_rate=0.0,
            test_results=[],
            service_breakdown={},
            slow_tests=[],
            pollution_detected=False,
            mock_isolation_issues=["Test execution timed out"],
        )

    def _create_error_metrics(self) -> TestRunMetrics:
        """Create metrics for error scenario"""
        return TestRunMetrics(
            timestamp=datetime.now().isoformat(),
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            total_duration=0.0,
            success_rate=0.0,
            test_results=[],
            service_breakdown={},
            slow_tests=[],
            pollution_detected=False,
            mock_isolation_issues=["Test execution failed"],
        )

    def save_metrics(self, metrics: TestRunMetrics) -> Path:
        """Save test metrics to disk"""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.reports_dir / f"health_metrics_{timestamp_str}.json"

        # Convert to dict for JSON serialization
        metrics_dict = asdict(metrics)

        with open(metrics_file, "w") as f:
            json.dump(metrics_dict, f, indent=2)

        print(f"[INFO] Health metrics saved: {metrics_file}")
        return metrics_file

    def analyze_trends(self, lookback_days: int = 7) -> list[HealthTrend]:
        """Analyze health trends over time"""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Find recent metrics files
        metrics_files = []
        for file_path in self.reports_dir.glob("health_metrics_*.json"):
            try:
                # Extract timestamp from filename
                timestamp_str = file_path.stem.replace("health_metrics_", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                if file_date >= cutoff_date:
                    metrics_files.append((file_date, file_path))
            except ValueError:
                continue

        if len(metrics_files) < 2:
            return []

        # Sort by date
        metrics_files.sort()

        # Load latest two metrics for trend analysis
        latest_metrics = self._load_metrics(metrics_files[-1][1])
        previous_metrics = self._load_metrics(metrics_files[-2][1])

        if not latest_metrics or not previous_metrics:
            return []

        trends = []

        # Success rate trend
        success_trend = self._calculate_trend(
            "success_rate", latest_metrics.get("success_rate", 0), previous_metrics.get("success_rate", 0)
        )
        trends.append(success_trend)

        # Test duration trend
        duration_trend = self._calculate_trend(
            "test_duration", latest_metrics.get("total_duration", 0), previous_metrics.get("total_duration", 0)
        )
        trends.append(duration_trend)

        # Failed tests trend
        failed_trend = self._calculate_trend(
            "failed_tests", latest_metrics.get("failed", 0), previous_metrics.get("failed", 0)
        )
        trends.append(failed_trend)

        return trends

    def _load_metrics(self, file_path: Path) -> dict | None:
        """Load metrics from JSON file"""
        try:
            with open(file_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load metrics from {file_path}: {e}")
            return None

    def _calculate_trend(self, metric_name: str, current: float, previous: float) -> HealthTrend:
        """Calculate trend for a metric"""
        change_percentage = (100.0 if current > 0 else 0.0) if previous == 0 else (current - previous) / previous * 100

        if abs(change_percentage) < 5:
            direction = "stable"
        elif change_percentage > 0:
            direction = "up"
        else:
            direction = "down"

        return HealthTrend(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            change_percentage=change_percentage,
            trend_direction=direction,
        )

    def generate_health_dashboard(self, metrics: TestRunMetrics, trends: list[HealthTrend]) -> str:
        """Generate comprehensive health dashboard"""

        # Status indicators
        success_indicator = "[GOOD]" if metrics.success_rate >= self.success_rate_threshold else "[POOR]"
        duration_indicator = "[GOOD]" if metrics.total_duration < 60 else "[SLOW]"
        pollution_indicator = "[CLEAN]" if not metrics.pollution_detected else "[POLLUTED]"

        dashboard = f"""# Test Health Dashboard
Generated: {metrics.timestamp}

## Overall Health Status
- **Test Success Rate**: {success_indicator} {metrics.success_rate:.1f}%
- **Execution Time**: {duration_indicator} {metrics.total_duration:.2f}s
- **Test Pollution**: {pollution_indicator}
- **Mock Isolation**: {"[OK]" if not metrics.mock_isolation_issues else "[ISSUES]"}

## Test Execution Summary
- **Total Tests**: {metrics.total_tests}
- **Passed**: {metrics.passed} ({(metrics.passed / metrics.total_tests * 100):.1f}%)
- **Failed**: {metrics.failed} ({(metrics.failed / metrics.total_tests * 100):.1f}%)
- **Skipped**: {metrics.skipped} ({(metrics.skipped / metrics.total_tests * 100):.1f}%)
- **Errors**: {metrics.errors} ({(metrics.errors / metrics.total_tests * 100):.1f}%)

## Service-Level Health
"""

        for service, breakdown in metrics.service_breakdown.items():
            total = breakdown["total"]
            passed = breakdown["passed"]
            failed = breakdown["failed"]
            service_rate = (passed / total * 100) if total > 0 else 0
            service_status = "[GOOD]" if service_rate >= 80 else "[FAIR]" if service_rate >= 60 else "[POOR]"

            dashboard += f"""
### {service_status} {service}
- **Tests**: {total}
- **Success Rate**: {service_rate:.1f}%
- **Passed**: {passed}, **Failed**: {failed}
- **Skipped**: {breakdown["skipped"]}, **Errors**: {breakdown["errors"]}"""

        # Trends section
        if trends:
            dashboard += "\n\n## Health Trends\n"
            for trend in trends:
                direction_emoji = {"up": "[UP]", "down": "[DOWN]", "stable": "[STABLE]"}
                dashboard += f"- **{trend.metric_name.replace('_', ' ').title()}**: {direction_emoji[trend.trend_direction]} {trend.change_percentage:+.1f}%\n"

        # Issues section
        if metrics.mock_isolation_issues:
            dashboard += "\n## Mock Isolation Issues\n"
            for issue in metrics.mock_isolation_issues:
                dashboard += f"- {issue}\n"

        # Slow tests section
        if metrics.slow_tests:
            dashboard += f"\n## Slow Tests (>{self.slow_test_threshold}s)\n"
            for test in metrics.slow_tests[:5]:  # Top 5
                dashboard += f"- **{test.test_name}**: {test.duration:.2f}s\n"

        # Failed tests details
        failed_tests = [t for t in metrics.test_results if t.status == "failed"]
        if failed_tests:
            dashboard += "\n## Failed Tests Details\n"
            for test in failed_tests:
                dashboard += f"""
### {test.test_name}
- **Service**: {test.service_name or "Unknown"}
- **Error**: {test.error_message or "No error message"}
"""

        dashboard += f"\n---\n*Dashboard generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return dashboard


def main():
    """Main health monitoring function"""
    monitor = TestHealthMonitor()

    print("[INFO] Starting test health monitoring...")

    # Run tests with monitoring
    metrics = monitor.run_tests_with_monitoring()

    # Save metrics
    monitor.save_metrics(metrics)

    # Analyze trends
    trends = monitor.analyze_trends()

    # Generate dashboard
    dashboard = monitor.generate_health_dashboard(metrics, trends)
    dashboard_file = monitor.reports_dir / "health_dashboard.md"

    with open(dashboard_file, "w", encoding="utf-8") as f:
        f.write(dashboard)

    print(f"[INFO] Health dashboard generated: {dashboard_file}")
    print("\n" + "=" * 50)
    print(dashboard)


if __name__ == "__main__":
    main()
