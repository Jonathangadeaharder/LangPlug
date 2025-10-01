"""
Strategic Service Coverage Planning System
Analyzes service dependencies and creates targeted test expansion strategies
"""

import ast
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ServiceDependency:
    """Service dependency relationship"""

    service_name: str
    depends_on: str
    dependency_type: str  # 'import', 'composition', 'inheritance'
    confidence: float  # 0-1, how certain we are about this dependency


@dataclass
class ServiceAnalysis:
    """Comprehensive service analysis"""

    service_name: str
    file_path: str
    current_coverage: float
    line_count: int
    complexity_score: float
    business_criticality: str  # 'high', 'medium', 'low'
    dependencies: list[ServiceDependency]
    public_methods: list[str]
    critical_paths: list[str]
    test_file_exists: bool
    test_count: int


@dataclass
class CoveragePlan:
    """Strategic coverage expansion plan"""

    service_name: str
    current_coverage: float
    target_coverage: float
    priority: str  # 'critical', 'high', 'medium', 'low'
    estimated_effort: str  # 'small', 'medium', 'large'
    test_strategy: list[str]
    dependencies_to_mock: list[str]
    key_scenarios: list[str]
    success_metrics: list[str]


@dataclass
class StrategicPlan:
    """Complete strategic testing plan"""

    plan_created: str
    overall_current_coverage: float
    overall_target_coverage: float
    total_services: int
    coverage_plans: list[CoveragePlan]
    implementation_phases: list[dict]
    resource_requirements: dict[str, str]
    timeline_estimate: str


class StrategicCoveragePlanner:
    """Strategic planning system for test coverage expansion"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.services_dir = self.project_root / "services"
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.tests_dir / "reports"

        # Business criticality mapping
        self.service_criticality = {
            "AuthService": "high",
            "VideoService": "high",
            "UserVocabularyService": "high",
            "AuthenticatedUserVocabularyService": "high",
            "DirectSubtitleProcessor": "medium",
            "LoggingService": "medium",
            "VocabularyService": "medium",
            "VocabularyPreloadService": "low",
            "ServiceFactoryService": "low",
        }

        # Coverage targets by criticality
        self.coverage_targets = {"high": 80.0, "medium": 60.0, "low": 40.0}

    def analyze_service_structure(self) -> list[ServiceAnalysis]:
        """Analyze all services for structure and dependencies"""
        analyses = []

        # Get coverage data
        coverage_data = self._load_current_coverage()
        coverage_by_service = {}
        if coverage_data:
            for service in coverage_data.get("service_coverage", []):
                coverage_by_service[service["service_name"]] = service["coverage_percentage"]

        # Scan service files
        for service_file in self.services_dir.rglob("*.py"):
            if service_file.name.startswith("__"):
                continue

            service_name = self._extract_service_name(service_file)
            if not service_name:
                continue

            analysis = self._analyze_single_service(service_file, service_name, coverage_by_service)
            analyses.append(analysis)

        return analyses

    def _extract_service_name(self, file_path: Path) -> str | None:
        """Extract service name from file path"""
        # Convert file path to service name
        if "service" in file_path.name.lower():
            parts = file_path.name.replace(".py", "").split("_")
            # Convert auth_service -> AuthService
            service_name = "".join(word.capitalize() for word in parts)
            if not service_name.endswith("Service"):
                service_name += "Service"
            return service_name
        return None

    def _analyze_single_service(
        self, file_path: Path, service_name: str, coverage_data: dict[str, float]
    ) -> ServiceAnalysis:
        """Analyze a single service file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST for deep analysis
            try:
                tree = ast.parse(content)
            except SyntaxError:
                tree = None

            # Count lines
            line_count = len([line for line in content.split("\n") if line.strip()])

            # Find dependencies
            dependencies = self._find_dependencies(content, tree)

            # Find public methods
            public_methods = self._find_public_methods(content, tree)

            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(content, tree, public_methods)

            # Find critical paths
            critical_paths = self._identify_critical_paths(content)

            # Check for existing tests
            test_file_exists, test_count = self._check_existing_tests(service_name)

            return ServiceAnalysis(
                service_name=service_name,
                file_path=str(file_path),
                current_coverage=coverage_data.get(service_name, 0.0),
                line_count=line_count,
                complexity_score=complexity_score,
                business_criticality=self.service_criticality.get(service_name, "low"),
                dependencies=dependencies,
                public_methods=public_methods,
                critical_paths=critical_paths,
                test_file_exists=test_file_exists,
                test_count=test_count,
            )

        except Exception as e:
            print(f"[WARN] Failed to analyze {file_path}: {e}")
            return ServiceAnalysis(
                service_name=service_name,
                file_path=str(file_path),
                current_coverage=coverage_data.get(service_name, 0.0),
                line_count=0,
                complexity_score=0.0,
                business_criticality=self.service_criticality.get(service_name, "low"),
                dependencies=[],
                public_methods=[],
                critical_paths=[],
                test_file_exists=False,
                test_count=0,
            )

    def _find_dependencies(self, content: str, tree: ast.AST | None) -> list[ServiceDependency]:
        """Find service dependencies"""
        dependencies = []

        # Find import dependencies
        import_pattern = r"from\s+(?:services\.(\w+)|\.\.(\w+))\s+import"
        for match in re.finditer(import_pattern, content):
            dep_name = match.group(1) or match.group(2)
            if dep_name and "service" in dep_name.lower():
                dependencies.append(
                    ServiceDependency(
                        service_name="",  # Will be set by caller
                        depends_on=dep_name,
                        dependency_type="import",
                        confidence=0.9,
                    )
                )

        # Find composition dependencies (basic heuristic)
        self_pattern = r"self\.(\w*service\w*)"
        for match in re.finditer(self_pattern, content, re.IGNORECASE):
            dep_name = match.group(1)
            dependencies.append(
                ServiceDependency(service_name="", depends_on=dep_name, dependency_type="composition", confidence=0.7)
            )

        return dependencies

    def _find_public_methods(self, content: str, tree: ast.AST | None) -> list[str]:
        """Find public methods in the service"""
        public_methods = []

        # Regex approach for reliability
        method_pattern = r"^\s+(?:async\s+)?def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\("
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_name = match.group(1)
            if not method_name.startswith("_"):  # Public method
                public_methods.append(method_name)

        return public_methods

    def _calculate_complexity_score(self, content: str, tree: ast.AST | None, public_methods: list[str]) -> float:
        """Calculate complexity score (0-100)"""
        score = 0.0

        # Method count factor
        method_count = len(public_methods)
        score += min(method_count * 2, 30)  # Max 30 points for methods

        # Control structure complexity
        control_keywords = ["if", "elif", "for", "while", "try", "except", "with"]
        control_count = sum(len(re.findall(rf"\b{keyword}\b", content)) for keyword in control_keywords)
        score += min(control_count, 40)  # Max 40 points for control structures

        # Async/await complexity
        async_count = len(re.findall(r"\basync\b", content)) + len(re.findall(r"\bawait\b", content))
        score += min(async_count, 20)  # Max 20 points for async complexity

        # Decorator complexity
        decorator_count = len(re.findall(r"@\w+", content))
        score += min(decorator_count, 10)  # Max 10 points for decorators

        return min(score, 100.0)

    def _identify_critical_paths(self, content: str) -> list[str]:
        """Identify critical code paths that need testing"""
        critical_paths = []

        # Authentication paths
        if any(keyword in content.lower() for keyword in ["login", "authenticate", "password", "token"]):
            critical_paths.append("authentication_flow")

        # Data processing paths
        if any(keyword in content.lower() for keyword in ["process", "parse", "filter", "transform"]):
            critical_paths.append("data_processing")

        # Database operations
        if any(keyword in content.lower() for keyword in ["create", "update", "delete", "query", "session"]):
            critical_paths.append("database_operations")

        # Error handling
        if any(keyword in content.lower() for keyword in ["exception", "error", "raise", "try"]):
            critical_paths.append("error_handling")

        # File operations
        if any(keyword in content.lower() for keyword in ["file", "path", "read", "write", "open"]):
            critical_paths.append("file_operations")

        return critical_paths

    def _check_existing_tests(self, service_name: str) -> tuple[bool, int]:
        """Check if tests exist for the service"""
        test_pattern = f"test_{service_name.lower().replace('service', '')}_service.py"
        test_files = list(self.tests_dir.rglob(test_pattern))

        if not test_files:
            # Try alternative patterns
            alt_patterns = [f"test_{service_name.lower()}.py", f"*{service_name.lower()}*.py"]
            for pattern in alt_patterns:
                test_files.extend(self.tests_dir.rglob(pattern))

        if test_files:
            # Count test methods in the file
            try:
                with open(test_files[0], encoding="utf-8") as f:
                    test_content = f.read()
                test_count = len(re.findall(r"def\s+test_\w+", test_content))
                return True, test_count
            except:
                return True, 0

        return False, 0

    def _load_current_coverage(self) -> dict | None:
        """Load current coverage data"""
        try:
            coverage_files = sorted(self.reports_dir.glob("coverage_snapshot_*.json"))
            if coverage_files:
                with open(coverage_files[-1]) as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load coverage data: {e}")
        return None

    def create_strategic_plan(self, analyses: list[ServiceAnalysis]) -> StrategicPlan:
        """Create comprehensive strategic coverage plan"""
        print("[INFO] Creating strategic coverage plan...")

        coverage_plans = []
        for analysis in analyses:
            plan = self._create_service_plan(analysis)
            coverage_plans.append(plan)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        coverage_plans.sort(key=lambda p: priority_order.get(p.priority, 4))

        # Calculate overall metrics
        current_avg = sum(p.current_coverage for p in coverage_plans) / len(coverage_plans) if coverage_plans else 0
        target_avg = sum(p.target_coverage for p in coverage_plans) / len(coverage_plans) if coverage_plans else 0

        # Create implementation phases
        phases = self._create_implementation_phases(coverage_plans)

        # Estimate resources and timeline
        resource_requirements = self._estimate_resources(coverage_plans)
        timeline_estimate = self._estimate_timeline(coverage_plans)

        return StrategicPlan(
            plan_created=datetime.now().isoformat(),
            overall_current_coverage=current_avg,
            overall_target_coverage=target_avg,
            total_services=len(coverage_plans),
            coverage_plans=coverage_plans,
            implementation_phases=phases,
            resource_requirements=resource_requirements,
            timeline_estimate=timeline_estimate,
        )

    def _create_service_plan(self, analysis: ServiceAnalysis) -> CoveragePlan:
        """Create coverage plan for a single service"""
        # Determine target coverage based on criticality
        target_coverage = self.coverage_targets.get(analysis.business_criticality, 40.0)

        # Determine priority
        if analysis.business_criticality == "high" and analysis.current_coverage < 50:
            priority = "critical"
        elif analysis.business_criticality == "high" or (
            analysis.business_criticality == "medium" and analysis.current_coverage < 30
        ):
            priority = "high"
        elif analysis.current_coverage < 20:
            priority = "medium"
        else:
            priority = "low"

        # Estimate effort based on complexity and current coverage
        gap = target_coverage - analysis.current_coverage
        if gap > 50 or analysis.complexity_score > 70:
            effort = "large"
        elif gap > 25 or analysis.complexity_score > 40:
            effort = "medium"
        else:
            effort = "small"

        # Create test strategy
        test_strategy = []
        if not analysis.test_file_exists:
            test_strategy.append("Create comprehensive test suite from scratch")
        else:
            test_strategy.append("Expand existing test suite")

        if analysis.critical_paths:
            test_strategy.append(f"Focus on critical paths: {', '.join(analysis.critical_paths)}")

        if analysis.complexity_score > 60:
            test_strategy.append("Use parameterized tests for complex scenarios")

        if len(analysis.public_methods) > 10:
            test_strategy.append("Create method-specific test classes for organization")

        # Dependencies to mock
        dependencies_to_mock = [dep.depends_on for dep in analysis.dependencies if dep.confidence > 0.5]

        # Key scenarios based on service type and paths
        key_scenarios = self._generate_key_scenarios(analysis)

        # Success metrics
        success_metrics = [
            f"Achieve {target_coverage:.0f}% test coverage",
            "All critical paths tested",
            "All public methods have test cases",
        ]

        if analysis.business_criticality == "high":
            success_metrics.append("Edge cases and error scenarios covered")

        return CoveragePlan(
            service_name=analysis.service_name,
            current_coverage=analysis.current_coverage,
            target_coverage=target_coverage,
            priority=priority,
            estimated_effort=effort,
            test_strategy=test_strategy,
            dependencies_to_mock=dependencies_to_mock,
            key_scenarios=key_scenarios,
            success_metrics=success_metrics,
        )

    def _generate_key_scenarios(self, analysis: ServiceAnalysis) -> list[str]:
        """Generate key test scenarios based on service analysis"""
        scenarios = []

        service_name_lower = analysis.service_name.lower()

        if "auth" in service_name_lower:
            scenarios.extend(
                [
                    "Successful user authentication",
                    "Invalid credentials handling",
                    "Session creation and validation",
                    "Password hashing and verification",
                    "User registration flow",
                ]
            )

        if "video" in service_name_lower:
            scenarios.extend(
                [
                    "Video file processing",
                    "Subtitle extraction and filtering",
                    "File path validation",
                    "Error handling for invalid files",
                    "Performance with large files",
                ]
            )

        if "vocabulary" in service_name_lower:
            scenarios.extend(
                [
                    "Vocabulary data retrieval",
                    "User-specific vocabulary filtering",
                    "Database operation success/failure",
                    "Data validation and sanitization",
                    "Performance with large datasets",
                ]
            )

        if "logging" in service_name_lower:
            scenarios.extend(
                [
                    "Log message formatting",
                    "Different log levels handling",
                    "File output operations",
                    "Error logging scenarios",
                    "Performance impact measurement",
                ]
            )

        # Generic scenarios for all services
        scenarios.extend(
            ["Initialization and configuration", "Error handling and recovery", "Resource cleanup and disposal"]
        )

        return scenarios[:8]  # Limit to most important scenarios

    def _create_implementation_phases(self, plans: list[CoveragePlan]) -> list[dict]:
        """Create phased implementation plan"""
        phases = []

        # Phase 1: Critical and High Priority
        phase1_services = [p for p in plans if p.priority in ["critical", "high"]]
        if phase1_services:
            phases.append(
                {
                    "phase": 1,
                    "name": "Critical Infrastructure Testing",
                    "services": [p.service_name for p in phase1_services],
                    "estimated_duration": "2-3 weeks",
                    "focus": "High-business-value services and critical gaps",
                }
            )

        # Phase 2: Medium Priority
        phase2_services = [p for p in plans if p.priority == "medium"]
        if phase2_services:
            phases.append(
                {
                    "phase": 2,
                    "name": "Core Service Coverage",
                    "services": [p.service_name for p in phase2_services],
                    "estimated_duration": "2-4 weeks",
                    "focus": "Essential service coverage and dependency stability",
                }
            )

        # Phase 3: Low Priority
        phase3_services = [p for p in plans if p.priority == "low"]
        if phase3_services:
            phases.append(
                {
                    "phase": 3,
                    "name": "Comprehensive Coverage",
                    "services": [p.service_name for p in phase3_services],
                    "estimated_duration": "1-2 weeks",
                    "focus": "Complete coverage and edge case handling",
                }
            )

        return phases

    def _estimate_resources(self, plans: list[CoveragePlan]) -> dict[str, str]:
        """Estimate resource requirements"""
        large_effort = len([p for p in plans if p.estimated_effort == "large"])
        medium_effort = len([p for p in plans if p.estimated_effort == "medium"])
        small_effort = len([p for p in plans if p.estimated_effort == "small"])

        total_effort_days = large_effort * 5 + medium_effort * 2 + small_effort * 1

        return {
            "total_estimated_days": f"{total_effort_days} development days",
            "developer_requirement": "1 senior developer" if total_effort_days <= 15 else "1-2 senior developers",
            "testing_expertise": "Required: Python async testing, SQLAlchemy mocking, FastAPI patterns",
            "infrastructure_setup": "Test monitoring systems, CI/CD integration, quality gates",
        }

    def _estimate_timeline(self, plans: list[CoveragePlan]) -> str:
        """Estimate implementation timeline"""
        len([p for p in plans if p.priority in ["critical", "high"]])
        total_services = len(plans)

        if total_services <= 5:
            return "4-6 weeks"
        elif total_services <= 10:
            return "6-8 weeks"
        else:
            return "8-12 weeks"

    def generate_strategic_report(self, plan: StrategicPlan) -> str:
        """Generate comprehensive strategic report"""
        report = f"""# Strategic Test Coverage Expansion Plan
Generated: {plan.plan_created}

## Executive Summary
- **Current Overall Coverage**: {plan.overall_current_coverage:.1f}%
- **Target Overall Coverage**: {plan.overall_target_coverage:.1f}%
- **Services to Enhance**: {plan.total_services}
- **Estimated Timeline**: {plan.timeline_estimate}
- **Resource Requirement**: {plan.resource_requirements.get("developer_requirement", "TBD")}

## Implementation Phases
"""

        for phase in plan.implementation_phases:
            report += f"""
### Phase {phase["phase"]}: {phase["name"]}
- **Duration**: {phase["estimated_duration"]}
- **Services**: {", ".join(phase["services"])}
- **Focus**: {phase["focus"]}
"""

        report += "\n## Service Coverage Plans\n"

        for coverage_plan in plan.coverage_plans:
            priority_icon = {"critical": "[CRITICAL]", "high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}

            report += f"""
### {priority_icon[coverage_plan.priority]} {coverage_plan.service_name}
- **Current Coverage**: {coverage_plan.current_coverage:.1f}%
- **Target Coverage**: {coverage_plan.target_coverage:.1f}%
- **Estimated Effort**: {coverage_plan.estimated_effort.upper()}
- **Priority**: {coverage_plan.priority.upper()}

#### Test Strategy
"""
            for strategy in coverage_plan.test_strategy:
                report += f"- {strategy}\n"

            if coverage_plan.dependencies_to_mock:
                report += "\n#### Dependencies to Mock\n"
                for dep in coverage_plan.dependencies_to_mock:
                    report += f"- {dep}\n"

            report += "\n#### Key Test Scenarios\n"
            for scenario in coverage_plan.key_scenarios:
                report += f"- {scenario}\n"

            report += "\n#### Success Metrics\n"
            for metric in coverage_plan.success_metrics:
                report += f"- {metric}\n"

        # Resource requirements
        report += "\n## Resource Requirements\n"
        for key, value in plan.resource_requirements.items():
            formatted_key = key.replace("_", " ").title()
            report += f"- **{formatted_key}**: {value}\n"

        # Implementation recommendations
        report += """
## Implementation Recommendations

### Development Approach
1. **Start with Critical Services**: Focus on AuthService and VideoService first
2. **Use Existing Patterns**: Follow patterns established in current test suite
3. **Mock External Dependencies**: Ensure test isolation and reliability
4. **Incremental Development**: Implement and validate coverage incrementally

### Quality Assurance
1. **Use Quality Gates**: Leverage automated quality gates to prevent regressions
2. **Monitor Progress**: Track coverage improvements using monitoring systems
3. **Review and Refactor**: Regular code review and test refactoring sessions
4. **Documentation**: Document complex test scenarios and patterns

### Risk Mitigation
1. **Parallel Development**: Work on independent services simultaneously
2. **Backup Plans**: Have alternative approaches for complex testing scenarios
3. **Stakeholder Communication**: Regular updates on progress and blockers
4. **Testing Infrastructure**: Ensure robust CI/CD pipeline for test execution

"""

        report += f"\n---\n*Strategic plan generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

        return report

    def save_strategic_plan(self, plan: StrategicPlan) -> Path:
        """Save strategic plan to disk"""
        # Save JSON data
        plan_file = self.reports_dir / "strategic_coverage_plan.json"
        with open(plan_file, "w") as f:
            json.dump(asdict(plan), f, indent=2)

        # Save report
        report = self.generate_strategic_report(plan)
        report_file = self.reports_dir / "strategic_coverage_plan.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"[INFO] Strategic plan saved: {report_file}")
        return report_file


def main():
    """Main strategic planning function"""
    planner = StrategicCoveragePlanner()

    print("[INFO] Starting strategic coverage analysis...")

    # Analyze service structure
    analyses = planner.analyze_service_structure()
    print(f"[INFO] Analyzed {len(analyses)} services")

    # Create strategic plan
    strategic_plan = planner.create_strategic_plan(analyses)

    # Save plan
    planner.save_strategic_plan(strategic_plan)

    # Display summary
    report = planner.generate_strategic_report(strategic_plan)
    print("\n" + "=" * 50)
    print(report)


if __name__ == "__main__":
    main()
