"""
Infrastructure Quality Gates System
Enforces test quality standards and prevents degradation
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class QualityThreshold:
    """Quality threshold configuration"""

    name: str
    current_value: float
    threshold_value: float
    direction: str  # 'above' or 'below'
    severity: str  # 'error', 'warning'
    message: str


@dataclass
class QualityViolation:
    """Quality gate violation"""

    gate_name: str
    threshold: QualityThreshold
    current_value: float
    expected_value: float
    severity: str
    message: str


class QualityGateChecker:
    """Automated quality gate enforcement system"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(self.project_root) / "tests" / "reports"

        # Define quality gates with thresholds
        self.quality_gates = {
            "minimum_coverage": QualityThreshold(
                name="Minimum Test Coverage",
                current_value=0.0,  # Will be updated dynamically
                threshold_value=25.0,
                direction="above",
                severity="error",
                message="Overall test coverage must be at least 25%",
            ),
            "critical_service_coverage": QualityThreshold(
                name="Critical Service Coverage",
                current_value=0.0,
                threshold_value=30.0,
                direction="above",
                severity="warning",
                message="Critical services should have at least 30% coverage",
            ),
            "test_success_rate": QualityThreshold(
                name="Test Success Rate",
                current_value=0.0,
                threshold_value=95.0,
                direction="above",
                severity="error",
                message="Test success rate must be at least 95%",
            ),
            "max_test_execution_time": QualityThreshold(
                name="Test Execution Performance",
                current_value=0.0,
                threshold_value=120.0,  # 2 minutes
                direction="below",
                severity="warning",
                message="Test suite should complete within 2 minutes",
            ),
            "no_test_pollution": QualityThreshold(
                name="Test Isolation",
                current_value=0.0,  # 0 = clean, 1 = polluted
                threshold_value=0.0,
                direction="below",
                severity="error",
                message="No test pollution or mock isolation issues allowed",
            ),
            "mock_isolation_compliance": QualityThreshold(
                name="Mock Isolation",
                current_value=0.0,
                threshold_value=0.0,
                direction="below",
                severity="error",
                message="All tests must have proper mock isolation",
            ),
        }

        # Critical services that must meet higher standards
        self.critical_services = ["AuthService", "VideoService", "UserVocabularyService"]

    def check_coverage_gates(self) -> list[QualityViolation]:
        """Check coverage-related quality gates"""
        violations = []

        # Load latest coverage report
        coverage_report = self._load_latest_coverage_report()
        if not coverage_report:
            violations.append(
                QualityViolation(
                    gate_name="coverage_data",
                    threshold=self.quality_gates["minimum_coverage"],
                    current_value=0.0,
                    expected_value=25.0,
                    severity="error",
                    message="No coverage data available - tests may not be running",
                )
            )
            return violations

        # Check overall coverage
        total_coverage = coverage_report.get("total_coverage", 0.0)
        min_coverage_gate = self.quality_gates["minimum_coverage"]
        min_coverage_gate.current_value = total_coverage

        if total_coverage < min_coverage_gate.threshold_value:
            violations.append(
                QualityViolation(
                    gate_name="minimum_coverage",
                    threshold=min_coverage_gate,
                    current_value=total_coverage,
                    expected_value=min_coverage_gate.threshold_value,
                    severity=min_coverage_gate.severity,
                    message=f"Coverage {total_coverage:.1f}% is below minimum {min_coverage_gate.threshold_value}%",
                )
            )

        # Check critical service coverage
        service_coverage = coverage_report.get("service_coverage", [])
        critical_gate = self.quality_gates["critical_service_coverage"]

        for service in service_coverage:
            if service["service_name"] in self.critical_services:
                coverage_pct = service["coverage_percentage"]
                if coverage_pct < critical_gate.threshold_value:
                    violations.append(
                        QualityViolation(
                            gate_name="critical_service_coverage",
                            threshold=critical_gate,
                            current_value=coverage_pct,
                            expected_value=critical_gate.threshold_value,
                            severity=critical_gate.severity,
                            message=f"{service['service_name']} coverage {coverage_pct:.1f}% below critical threshold {critical_gate.threshold_value}%",
                        )
                    )

        return violations

    def check_health_gates(self) -> list[QualityViolation]:
        """Check health-related quality gates"""
        violations = []

        # Load latest health metrics
        health_metrics = self._load_latest_health_metrics()
        if not health_metrics:
            violations.append(
                QualityViolation(
                    gate_name="health_data",
                    threshold=self.quality_gates["test_success_rate"],
                    current_value=0.0,
                    expected_value=95.0,
                    severity="error",
                    message="No health metrics available - tests may not be running",
                )
            )
            return violations

        # Check test success rate
        success_rate = health_metrics.get("success_rate", 0.0)
        success_gate = self.quality_gates["test_success_rate"]
        success_gate.current_value = success_rate

        if success_rate < success_gate.threshold_value:
            violations.append(
                QualityViolation(
                    gate_name="test_success_rate",
                    threshold=success_gate,
                    current_value=success_rate,
                    expected_value=success_gate.threshold_value,
                    severity=success_gate.severity,
                    message=f"Test success rate {success_rate:.1f}% is below required {success_gate.threshold_value}%",
                )
            )

        # Check test execution time
        execution_time = health_metrics.get("total_duration", 0.0)
        time_gate = self.quality_gates["max_test_execution_time"]
        time_gate.current_value = execution_time

        if execution_time > time_gate.threshold_value:
            violations.append(
                QualityViolation(
                    gate_name="max_test_execution_time",
                    threshold=time_gate,
                    current_value=execution_time,
                    expected_value=time_gate.threshold_value,
                    severity=time_gate.severity,
                    message=f"Test execution time {execution_time:.1f}s exceeds limit {time_gate.threshold_value}s",
                )
            )

        # Check for test pollution
        pollution_detected = health_metrics.get("pollution_detected", False)
        pollution_gate = self.quality_gates["no_test_pollution"]
        pollution_gate.current_value = 1.0 if pollution_detected else 0.0

        if pollution_detected:
            violations.append(
                QualityViolation(
                    gate_name="no_test_pollution",
                    threshold=pollution_gate,
                    current_value=1.0,
                    expected_value=0.0,
                    severity=pollution_gate.severity,
                    message="Test pollution detected - database state or mock leakage found",
                )
            )

        # Check mock isolation issues
        isolation_issues = health_metrics.get("mock_isolation_issues", [])
        isolation_gate = self.quality_gates["mock_isolation_compliance"]
        isolation_gate.current_value = len(isolation_issues)

        if isolation_issues:
            violations.append(
                QualityViolation(
                    gate_name="mock_isolation_compliance",
                    threshold=isolation_gate,
                    current_value=len(isolation_issues),
                    expected_value=0.0,
                    severity=isolation_gate.severity,
                    message=f"Mock isolation issues detected: {', '.join(isolation_issues)}",
                )
            )

        return violations

    def check_regression_gates(self) -> list[QualityViolation]:
        """Check for quality regressions compared to previous runs"""
        violations = []

        # Load current and previous metrics for comparison
        current_coverage = self._load_latest_coverage_report()
        previous_coverage = self._load_previous_coverage_report()

        if current_coverage and previous_coverage:
            current_total = current_coverage.get("total_coverage", 0.0)
            previous_total = previous_coverage.get("total_coverage", 0.0)

            # Check for significant coverage regression (>5% drop)
            if current_total < previous_total - 5.0:
                violations.append(
                    QualityViolation(
                        gate_name="coverage_regression",
                        threshold=QualityThreshold(
                            name="Coverage Regression",
                            current_value=current_total,
                            threshold_value=previous_total - 5.0,
                            direction="above",
                            severity="warning",
                            message="Coverage regression exceeds acceptable threshold",
                        ),
                        current_value=current_total,
                        expected_value=previous_total - 5.0,
                        severity="warning",
                        message=f"Coverage dropped from {previous_total:.1f}% to {current_total:.1f}% (>{5.0}% regression)",
                    )
                )

        return violations

    def _load_latest_coverage_report(self) -> dict | None:
        """Load the most recent coverage report"""
        try:
            coverage_files = sorted(self.reports_dir.glob("coverage_snapshot_*.json"))
            if coverage_files:
                with open(coverage_files[-1]) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load coverage report: {e}")
        return None

    def _load_previous_coverage_report(self) -> dict | None:
        """Load the second most recent coverage report"""
        try:
            coverage_files = sorted(self.reports_dir.glob("coverage_snapshot_*.json"))
            if len(coverage_files) >= 2:
                with open(coverage_files[-2]) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load previous coverage report: {e}")
        return None

    def _load_latest_health_metrics(self) -> dict | None:
        """Load the most recent health metrics"""
        try:
            health_files = sorted(self.reports_dir.glob("health_metrics_*.json"))
            if health_files:
                with open(health_files[-1]) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load health metrics: {e}")
        return None

    def run_all_gates(self) -> tuple[list[QualityViolation], bool]:
        """Run all quality gates and return violations with overall pass/fail"""
        print("[INFO] Running quality gate checks...")

        violations = []

        # Run coverage gates
        coverage_violations = self.check_coverage_gates()
        violations.extend(coverage_violations)

        # Run health gates
        health_violations = self.check_health_gates()
        violations.extend(health_violations)

        # Run regression gates
        regression_violations = self.check_regression_gates()
        violations.extend(regression_violations)

        # Determine overall pass/fail
        error_violations = [v for v in violations if v.severity == "error"]
        gates_passed = len(error_violations) == 0

        return violations, gates_passed

    def generate_gate_report(self, violations: list[QualityViolation], gates_passed: bool) -> str:
        """Generate quality gate report"""
        status = "[PASSED]" if gates_passed else "[FAILED]"
        timestamp = datetime.now().isoformat()

        report = f"""# Quality Gate Report
Generated: {timestamp}
Status: {status}

## Summary
- **Overall Status**: {"PASSED" if gates_passed else "FAILED"}
- **Total Violations**: {len(violations)}
- **Error Violations**: {len([v for v in violations if v.severity == "error"])}
- **Warning Violations**: {len([v for v in violations if v.severity == "warning"])}

## Gate Results
"""

        # Show all gates and their status
        for gate_name, threshold in self.quality_gates.items():
            gate_violations = [v for v in violations if v.gate_name == gate_name]
            gate_status = "[FAILED]" if gate_violations else "[PASSED]"

            report += f"\n### {gate_status} {threshold.name}\n"
            report += f"- **Current Value**: {threshold.current_value}\n"
            report += f"- **Threshold**: {threshold.direction} {threshold.threshold_value}\n"

            if gate_violations:
                for violation in gate_violations:
                    report += f"- **Issue**: {violation.message}\n"

        # Detail violations
        if violations:
            report += "\n## Violation Details\n"

            error_violations = [v for v in violations if v.severity == "error"]
            warning_violations = [v for v in violations if v.severity == "warning"]

            if error_violations:
                report += "\n### [ERROR] Critical Issues\n"
                for violation in error_violations:
                    report += f"""
#### {violation.gate_name}
- **Message**: {violation.message}
- **Current**: {violation.current_value}
- **Expected**: {violation.expected_value}
"""

            if warning_violations:
                report += "\n### [WARNING] Quality Warnings\n"
                for violation in warning_violations:
                    report += f"""
#### {violation.gate_name}
- **Message**: {violation.message}
- **Current**: {violation.current_value}
- **Expected**: {violation.expected_value}
"""

        if gates_passed:
            report += "\n## [SUCCESS] All Quality Gates Passed\n"
            report += "The codebase meets all defined quality standards.\n"
        else:
            report += "\n## [BLOCKED] Quality Gates Failed\n"
            report += "The following issues must be resolved before proceeding:\n"
            for violation in [v for v in violations if v.severity == "error"]:
                report += f"- {violation.message}\n"

        report += f"\n---\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return report

    def save_gate_report(self, violations: list[QualityViolation], gates_passed: bool) -> Path:
        """Save quality gate report to disk"""
        report = self.generate_gate_report(violations, gates_passed)
        report_file = self.reports_dir / "quality_gates_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"[INFO] Quality gate report saved: {report_file}")
        return report_file


def main():
    """Main quality gate enforcement function"""
    checker = QualityGateChecker()

    # Run all quality gates
    violations, gates_passed = checker.run_all_gates()

    # Save report
    checker.save_gate_report(violations, gates_passed)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"QUALITY GATES: {'PASSED' if gates_passed else 'FAILED'}")
    print(f"Violations: {len(violations)} ({len([v for v in violations if v.severity == 'error'])} errors)")

    if violations:
        print("\nViolation Summary:")
        for violation in violations:
            severity_indicator = "[ERROR]" if violation.severity == "error" else "[WARN]"
            print(f"  {severity_indicator} {violation.gate_name}: {violation.message}")

    # Exit with appropriate code for CI/CD integration
    if not gates_passed:
        print("\n[BLOCKED] Quality gates failed - commit blocked")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All quality gates passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
