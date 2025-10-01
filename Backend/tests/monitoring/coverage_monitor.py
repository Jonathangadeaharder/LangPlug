"""
Test Coverage Monitoring System
Provides automated tracking and analysis of test coverage across the codebase
"""

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ServiceCoverage:
    """Coverage metrics for a single service"""

    service_name: str
    total_statements: int
    missing_statements: int
    coverage_percentage: float
    covered_lines: list[int]
    missing_lines: list[int]
    critical_methods_covered: list[str]
    critical_methods_missing: list[str]


@dataclass
class CoverageSnapshot:
    """Complete coverage snapshot at a point in time"""

    timestamp: str
    total_coverage: float
    service_coverage: list[ServiceCoverage]
    test_count: int
    test_files: list[str]
    critical_services_status: dict[str, str]  # service -> status


class CoverageMonitor:
    """Automated test coverage monitoring and analysis system"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(self.project_root) / "tests" / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Critical services that require high coverage
        self.critical_services = {
            "AuthService": 80,
            "VideoService": 70,
            "DirectSubtitleProcessor": 75,
            "LoggingService": 60,
            "UserVocabularyService": 70,
        }

        # Business logic patterns that require coverage
        self.critical_patterns = [
            r"def\s+(authenticate|login|register)",
            r"def\s+(process|filter|parse)",
            r"def\s+(validate|verify|check)",
            r"class\s+\w*Service",
            r"def\s+(create|update|delete|get)",
        ]

    def collect_current_coverage(self, run_tests: bool = False) -> CoverageSnapshot:
        """Collect current test coverage metrics"""
        coverage_file = self.reports_dir / "coverage.json"

        if run_tests:
            print("[INFO] Running tests to collect coverage metrics...")
            cmd = [
                "powershell.exe",
                "-Command",
                f"api_venv\\Scripts\\python.exe -m pytest --cov=. --cov-report=json:{coverage_file} --tb=no -q",
            ]

            try:
                result = subprocess.run(
                    cmd, check=False, cwd=self.project_root, capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    print(f"[WARN] Coverage collection had issues: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("[WARN] Coverage collection timed out, using existing data if available")
            except Exception as e:
                print(f"[ERROR] Failed to run coverage: {e}")

        if not coverage_file.exists():
            print(f"[ERROR] Coverage file not found at {coverage_file}")
            return self._create_empty_snapshot()

        print(f"[INFO] Using coverage data from: {coverage_file}")
        return self._parse_coverage_data(coverage_file)

    def _parse_coverage_data(self, coverage_file: Path) -> CoverageSnapshot:
        """Parse pytest coverage JSON output"""
        try:
            with open(coverage_file) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to parse coverage data: {e}")
            return self._create_empty_snapshot()

        # Extract service-level coverage
        service_coverage = []
        for filename, file_data in data.get("files", {}).items():
            # Handle both Windows and Unix paths
            normalized_path = filename.replace("\\", "/")
            if "services/" in normalized_path and normalized_path.endswith(".py"):
                service_name = self._extract_service_name(normalized_path)
                if service_name:
                    coverage_info = self._analyze_service_coverage(service_name, normalized_path, file_data)
                    service_coverage.append(coverage_info)

        # Count test files
        test_files = [f for f in data.get("files", {}) if "test_" in f]

        # Assess critical services
        critical_status = {}
        for service_name, threshold in self.critical_services.items():
            service_data = next((s for s in service_coverage if s.service_name == service_name), None)
            if service_data:
                status = "[GOOD]" if service_data.coverage_percentage >= threshold else "[NEEDS IMPROVEMENT]"
                critical_status[service_name] = f"{status} ({service_data.coverage_percentage:.1f}%)"
            else:
                critical_status[service_name] = "[NO TESTS]"

        return CoverageSnapshot(
            timestamp=datetime.now().isoformat(),
            total_coverage=data.get("totals", {}).get("percent_covered", 0.0),
            service_coverage=service_coverage,
            test_count=len(test_files),
            test_files=test_files,
            critical_services_status=critical_status,
        )

    def _extract_service_name(self, filename: str) -> str | None:
        """Extract service name from filename"""
        # Extract from paths like 'services/authservice/auth_service.py'
        if "service" in filename.lower():
            parts = filename.split("/")
            for part in parts:
                if "service" in part.lower() and part.endswith(".py"):
                    # Convert auth_service.py -> AuthService
                    name = part.replace(".py", "").replace("_", " ").title().replace(" ", "")
                    if not name.endswith("Service"):
                        name += "Service"
                    return name
        return None

    def _analyze_service_coverage(self, service_name: str, filename: str, file_data: dict) -> ServiceCoverage:
        """Analyze coverage for a specific service"""
        summary = file_data.get("summary", {})

        # Analyze critical methods
        critical_covered = []
        critical_missing = []

        try:
            # Read source file to analyze methods
            source_path = Path(self.project_root) / filename
            if source_path.exists():
                with open(source_path) as f:
                    content = f.read()

                # Find critical methods
                for pattern in self.critical_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # This is a simplified analysis - in reality we'd need more sophisticated parsing
                        if "def" in pattern:
                            method_name = match.split("(")[0] if "(" in match else match
                            critical_covered.append(method_name)
        except Exception as e:
            print(f"[WARN] Could not analyze methods in {filename}: {e}")

        return ServiceCoverage(
            service_name=service_name,
            total_statements=summary.get("num_statements", 0),
            missing_statements=summary.get("missing_lines", 0),
            coverage_percentage=summary.get("percent_covered", 0.0),
            covered_lines=file_data.get("executed_lines", []),
            missing_lines=file_data.get("missing_lines", []),
            critical_methods_covered=critical_covered,
            critical_methods_missing=critical_missing,
        )

    def _create_empty_snapshot(self) -> CoverageSnapshot:
        """Create empty snapshot when coverage collection fails"""
        return CoverageSnapshot(
            timestamp=datetime.now().isoformat(),
            total_coverage=0.0,
            service_coverage=[],
            test_count=0,
            test_files=[],
            critical_services_status={},
        )

    def save_snapshot(self, snapshot: CoverageSnapshot) -> Path:
        """Save coverage snapshot to disk"""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.reports_dir / f"coverage_snapshot_{timestamp_str}.json"

        # Convert dataclasses to dict for JSON serialization
        snapshot_dict = asdict(snapshot)

        with open(snapshot_file, "w") as f:
            json.dump(snapshot_dict, f, indent=2)

        print(f"[INFO] Coverage snapshot saved: {snapshot_file}")
        return snapshot_file

    def generate_coverage_report(self, snapshot: CoverageSnapshot) -> str:
        """Generate human-readable coverage report"""
        report = f"""# Test Coverage Report
Generated: {snapshot.timestamp}

## Overall Coverage
**Total Coverage**: {snapshot.total_coverage:.1f}%
**Test Files**: {snapshot.test_count}

## Critical Services Status
"""
        for service, status in snapshot.critical_services_status.items():
            report += f"- **{service}**: {status}\n"

        report += "\n## Service-Level Coverage\n"

        # Sort services by coverage percentage
        sorted_services = sorted(snapshot.service_coverage, key=lambda s: s.coverage_percentage, reverse=True)

        for service in sorted_services:
            status_indicator = (
                "[GOOD]"
                if service.coverage_percentage >= 70
                else "[FAIR]"
                if service.coverage_percentage >= 40
                else "[POOR]"
            )
            report += f"""
### {status_indicator} {service.service_name}
- **Coverage**: {service.coverage_percentage:.1f}%
- **Statements**: {service.total_statements - service.missing_statements}/{service.total_statements}
- **Missing Lines**: {len(service.missing_lines)} lines
"""

        return report

    def analyze_trends(self, snapshots_limit: int = 10) -> dict:
        """Analyze coverage trends over time"""
        snapshot_files = sorted(self.reports_dir.glob("coverage_snapshot_*.json"))[-snapshots_limit:]

        if len(snapshot_files) < 2:
            return {"message": "Need at least 2 snapshots to analyze trends"}

        trends = {"total_coverage_trend": [], "service_trends": {}, "test_count_trend": []}

        for snapshot_file in snapshot_files:
            try:
                with open(snapshot_file) as f:
                    data = json.load(f)

                trends["total_coverage_trend"].append(
                    {"timestamp": data["timestamp"], "coverage": data["total_coverage"]}
                )

                trends["test_count_trend"].append({"timestamp": data["timestamp"], "test_count": data["test_count"]})

                # Track service trends
                for service_data in data.get("service_coverage", []):
                    service_name = service_data["service_name"]
                    if service_name not in trends["service_trends"]:
                        trends["service_trends"][service_name] = []

                    trends["service_trends"][service_name].append(
                        {"timestamp": data["timestamp"], "coverage": service_data["coverage_percentage"]}
                    )

            except Exception as e:
                print(f"[WARN] Could not parse snapshot {snapshot_file}: {e}")

        return trends


def main():
    """Main monitoring function"""
    monitor = CoverageMonitor()

    print("[INFO] Starting test coverage monitoring...")
    snapshot = monitor.collect_current_coverage()

    # Save snapshot
    monitor.save_snapshot(snapshot)

    # Generate report
    report = monitor.generate_coverage_report(snapshot)
    report_file = monitor.reports_dir / "latest_coverage_report.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"[INFO] Coverage report generated: {report_file}")
    print("\n" + "=" * 50)
    print(report)

    # Analyze trends if possible
    trends = monitor.analyze_trends()
    if "message" not in trends:
        print(f"\n[INFO] Trend Analysis Available - {len(trends['total_coverage_trend'])} snapshots")


if __name__ == "__main__":
    main()
