"""
Progress Tracking System
Provides historical analysis and trend visualization for test infrastructure improvement
"""

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class ProgressDataPoint:
    """Single progress measurement point"""

    timestamp: str
    metric_name: str
    value: float
    context: dict[str, Any]  # Additional context data


@dataclass
class TrendAnalysis:
    """Trend analysis for a specific metric"""

    metric_name: str
    current_value: float
    previous_value: float
    change_absolute: float
    change_percentage: float
    trend_direction: str  # 'improving', 'declining', 'stable'
    velocity: float  # Rate of change per day
    confidence: float  # Confidence in trend (0-1)
    milestones_hit: list[str]
    next_milestone: str | None


@dataclass
class ProgressSummary:
    """Overall progress summary"""

    tracking_period_days: int
    total_metrics_tracked: int
    improving_metrics: int
    declining_metrics: int
    stable_metrics: int
    overall_health_trend: str
    key_achievements: list[str]
    areas_needing_focus: list[str]
    velocity_score: float  # Overall improvement velocity (0-100)


class ProgressTracker:
    """Historical progress tracking and trend analysis system"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.reports_dir = Path(self.project_root) / "tests" / "reports"
        self.progress_dir = self.reports_dir / "progress"
        self.progress_dir.mkdir(exist_ok=True)

        # Progress tracking configuration
        self.tracked_metrics = {
            "total_coverage": {
                "name": "Overall Test Coverage",
                "milestones": [20, 30, 40, 50, 60, 70, 80],
                "target": 80.0,
                "source": "coverage",
                "higher_is_better": True,
            },
            "test_success_rate": {
                "name": "Test Success Rate",
                "milestones": [90, 95, 98, 99],
                "target": 100.0,
                "source": "health",
                "higher_is_better": True,
            },
            "test_execution_time": {
                "name": "Test Execution Time",
                "milestones": [120, 90, 60, 45, 30],
                "target": 30.0,
                "source": "health",
                "higher_is_better": False,
            },
            "critical_service_coverage": {
                "name": "Critical Services Average Coverage",
                "milestones": [20, 30, 40, 50, 60, 70],
                "target": 70.0,
                "source": "coverage",
                "higher_is_better": True,
            },
            "quality_gates_score": {
                "name": "Quality Gates Score",
                "milestones": [60, 70, 80, 90, 95],
                "target": 100.0,
                "source": "quality",
                "higher_is_better": True,
            },
            "infrastructure_health_score": {
                "name": "Infrastructure Health Score",
                "milestones": [40, 50, 60, 70, 80, 90],
                "target": 95.0,
                "source": "master",
                "higher_is_better": True,
            },
        }

    def collect_current_metrics(self) -> list[ProgressDataPoint]:
        """Collect current metric values from latest reports"""
        timestamp = datetime.now().isoformat()
        data_points = []

        # Coverage metrics
        coverage_data = self._load_latest_json_report("coverage_snapshot_*.json")
        if coverage_data:
            # Total coverage
            total_coverage = coverage_data.get("total_coverage", 0.0)
            data_points.append(
                ProgressDataPoint(
                    timestamp=timestamp,
                    metric_name="total_coverage",
                    value=total_coverage,
                    context={
                        "source": "coverage_snapshot",
                        "service_count": len(coverage_data.get("service_coverage", [])),
                    },
                )
            )

            # Critical service coverage average
            service_coverage = coverage_data.get("service_coverage", [])
            critical_services = ["AuthService", "VideoService", "UserVocabularyService"]
            critical_coverages = [
                s["coverage_percentage"] for s in service_coverage if s["service_name"] in critical_services
            ]
            if critical_coverages:
                avg_critical = statistics.mean(critical_coverages)
                data_points.append(
                    ProgressDataPoint(
                        timestamp=timestamp,
                        metric_name="critical_service_coverage",
                        value=avg_critical,
                        context={"critical_services": len(critical_coverages), "individual_scores": critical_coverages},
                    )
                )

        # Health metrics
        health_data = self._load_latest_json_report("health_metrics_*.json")
        if health_data:
            # Test success rate
            success_rate = health_data.get("success_rate", 0.0)
            data_points.append(
                ProgressDataPoint(
                    timestamp=timestamp,
                    metric_name="test_success_rate",
                    value=success_rate,
                    context={
                        "total_tests": health_data.get("total_tests", 0),
                        "passed": health_data.get("passed", 0),
                        "failed": health_data.get("failed", 0),
                    },
                )
            )

            # Test execution time
            execution_time = health_data.get("total_duration", 0.0)
            data_points.append(
                ProgressDataPoint(
                    timestamp=timestamp,
                    metric_name="test_execution_time",
                    value=execution_time,
                    context={"test_count": health_data.get("total_tests", 0)},
                )
            )

        # Master summary metrics
        master_data = self._load_latest_master_summary()
        if master_data:
            # Infrastructure health score
            health_score = master_data.get("health_score", 0.0)
            data_points.append(
                ProgressDataPoint(
                    timestamp=timestamp,
                    metric_name="infrastructure_health_score",
                    value=health_score,
                    context={"quality_gates_passed": master_data.get("quality_gates_passed", False)},
                )
            )

        return data_points

    def save_progress_data(self, data_points: list[ProgressDataPoint]) -> Path:
        """Save progress data points to disk"""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_file = self.progress_dir / f"progress_data_{timestamp_str}.json"

        # Convert to dict for JSON serialization
        data_dict = [asdict(dp) for dp in data_points]

        with open(progress_file, "w") as f:
            json.dump(data_dict, f, indent=2)

        print(f"[INFO] Progress data saved: {progress_file}")
        return progress_file

    def load_historical_data(self, lookback_days: int = 30) -> dict[str, list[ProgressDataPoint]]:
        """Load historical progress data organized by metric"""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Collect all progress files
        progress_files = []
        for file_path in self.progress_dir.glob("progress_data_*.json"):
            try:
                timestamp_str = file_path.stem.replace("progress_data_", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                if file_date >= cutoff_date:
                    progress_files.append((file_date, file_path))
            except ValueError:
                continue

        # Load and organize data by metric
        metrics_data = {}
        for _, file_path in sorted(progress_files):
            try:
                with open(file_path) as f:
                    data = json.load(f)

                for dp_dict in data:
                    dp = ProgressDataPoint(**dp_dict)
                    if dp.metric_name not in metrics_data:
                        metrics_data[dp.metric_name] = []
                    metrics_data[dp.metric_name].append(dp)
            except Exception as e:
                print(f"[WARN] Could not load progress file {file_path}: {e}")

        return metrics_data

    def analyze_metric_trend(self, metric_name: str, data_points: list[ProgressDataPoint]) -> TrendAnalysis:
        """Analyze trend for a specific metric"""
        if len(data_points) < 2:
            # Not enough data for trend analysis
            current_value = data_points[0].value if data_points else 0.0
            return TrendAnalysis(
                metric_name=metric_name,
                current_value=current_value,
                previous_value=current_value,
                change_absolute=0.0,
                change_percentage=0.0,
                trend_direction="stable",
                velocity=0.0,
                confidence=0.0,
                milestones_hit=[],
                next_milestone=None,
            )

        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        current = sorted_points[-1]
        previous = sorted_points[-2]

        # Calculate changes
        change_absolute = current.value - previous.value
        change_percentage = (change_absolute / previous.value * 100) if previous.value != 0 else 0.0

        # Determine trend direction
        config = self.tracked_metrics.get(metric_name, {})
        higher_is_better = config.get("higher_is_better", True)

        if abs(change_percentage) < 2.0:  # Less than 2% change is considered stable
            trend_direction = "stable"
        elif (change_absolute > 0 and higher_is_better) or (change_absolute < 0 and not higher_is_better):
            trend_direction = "improving"
        else:
            trend_direction = "declining"

        # Calculate velocity (change per day)
        try:
            current_time = datetime.fromisoformat(current.timestamp)
            previous_time = datetime.fromisoformat(previous.timestamp)
            time_diff_days = (current_time - previous_time).total_seconds() / 86400
            velocity = change_absolute / time_diff_days if time_diff_days > 0 else 0.0
        except:
            velocity = 0.0

        # Calculate confidence based on data consistency
        if len(sorted_points) >= 5:
            # Look at recent trend consistency
            recent_changes = []
            for i in range(len(sorted_points) - 4, len(sorted_points)):
                if i > 0:
                    change = sorted_points[i].value - sorted_points[i - 1].value
                    recent_changes.append(1 if change > 0 else -1 if change < 0 else 0)

            # Confidence based on consistency
            if recent_changes and all(c == recent_changes[0] for c in recent_changes):
                confidence = 0.9  # High confidence
            elif recent_changes and sum(recent_changes) != 0:
                confidence = 0.6  # Medium confidence
            else:
                confidence = 0.3  # Low confidence
        else:
            confidence = 0.5  # Medium confidence for limited data

        # Check milestones
        milestones = config.get("milestones", [])
        milestones_hit = []
        next_milestone = None

        if higher_is_better:
            milestones_hit = [str(m) for m in milestones if current.value >= m]
            next_candidates = [m for m in milestones if current.value < m]
            next_milestone = str(min(next_candidates)) if next_candidates else None
        else:
            milestones_hit = [str(m) for m in milestones if current.value <= m]
            next_candidates = [m for m in milestones if current.value > m]
            next_milestone = str(max(next_candidates)) if next_candidates else None

        return TrendAnalysis(
            metric_name=metric_name,
            current_value=current.value,
            previous_value=previous.value,
            change_absolute=change_absolute,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
            velocity=velocity,
            confidence=confidence,
            milestones_hit=milestones_hit,
            next_milestone=next_milestone,
        )

    def generate_progress_report(self, lookback_days: int = 30) -> str:
        """Generate comprehensive progress report"""
        print(f"[INFO] Generating progress report for last {lookback_days} days...")

        # Load historical data
        historical_data = self.load_historical_data(lookback_days)

        if not historical_data:
            return f"""# Progress Report
Generated: {datetime.now().isoformat()}

## No Historical Data Available
No progress data found for the last {lookback_days} days.
Run the progress tracker regularly to build historical trends.
"""

        # Analyze trends for each metric
        trend_analyses = []
        for metric_name, data_points in historical_data.items():
            trend = self.analyze_metric_trend(metric_name, data_points)
            trend_analyses.append(trend)

        # Generate summary statistics
        improving_count = len([t for t in trend_analyses if t.trend_direction == "improving"])
        declining_count = len([t for t in trend_analyses if t.trend_direction == "declining"])
        stable_count = len([t for t in trend_analyses if t.trend_direction == "stable"])

        # Calculate overall velocity score
        velocity_scores = []
        for trend in trend_analyses:
            config = self.tracked_metrics.get(trend.metric_name, {})
            target = config.get("target", 100.0)
            higher_is_better = config.get("higher_is_better", True)

            # Normalize velocity based on distance to target
            if higher_is_better:
                trend.current_value / target if target > 0 else 0
                velocity_score = min(50 + (trend.velocity * trend.confidence * 10), 100)
            else:
                target / trend.current_value if trend.current_value > 0 else 0
                velocity_score = min(50 + (abs(trend.velocity) * trend.confidence * 10), 100)

            velocity_scores.append(max(0, velocity_score))

        overall_velocity = statistics.mean(velocity_scores) if velocity_scores else 0

        # Generate report
        report = f"""# Infrastructure Progress Report
Generated: {datetime.now().isoformat()}
Tracking Period: {lookback_days} days

## Executive Summary
- **Metrics Tracked**: {len(trend_analyses)}
- **Improving**: {improving_count} ({improving_count / len(trend_analyses) * 100:.1f}%)
- **Declining**: {declining_count} ({declining_count / len(trend_analyses) * 100:.1f}%)
- **Stable**: {stable_count} ({stable_count / len(trend_analyses) * 100:.1f}%)
- **Overall Velocity Score**: {overall_velocity:.1f}/100

## Metric Trends

"""

        # Sort trends by importance (improving first, then by current value)
        sorted_trends = sorted(
            trend_analyses,
            key=lambda t: (
                0 if t.trend_direction == "improving" else 1 if t.trend_direction == "stable" else 2,
                -t.current_value,
            ),
        )

        for trend in sorted_trends:
            config = self.tracked_metrics.get(trend.metric_name, {})
            metric_display_name = config.get("name", trend.metric_name)

            # Trend indicators
            direction_icon = {"improving": "[UP]", "declining": "[DOWN]", "stable": "[STABLE]"}

            confidence_level = "HIGH" if trend.confidence >= 0.7 else "MEDIUM" if trend.confidence >= 0.4 else "LOW"

            report += f"""
### {direction_icon[trend.trend_direction]} {metric_display_name}
- **Current Value**: {trend.current_value:.2f}
- **Previous Value**: {trend.previous_value:.2f}
- **Change**: {trend.change_absolute:+.2f} ({trend.change_percentage:+.1f}%)
- **Velocity**: {trend.velocity:.3f}/day
- **Confidence**: {confidence_level} ({trend.confidence:.1f})
- **Milestones Hit**: {", ".join(trend.milestones_hit) if trend.milestones_hit else "None"}
- **Next Milestone**: {trend.next_milestone or "Target reached"}
"""

        # Key achievements section
        achievements = []
        focus_areas = []

        for trend in trend_analyses:
            config = self.tracked_metrics.get(trend.metric_name, {})
            metric_name = config.get("name", trend.metric_name)

            if trend.trend_direction == "improving" and trend.confidence >= 0.6:
                achievements.append(f"{metric_name} improving at {trend.velocity:.2f}/day")

            if trend.trend_direction == "declining" or (
                trend.current_value < 30 and config.get("higher_is_better", True)
            ):
                focus_areas.append(f"{metric_name} needs attention ({trend.current_value:.1f})")

        report += "\n## Key Achievements\n"
        if achievements:
            for achievement in achievements:
                report += f"- {achievement}\n"
        else:
            report += "- No significant improvements detected in tracking period\n"

        report += "\n## Areas Needing Focus\n"
        if focus_areas:
            for area in focus_areas:
                report += f"- {area}\n"
        else:
            report += "- All metrics are stable or improving\n"

        # Recommendations
        report += "\n## Recommendations\n"

        if improving_count > declining_count:
            report += "- [POSITIVE] Overall trend is positive - maintain current practices\n"
        elif declining_count > improving_count:
            report += "- [PRIORITY] More metrics declining than improving - review recent changes\n"
        else:
            report += "- [STABLE] Mixed results - focus on specific declining metrics\n"

        if overall_velocity < 30:
            report += "- [ACTION] Low improvement velocity - consider increasing development focus on testing\n"
        elif overall_velocity > 70:
            report += "- [EXCELLENT] High improvement velocity - excellent progress\n"

        # Historical data availability
        total_data_points = sum(len(points) for points in historical_data.values())
        report += "\n## Data Quality\n"
        report += f"- **Total Data Points**: {total_data_points}\n"
        report += f"- **Average Points per Metric**: {total_data_points / len(historical_data):.1f}\n"
        report += f"- **Data Confidence**: {'HIGH' if total_data_points >= 50 else 'MEDIUM' if total_data_points >= 20 else 'LOW'}\n"

        report += f"\n---\n*Progress report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return report

    def _load_latest_json_report(self, pattern: str) -> dict | None:
        """Load the most recent JSON report matching pattern"""
        try:
            files = sorted(self.reports_dir.glob(pattern))
            if files:
                with open(files[-1]) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load report {pattern}: {e}")
        return None

    def _load_latest_master_summary(self) -> dict | None:
        """Extract metrics from latest master summary markdown"""
        try:
            summary_file = self.reports_dir / "master_summary.md"
            if not summary_file.exists():
                return None

            with open(summary_file) as f:
                content = f.read()

            # Parse health score
            import re

            health_match = re.search(r"Overall Health Score: ([\d.]+)/100", content)
            health_score = float(health_match.group(1)) if health_match else 0.0

            # Parse quality gates status
            gates_match = re.search(r"Quality Gates\*\*: (PASSED|FAILED)", content)
            gates_passed = gates_match.group(1) == "PASSED" if gates_match else False

            return {"health_score": health_score, "quality_gates_passed": gates_passed}

        except Exception as e:
            print(f"[WARN] Could not parse master summary: {e}")
            return None


def main():
    """Main progress tracking function"""
    tracker = ProgressTracker()

    print("[INFO] Starting progress tracking...")

    # Collect current metrics
    data_points = tracker.collect_current_metrics()
    print(f"[INFO] Collected {len(data_points)} metric data points")

    # Save progress data
    if data_points:
        tracker.save_progress_data(data_points)

    # Generate progress report
    progress_report = tracker.generate_progress_report(lookback_days=14)  # 2 weeks
    report_file = tracker.reports_dir / "progress_report.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(progress_report)

    print(f"[INFO] Progress report generated: {report_file}")
    print("\n" + "=" * 50)
    print(progress_report)


if __name__ == "__main__":
    main()
