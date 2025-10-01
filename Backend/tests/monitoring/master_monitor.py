"""
Master Test Monitoring System
Orchestrates all monitoring components for comprehensive test infrastructure oversight
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from coverage_monitor import CoverageMonitor
from health_monitor import TestHealthMonitor
from quality_gates import QualityGateChecker


class MasterTestMonitor:
    """Master coordinator for all test monitoring systems"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(self.project_root) / "tests" / "reports"

        # Initialize monitoring systems
        self.coverage_monitor = CoverageMonitor(self.project_root)
        self.health_monitor = TestHealthMonitor(self.project_root)
        self.quality_checker = QualityGateChecker(self.project_root)

    def run_full_monitoring_cycle(self, run_tests: bool = True) -> bool:
        """Run complete monitoring cycle with all systems"""
        print("[INFO] Starting master monitoring cycle...")
        print(f"[INFO] Timestamp: {datetime.now().isoformat()}")

        success = True

        try:
            # Step 1: Coverage monitoring
            print("\n[STEP 1] Running coverage analysis...")
            coverage_snapshot = self.coverage_monitor.collect_current_coverage(run_tests=run_tests)
            self.coverage_monitor.save_snapshot(coverage_snapshot)

            coverage_report = self.coverage_monitor.generate_coverage_report(coverage_snapshot)
            coverage_file = self.reports_dir / "latest_coverage_report.md"
            with open(coverage_file, "w") as f:
                f.write(coverage_report)
            print(f"[INFO] Coverage report saved: {coverage_file}")

            # Step 2: Health monitoring (only if we ran tests)
            if run_tests:
                print("\n[STEP 2] Running health analysis...")
                health_metrics = self.health_monitor.run_tests_with_monitoring()
                self.health_monitor.save_metrics(health_metrics)

                health_trends = self.health_monitor.analyze_trends()
                health_dashboard = self.health_monitor.generate_health_dashboard(health_metrics, health_trends)
                dashboard_file = self.reports_dir / "health_dashboard.md"
                with open(dashboard_file, "w", encoding="utf-8") as f:
                    f.write(health_dashboard)
                print(f"[INFO] Health dashboard saved: {dashboard_file}")
            else:
                print("[SKIP] Health monitoring skipped (tests not run)")

            # Step 3: Quality gates
            print("\n[STEP 3] Running quality gates...")
            violations, gates_passed = self.quality_checker.run_all_gates()
            self.quality_checker.save_gate_report(violations, gates_passed)

            if not gates_passed:
                success = False
                print("[ERROR] Quality gates failed")
            else:
                print("[SUCCESS] Quality gates passed")

            # Step 4: Generate master summary
            print("\n[STEP 4] Generating master summary...")
            master_summary = self._generate_master_summary(coverage_snapshot, violations, gates_passed)
            summary_file = self.reports_dir / "master_summary.md"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(master_summary)
            print(f"[INFO] Master summary saved: {summary_file}")

        except Exception as e:
            print(f"[ERROR] Monitoring cycle failed: {e}")
            success = False

        print(f"\n[COMPLETE] Master monitoring cycle: {'SUCCESS' if success else 'FAILED'}")
        return success

    def _generate_master_summary(self, coverage_snapshot, violations, gates_passed) -> str:
        """Generate comprehensive master summary report"""
        timestamp = datetime.now().isoformat()

        # Calculate key metrics
        total_coverage = coverage_snapshot.total_coverage
        service_count = len(coverage_snapshot.service_coverage)
        critical_violations = len([v for v in violations if v.severity == "error"])
        warning_violations = len([v for v in violations if v.severity == "warning"])

        # Overall health score (0-100)
        health_score = self._calculate_health_score(coverage_snapshot, violations)

        summary = f"""# Master Test Infrastructure Summary
Generated: {timestamp}

## Overall Health Score: {health_score:.1f}/100

## Key Metrics
- **Test Coverage**: {total_coverage:.1f}%
- **Services Monitored**: {service_count}
- **Quality Gates**: {"PASSED" if gates_passed else "FAILED"}
- **Critical Issues**: {critical_violations}
- **Warnings**: {warning_violations}

## System Status
- **Coverage Monitoring**: [ACTIVE] Latest snapshot collected
- **Health Monitoring**: [ACTIVE] Dashboard updated
- **Quality Gates**: [{"PASSED" if gates_passed else "BLOCKED"}] {"All gates passed" if gates_passed else f"{critical_violations} critical violations"}

## Coverage Summary
"""

        # Top and bottom services by coverage
        sorted_services = sorted(coverage_snapshot.service_coverage, key=lambda s: s.coverage_percentage, reverse=True)

        if sorted_services:
            summary += "\n### Top Coverage Services\n"
            for service in sorted_services[:3]:
                status = (
                    "[GOOD]"
                    if service.coverage_percentage >= 70
                    else "[FAIR]"
                    if service.coverage_percentage >= 40
                    else "[POOR]"
                )
                summary += f"- {status} **{service.service_name}**: {service.coverage_percentage:.1f}%\n"

            summary += "\n### Needs Improvement\n"
            for service in sorted_services[-3:]:
                if service.coverage_percentage < 40:
                    summary += f"- [POOR] **{service.service_name}**: {service.coverage_percentage:.1f}%\n"

        # Quality gate summary
        if violations:
            summary += f"\n## Quality Issues ({len(violations)} total)\n"

            if critical_violations > 0:
                summary += "\n### Critical Issues (Must Fix)\n"
                for violation in [v for v in violations if v.severity == "error"]:
                    summary += f"- **{violation.gate_name}**: {violation.message}\n"

            if warning_violations > 0:
                summary += "\n### Warnings (Should Fix)\n"
                for violation in [v for v in violations if v.severity == "warning"]:
                    summary += f"- **{violation.gate_name}**: {violation.message}\n"
        else:
            summary += "\n## [SUCCESS] No Quality Issues Detected\n"

        # Recommendations
        summary += "\n## Recommendations\n"

        if total_coverage < 60:
            summary += "- [PRIORITY] Increase overall test coverage to at least 60%\n"

        low_coverage_services = [s for s in coverage_snapshot.service_coverage if s.coverage_percentage < 30]
        if low_coverage_services:
            summary += f"- [ACTION] Focus testing effort on {len(low_coverage_services)} low-coverage services\n"

        if critical_violations > 0:
            summary += "- [URGENT] Resolve critical quality gate violations before proceeding\n"

        if len(violations) == 0 and total_coverage >= 60:
            summary += "- [EXCELLENT] Test infrastructure is in good health - maintain current standards\n"

        summary += f"\n---\n*Master summary generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return summary

    def _calculate_health_score(self, coverage_snapshot, violations) -> float:
        """Calculate overall health score (0-100)"""

        # Coverage component (40% of score)
        coverage_score = min(coverage_snapshot.total_coverage / 80.0, 1.0) * 40

        # Quality gates component (40% of score)
        critical_violations = len([v for v in violations if v.severity == "error"])
        warning_violations = len([v for v in violations if v.severity == "warning"])

        quality_score = 40.0
        quality_score -= critical_violations * 15  # -15 per critical violation
        quality_score -= warning_violations * 5  # -5 per warning
        quality_score = max(quality_score, 0)

        # Service coverage distribution component (20% of score)
        service_scores = [s.coverage_percentage for s in coverage_snapshot.service_coverage]
        if service_scores:
            avg_service_coverage = sum(service_scores) / len(service_scores)
            service_score = min(avg_service_coverage / 50.0, 1.0) * 20
        else:
            service_score = 0

        total_score = coverage_score + quality_score + service_score
        return min(max(total_score, 0), 100)

    def quick_status_check(self) -> str:
        """Quick status check without running tests"""
        try:
            # Load latest reports
            latest_coverage = self.reports_dir / "latest_coverage_report.md"
            health_dashboard = self.reports_dir / "health_dashboard.md"
            quality_gates = self.reports_dir / "quality_gates_report.md"

            status = "[MONITORING STATUS]\n"

            if latest_coverage.exists():
                mtime = datetime.fromtimestamp(latest_coverage.stat().st_mtime)
                status += f"Coverage Report: [AVAILABLE] {mtime.strftime('%Y-%m-%d %H:%M')}\n"
            else:
                status += "Coverage Report: [MISSING]\n"

            if health_dashboard.exists():
                mtime = datetime.fromtimestamp(health_dashboard.stat().st_mtime)
                status += f"Health Dashboard: [AVAILABLE] {mtime.strftime('%Y-%m-%d %H:%M')}\n"
            else:
                status += "Health Dashboard: [MISSING]\n"

            if quality_gates.exists():
                mtime = datetime.fromtimestamp(quality_gates.stat().st_mtime)
                status += f"Quality Gates: [AVAILABLE] {mtime.strftime('%Y-%m-%d %H:%M')}\n"
            else:
                status += "Quality Gates: [MISSING]\n"

            return status

        except Exception as e:
            return f"[ERROR] Status check failed: {e}"


def main():
    """Main monitoring orchestration function"""
    parser = argparse.ArgumentParser(description="Master test monitoring system")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests, use existing data only")
    parser.add_argument("--status", action="store_true", help="Quick status check only")
    parser.add_argument("--coverage-only", action="store_true", help="Run coverage monitoring only")
    parser.add_argument("--health-only", action="store_true", help="Run health monitoring only")
    parser.add_argument("--gates-only", action="store_true", help="Run quality gates only")

    args = parser.parse_args()

    monitor = MasterTestMonitor()

    if args.status:
        # Quick status check
        print(monitor.quick_status_check())
        return

    # Component-specific runs
    if args.coverage_only:
        print("[INFO] Running coverage monitoring only...")
        snapshot = monitor.coverage_monitor.collect_current_coverage(run_tests=not args.no_tests)
        monitor.coverage_monitor.save_snapshot(snapshot)
        report = monitor.coverage_monitor.generate_coverage_report(snapshot)
        print(report)
        return

    if args.health_only:
        print("[INFO] Running health monitoring only...")
        metrics = monitor.health_monitor.run_tests_with_monitoring()
        monitor.health_monitor.save_metrics(metrics)
        trends = monitor.health_monitor.analyze_trends()
        dashboard = monitor.health_monitor.generate_health_dashboard(metrics, trends)
        print(dashboard)
        return

    if args.gates_only:
        print("[INFO] Running quality gates only...")
        violations, passed = monitor.quality_checker.run_all_gates()
        monitor.quality_checker.save_gate_report(violations, passed)
        return

    # Full monitoring cycle
    success = monitor.run_full_monitoring_cycle(run_tests=not args.no_tests)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
