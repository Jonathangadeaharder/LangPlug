#!/usr/bin/env python3
"""
Comprehensive Code Quality Metrics Report
Generates detailed metrics for maintainability, complexity, and code health
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Run command and return output and return code"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return f"Error: {e}", 1


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}\n")


def radon_cyclomatic_complexity():
    """Run Radon cyclomatic complexity analysis"""
    print_section("Cyclomatic Complexity (Radon)")
    output, code = run_command(["radon", "cc", ".", "-a", "-s"])
    print(output)
    return {"success": code == 0, "output": output}


def radon_maintainability_index():
    """Run Radon maintainability index analysis"""
    print_section("Maintainability Index (Radon)")
    output, code = run_command(["radon", "mi", ".", "-s"])
    print(output)
    return {"success": code == 0, "output": output}


def radon_halstead_metrics():
    """Run Radon Halstead metrics analysis"""
    print_section("Halstead Metrics (Radon)")
    output, code = run_command(["radon", "hal", ".", "-f"])
    print(output[:2000])  # Limit output
    if len(output) > 2000:
        print("\n... (output truncated) ...")
    return {"success": code == 0, "output": output[:2000]}


def radon_raw_metrics():
    """Run Radon raw metrics (LOC, LLOC, comments, etc.)"""
    print_section("Raw Metrics - Lines of Code (Radon)")
    output, code = run_command(["radon", "raw", ".", "-s"])
    print(output)
    return {"success": code == 0, "output": output}


def lizard_complexity():
    """Run Lizard complexity analysis"""
    print_section("Cognitive Complexity (Lizard)")
    output, code = run_command(["lizard", ".", "-l", "python", "-w", "-T", "nloc=50", "-T", "cyclomatic_complexity=10"])
    print(output)
    return {"success": code == 0, "output": output}


def mypy_type_coverage():
    """Run MyPy with type coverage report"""
    print_section("Type Coverage (MyPy)")
    output, code = run_command(
        [
            "mypy",
            ".",
            "--explicit-package-bases",
            "--ignore-missing-imports",
            "--no-error-summary",
            "--txt-report",
            "mypy-coverage",
            "--html-report",
            "mypy-html",
        ]
    )
    # Read type coverage statistics
    try:
        stats_file = Path("mypy-coverage/index.txt")
        if stats_file.exists():
            stats = stats_file.read_text()
            print(stats[:1000])
        else:
            print(output[:1000])
    except Exception as e:
        print(f"Could not read type coverage: {e}")
    return {"success": True, "output": "Type coverage generated"}


def test_coverage():
    """Get test coverage statistics"""
    print_section("Test Coverage (Pytest)")

    # Check if coverage.json exists
    coverage_file = Path("coverage.json")
    if coverage_file.exists():
        try:
            with open(coverage_file) as f:
                data = json.load(f)

            total_coverage = data.get("totals", {}).get("percent_covered", 0)
            print(f"Overall Test Coverage: {total_coverage:.2f}%")
            print(f"Total Statements: {data.get('totals', {}).get('num_statements', 0)}")
            print(f"Missing Statements: {data.get('totals', {}).get('num_missing', 0)}")

            # Show per-file coverage for main modules
            print("\nKey Module Coverage:")
            files = data.get("files", {})
            for filepath, file_data in list(files.items())[:10]:
                if "test" not in filepath and "venv" not in filepath:
                    coverage = file_data.get("summary", {}).get("percent_covered", 0)
                    print(f"  {filepath}: {coverage:.1f}%")

            return {"success": True, "coverage": total_coverage}
        except Exception as e:
            print(f"Error reading coverage.json: {e}")
            return {"success": False, "error": str(e)}
    else:
        print("No coverage.json found. Run: pytest --cov=. --cov-report=json")
        return {"success": False, "message": "Coverage file not found"}


def security_scan():
    """Run Bandit security scan"""
    print_section("Security Vulnerabilities (Bandit)")
    output, code = run_command(["bandit", "-r", ".", "-c", "pyproject.toml", "-f", "screen"])
    # Print summary only
    lines = output.split("\n")
    summary_start = False
    for line in lines:
        if "Run metrics:" in line or summary_start:
            summary_start = True
            print(line)
    return {"success": code == 0, "output": output}


def ruff_lint_stats():
    """Get Ruff linting statistics"""
    print_section("Linting Issues (Ruff)")
    output, code = run_command(["ruff", "check", ".", "--statistics"])
    print(output)
    return {"success": True, "output": output}


def generate_summary(results: dict):
    """Generate summary report"""
    print_section("METRICS SUMMARY")

    print("Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("\nMetrics Status:")

    for metric, result in results.items():
        status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
        print(f"  {metric}: {status}")

    print("\nRecommendations:")
    print("  - Cyclomatic Complexity: Keep functions under 10")
    print("  - Maintainability Index: Aim for >65 (good), >85 (excellent)")
    print("  - Test Coverage: Target 80%+ for critical code")
    print("  - Type Coverage: Gradually increase to 90%+")
    print("  - Security: Address all high/medium severity issues")

    print("\nFor detailed analysis:")
    print("  - Radon: https://radon.readthedocs.io/")
    print("  - Lizard: https://github.com/terryyin/lizard")
    print("  - MyPy: https://mypy.readthedocs.io/")


def main():
    """Run all metrics and generate report"""
    print("=" * 80)
    print(" CODE QUALITY METRICS REPORT")
    print("=" * 80)
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {}

    # Run all metrics
    results["Cyclomatic Complexity"] = radon_cyclomatic_complexity()
    results["Maintainability Index"] = radon_maintainability_index()
    results["Halstead Metrics"] = radon_halstead_metrics()
    results["Lines of Code"] = radon_raw_metrics()
    results["Cognitive Complexity"] = lizard_complexity()
    results["Type Coverage"] = mypy_type_coverage()
    results["Test Coverage"] = test_coverage()
    results["Security Scan"] = security_scan()
    results["Linting Stats"] = ruff_lint_stats()

    # Generate summary
    generate_summary(results)

    print("\n" + "=" * 80)
    print(" Report complete!")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
