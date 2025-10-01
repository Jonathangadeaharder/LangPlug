"""
Test fixture validation and cleanup automation
"""

import asyncio
import weakref
from functools import wraps
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class FixtureValidator:
    """Validates test fixtures and ensures proper cleanup"""

    def __init__(self):
        self.tracked_mocks: set[weakref.ReferenceType] = set()
        self.active_patches: list[Any] = []

    def track_mock(self, mock_obj: Any) -> Any:
        """Track a mock object for cleanup validation"""
        if hasattr(mock_obj, "_mock_name") or isinstance(mock_obj, (AsyncMock, MagicMock)):
            self.tracked_mocks.add(weakref.ref(mock_obj))
        return mock_obj

    def validate_mock_cleanup(self) -> dict[str, Any]:
        """Validate that mocks were properly cleaned up"""
        alive_mocks = []
        for mock_ref in self.tracked_mocks:
            mock_obj = mock_ref()
            if mock_obj is not None:
                alive_mocks.append(mock_obj)

        return {
            "total_tracked": len(self.tracked_mocks),
            "still_alive": len(alive_mocks),
            "cleanup_rate": (len(self.tracked_mocks) - len(alive_mocks)) / len(self.tracked_mocks)
            if self.tracked_mocks
            else 1.0,
        }

    def cleanup_patches(self) -> None:
        """Clean up all active patches"""
        for patch_obj in self.active_patches:
            if hasattr(patch_obj, "stop"):
                patch_obj.stop()
        self.active_patches.clear()


class TestHealthMonitor:
    """Monitor test health and performance metrics"""

    def __init__(self):
        self.test_metrics: dict[str, dict[str, Any]] = {}
        self.failure_patterns: list[dict[str, Any]] = []

    def record_test_metrics(self, test_name: str, metrics: dict[str, Any]) -> None:
        """Record metrics for a test"""
        self.test_metrics[test_name] = {
            "execution_time": metrics.get("execution_time", 0),
            "memory_usage": metrics.get("memory_usage", 0),
            "mock_count": metrics.get("mock_count", 0),
            "database_queries": metrics.get("database_queries", 0),
            "status": metrics.get("status", "unknown"),
        }

    def analyze_failure_patterns(self) -> dict[str, Any]:
        """Analyze common failure patterns"""
        failures_by_type = {}
        failures_by_module = {}

        for failure in self.failure_patterns:
            error_type = failure.get("error_type", "unknown")
            module = failure.get("module", "unknown")

            failures_by_type[error_type] = failures_by_type.get(error_type, 0) + 1
            failures_by_module[module] = failures_by_module.get(module, 0) + 1

        return {
            "total_failures": len(self.failure_patterns),
            "by_type": failures_by_type,
            "by_module": failures_by_module,
            "most_common_error": max(failures_by_type.items(), key=lambda x: x[1]) if failures_by_type else None,
        }


# Global instances
fixture_validator = FixtureValidator()
health_monitor = TestHealthMonitor()


@pytest.fixture(scope="function", autouse=True)
def test_cleanup_validator():
    """Automatic fixture that validates cleanup after each test"""
    # Setup
    len(fixture_validator.tracked_mocks)

    yield fixture_validator

    # Teardown and validation
    cleanup_stats = fixture_validator.validate_mock_cleanup()
    fixture_validator.cleanup_patches()

    # Log cleanup statistics for monitoring
    if cleanup_stats["cleanup_rate"] < 0.8:  # Less than 80% cleanup
        pytest.warn(f"Poor mock cleanup detected: {cleanup_stats}")


@pytest.fixture(scope="function")
def isolated_mock_session():
    """Provide a completely isolated mock session for database tests"""
    from tests.base import DatabaseTestBase

    mock_session = DatabaseTestBase.create_mock_session()
    fixture_validator.track_mock(mock_session)

    yield mock_session

    # Explicit cleanup
    if hasattr(mock_session, "close"):
        asyncio.create_task(mock_session.close())


@pytest.fixture(scope="function")
def health_monitored_test():
    """Monitor test health metrics"""
    import os
    import time

    import psutil

    start_time = time.time()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss

    yield health_monitor

    # Record metrics
    end_time = time.time()
    end_memory = process.memory_info().rss

    test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown")
    health_monitor.record_test_metrics(
        test_name,
        {"execution_time": end_time - start_time, "memory_usage": end_memory - start_memory, "status": "completed"},
    )


def validate_async_fixture(fixture_func):
    """Decorator to validate async fixtures"""

    @wraps(fixture_func)
    async def wrapper(*args, **kwargs):
        # Pre-execution validation
        if not asyncio.iscoroutinefunction(fixture_func):
            raise ValueError(f"Fixture {fixture_func.__name__} is not async but decorated with validate_async_fixture")

        # Execute fixture
        result = await fixture_func(*args, **kwargs)

        # Post-execution validation
        if hasattr(result, "__aenter__"):
            # Context manager validation
            try:
                async with result:
                    pass
            except Exception as e:
                pytest.warn(f"Async context manager validation failed for {fixture_func.__name__}: {e}")

        return result

    return wrapper


def require_clean_state(test_func):
    """Decorator that ensures tests start with clean state"""

    @wraps(test_func)
    def wrapper(*args, **kwargs):
        # Pre-test validation
        import gc

        gc.collect()  # Force garbage collection

        # Check for leaked mocks from previous tests
        leaked_mocks = fixture_validator.validate_mock_cleanup()
        if leaked_mocks["still_alive"] > 0:
            pytest.warn(f"Detected {leaked_mocks['still_alive']} leaked mocks from previous tests")

        # Execute test
        result = test_func(*args, **kwargs)

        return result

    return wrapper


class DatabaseTestValidator:
    """Validates database test patterns and suggests improvements"""

    @staticmethod
    def validate_session_mock(mock_session: Any) -> dict[str, bool]:
        """Validate that a session mock has the required methods"""
        required_methods = ["execute", "commit", "rollback", "refresh", "add", "delete", "close"]

        validation_results = {}
        for method in required_methods:
            validation_results[method] = hasattr(mock_session, method)

        return validation_results

    @staticmethod
    def suggest_mock_improvements(mock_session: Any) -> list[str]:
        """Suggest improvements for mock session setup"""
        suggestions = []

        validation_results = DatabaseTestValidator.validate_session_mock(mock_session)
        missing_methods = [method for method, exists in validation_results.items() if not exists]

        if missing_methods:
            suggestions.append(f"Add missing methods: {missing_methods}")

        if hasattr(mock_session, "execute"):
            if not hasattr(mock_session.execute, "side_effect") and not hasattr(mock_session.execute, "return_value"):
                suggestions.append("Configure execute method with return_value or side_effect")

        if not hasattr(mock_session, "_mock_result"):
            suggestions.append("Add _mock_result attribute for easier result customization")

        return suggestions


# Pytest plugin hooks for automatic validation
def pytest_runtest_setup(item):
    """Hook called before each test is run"""
    # Reset tracking for each test
    fixture_validator.tracked_mocks.clear()


def pytest_runtest_teardown(item):
    """Hook called after each test is run"""
    # Validate cleanup
    cleanup_stats = fixture_validator.validate_mock_cleanup()

    if cleanup_stats["cleanup_rate"] < 0.5:  # Less than 50% cleanup
        health_monitor.failure_patterns.append(
            {
                "test_name": item.name,
                "error_type": "poor_cleanup",
                "module": item.module.__name__ if item.module else "unknown",
                "cleanup_rate": cleanup_stats["cleanup_rate"],
            }
        )


def pytest_sessionfinish(session, exitstatus):
    """Hook called when the test session finishes"""
    # Generate final report
    failure_analysis = health_monitor.analyze_failure_patterns()

    print("\n" + "=" * 50)
    print("TEST INFRASTRUCTURE HEALTH REPORT")
    print("=" * 50)

    if failure_analysis["total_failures"] > 0:
        print(f"Total infrastructure issues detected: {failure_analysis['total_failures']}")
        print(f"Most common issue: {failure_analysis['most_common_error']}")
        print("\nIssues by module:")
        for module, count in failure_analysis["by_module"].items():
            print(f"  {module}: {count}")
    else:
        print("No infrastructure issues detected! ✓")

    print("=" * 50)
