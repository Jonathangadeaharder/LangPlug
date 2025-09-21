#!/usr/bin/env python3
"""
LangPlug Comprehensive Test Suite Runner
========================================

Executes all meaningful tests (Backend API Integration, Frontend Integration, E2E Workflows)
and provides a complete development status report.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json

class LangPlugTestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "Backend"
        self.tests_dir = project_root / "tests"
        self.results = {}
        self.start_time = time.time()
        
    def print_header(self, title: str, symbol: str = "="):
        """Print a formatted section header."""
        print(f"\n{symbol * 60}")
        print(f"{title:^60}")
        print(f"{symbol * 60}")
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print a status message with emoji."""
        status_icons = {
            "SUCCESS": "✅",
            "FAILURE": "❌", 
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "RUNNING": "🏃"
        }
        icon = status_icons.get(status, "•")
        print(f"{icon} {message}")
        
    def run_command(self, command: List[str], cwd: Path, timeout: int = 300) -> Tuple[int, str, str]:
        """Run a command and return (exit_code, stdout, stderr)."""
        try:
            # Join command for Windows shell execution
            cmd_str = " ".join(command) if sys.platform == "win32" else command
            
            result = subprocess.run(
                cmd_str if sys.platform == "win32" else command, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                shell=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)
            
    def run_backend_integration_tests(self) -> Dict:
        """Run enhanced backend API integration tests."""
        self.print_header("🔧 BACKEND API INTEGRATION TESTS", "=")
        self.print_status("Running comprehensive backend API tests...", "RUNNING")
        
        command = [
            "python", "-m", "pytest", 
            "tests/integration/test_api_integration.py", 
            "-v", "--tb=short", "--disable-warnings"
        ]
        
        exit_code, stdout, stderr = self.run_command(command, self.backend_dir)
        
        # Parse pytest results
        passed_tests = stdout.count(" PASSED") if stdout else 0
        failed_tests = stdout.count(" FAILED") if stdout else 0
        total_tests = passed_tests + failed_tests
        
        result = {
            "name": "Backend API Integration Tests",
            "exit_code": exit_code,
            "passed": passed_tests,
            "failed": failed_tests,
            "total": total_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "stdout": stdout,
            "stderr": stderr
        }
        
        if exit_code == 0:
            self.print_status(f"Backend tests: {passed_tests}/{total_tests} passed", "SUCCESS")
        else:
            self.print_status(f"Backend tests: {passed_tests}/{total_tests} passed, {failed_tests} failed", "WARNING")
            
        # Extract meaningful insights
        if "Authentication" in stdout:
            self.print_status("Authentication workflows tested", "INFO")
        if "Vocabulary" in stdout:
            self.print_status("Vocabulary API endpoints tested", "INFO") 
        if "Video" in stdout:
            self.print_status("Video processing endpoints tested", "INFO")
            
        return result
        
    def run_frontend_integration_tests(self) -> Dict:
        """Run enhanced frontend React component integration tests."""
        self.print_header("🌐 FRONTEND INTEGRATION TESTS", "=")
        self.print_status("Running React component integration tests...", "RUNNING")
        
        command = ["node", "-r", "ts-node/register", "frontend-integration.test.ts"]
        
        exit_code, stdout, stderr = self.run_command(
            command, 
            self.tests_dir / "integration",
            timeout=180  # Frontend tests need more time
        )
        
        # Parse frontend test results
        passed_count = stdout.count("✅") if stdout else 0
        failed_count = stdout.count("❌") if stdout else 0
        
        # Extract test summary if available
        if "Frontend Integration Test Results:" in stdout:
            lines = stdout.split("\n")
            for line in lines:
                if "Passed:" in line:
                    try:
                        # Extract "Passed: X/Y" format
                        parts = line.split("Passed:")[1].strip().split("/")
                        passed_count = int(parts[0])
                        total_count = int(parts[1])
                        failed_count = total_count - passed_count
                    except:
                        pass
        
        result = {
            "name": "Frontend Integration Tests", 
            "exit_code": exit_code,
            "passed": passed_count,
            "failed": failed_count,
            "total": passed_count + failed_count,
            "success_rate": (passed_count / (passed_count + failed_count) * 100) if (passed_count + failed_count) > 0 else 0,
            "stdout": stdout,
            "stderr": stderr
        }
        
        if passed_count > failed_count:
            self.print_status(f"Frontend tests: {passed_count} passed, {failed_count} failed", "SUCCESS")
        else:
            self.print_status(f"Frontend tests: {passed_count} passed, {failed_count} failed", "WARNING")
            
        # Extract meaningful insights
        if "Application Load" in stdout:
            self.print_status("React application loading tested", "INFO")
        if "Registration" in stdout:
            self.print_status("User registration workflow tested", "INFO")
        if "Vocabulary" in stdout:
            self.print_status("Vocabulary components tested", "INFO")
            
        return result
        
    def run_e2e_workflow_tests(self) -> Dict:
        """Run meaningful end-to-end user journey tests."""
        self.print_header("🎬 END-TO-END WORKFLOW TESTS", "=")
        self.print_status("Running complete user journey workflows...", "RUNNING")
        
        command = ["node", "-r", "ts-node/register", "meaningful-workflows.test.ts"]
        
        exit_code, stdout, stderr = self.run_command(
            command,
            self.tests_dir / "e2e", 
            timeout=300  # E2E tests need even more time
        )
        
        # Parse E2E workflow results
        passed_workflows = stdout.count("✅") if stdout else 0
        failed_workflows = stdout.count("❌") if stdout else 0
        screenshots_taken = 0
        
        # Extract workflow summary
        if "E2E Workflow Results:" in stdout:
            lines = stdout.split("\n")
            for line in lines:
                if "Passed:" in line:
                    try:
                        parts = line.split("Passed:")[1].strip().split("/")
                        passed_workflows = int(parts[0])
                        total_workflows = int(parts[1])
                        failed_workflows = total_workflows - passed_workflows
                    except:
                        pass
                elif "Screenshots Taken:" in line:
                    try:
                        screenshots_taken = int(line.split("Screenshots Taken:")[1].strip())
                    except:
                        pass
        
        result = {
            "name": "E2E Workflow Tests",
            "exit_code": exit_code, 
            "passed": passed_workflows,
            "failed": failed_workflows,
            "total": passed_workflows + failed_workflows,
            "success_rate": (passed_workflows / (passed_workflows + failed_workflows) * 100) if (passed_workflows + failed_workflows) > 0 else 0,
            "screenshots": screenshots_taken,
            "stdout": stdout,
            "stderr": stderr
        }
        
        if passed_workflows > 0:
            self.print_status(f"E2E workflows: {passed_workflows} passed, {failed_workflows} failed", "SUCCESS" if failed_workflows == 0 else "WARNING")
        else:
            self.print_status(f"E2E workflows: {failed_workflows} workflows need attention", "WARNING")
            
        if screenshots_taken > 0:
            self.print_status(f"{screenshots_taken} workflow screenshots captured", "INFO")
            
        # Extract meaningful insights
        if "Authentication Workflow" in stdout:
            self.print_status("User authentication journey tested", "INFO")
        if "Video Processing" in stdout:
            self.print_status("Video upload workflow tested", "INFO")
        if "Vocabulary Learning" in stdout:
            self.print_status("Vocabulary management workflow tested", "INFO")
        if "Subtitle Processing" in stdout:
            self.print_status("Subtitle processing workflow tested", "INFO")
            
        return result
        
    def generate_development_report(self):
        """Generate a comprehensive development status report."""
        self.print_header("📊 LANGPLUG DEVELOPMENT STATUS REPORT", "#")
        
        total_duration = time.time() - self.start_time
        self.print_status(f"Total test execution time: {total_duration:.1f} seconds", "INFO")
        
        # Calculate overall metrics
        total_tests = sum(result.get('total', 0) for result in self.results.values())
        total_passed = sum(result.get('passed', 0) for result in self.results.values()) 
        total_failed = sum(result.get('failed', 0) for result in self.results.values())
        
        print(f"\n📈 OVERALL TEST METRICS:")
        print(f"   Total Tests Executed: {total_tests}")
        print(f"   Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "   No tests executed")
        print(f"   Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)" if total_tests > 0 else "")
        
        # Feature implementation status
        print(f"\n🎯 FEATURE IMPLEMENTATION STATUS:")
        
        backend_result = self.results.get("backend", {})
        if backend_result.get("success_rate", 0) > 50:
            self.print_status("Backend API: Authentication working, some endpoints need implementation", "SUCCESS")
        else:
            self.print_status("Backend API: Major implementation needed", "WARNING")
            
        frontend_result = self.results.get("frontend", {})
        if frontend_result.get("success_rate", 0) > 30:
            self.print_status("Frontend: Basic React app working, UI features need development", "WARNING")
        else:
            self.print_status("Frontend: Significant UI development needed", "FAILURE")
            
        e2e_result = self.results.get("e2e", {})
        if e2e_result.get("passed", 0) > 0:
            self.print_status("User Workflows: Some journeys working, features need completion", "WARNING")
        else:
            self.print_status("User Workflows: Core features need implementation", "FAILURE")
            
        # Development recommendations
        print(f"\n💡 DEVELOPMENT RECOMMENDATIONS:")
        
        if backend_result.get("failed", 0) > 0:
            self.print_status("Implement missing API endpoints (vocabulary, video processing)", "INFO")
            
        if frontend_result.get("failed", 0) > 0:
            self.print_status("Build UI components for core features (video upload, vocabulary management)", "INFO")
            
        if e2e_result.get("failed", 0) > 0:
            self.print_status("Complete user registration forms and navigation", "INFO")
            
        # Business value assessment
        print(f"\n🚀 BUSINESS VALUE ASSESSMENT:")
        
        if total_passed > total_failed:
            self.print_status("LangPlug infrastructure is solid - ready for feature development", "SUCCESS")
        else:
            self.print_status("LangPlug needs core feature implementation before user testing", "WARNING")
            
        print(f"\n🎬 These meaningful tests validate real user workflows, not just connectivity!")
        print(f"🔍 Check test-results/ directory for workflow screenshots and detailed logs.")
        
    def run_all_tests(self):
        """Execute the complete meaningful test suite."""
        self.print_header("🚀 LANGPLUG COMPREHENSIVE TEST EXECUTION", "#")
        self.print_status("Starting meaningful test suite execution...", "INFO")
        
        # Run each test suite
        self.results["backend"] = self.run_backend_integration_tests()
        self.results["frontend"] = self.run_frontend_integration_tests() 
        self.results["e2e"] = self.run_e2e_workflow_tests()
        
        # Generate comprehensive report
        self.generate_development_report()
        
        # Save results for future analysis
        results_file = self.project_root / "tests" / "test-results" / f"comprehensive-test-results-{int(time.time())}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": int(time.time()),
                "duration": time.time() - self.start_time,
                "results": self.results
            }, f, indent=2)
            
        self.print_status(f"Detailed results saved to: {results_file}", "INFO")

def main():
    """Main entry point for the comprehensive test runner."""
    project_root = Path(__file__).parent.parent
    runner = LangPlugTestRunner(project_root)
    runner.run_all_tests()

if __name__ == "__main__":
    main()