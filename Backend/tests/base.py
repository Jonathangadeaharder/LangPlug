"""
Base test classes and utilities for robust database testing
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseTestBase:
    """Base class for database-dependent tests with proper mock isolation"""

    @staticmethod
    def create_mock_session() -> AsyncMock:
        """
        Create a properly isolated mock database session

        Returns:
            AsyncMock: Fully configured mock session with proper isolation
        """
        mock_session = AsyncMock(spec=AsyncSession)

        # Create default mock result that can be customized per test
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)  # Sync method
        mock_result.scalar = MagicMock(return_value=None)  # Sync method
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        mock_result.scalars.return_value.first = MagicMock(return_value=None)
        mock_result.first = MagicMock(return_value=None)
        mock_result.fetchall = MagicMock(return_value=[])
        mock_result.rowcount = 0

        # Configure session methods with proper async/sync distinction
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()  # Sync method
        mock_session.delete = MagicMock()  # Sync method
        mock_session.close = AsyncMock()

        # Store reference to mock result for test customization
        mock_session._mock_result = mock_result

        return mock_session

    @staticmethod
    def configure_mock_query_result(mock_session: AsyncMock, query_results: dict[str, Any]) -> None:
        """
        Configure specific query results for a mock session

        Args:
            mock_session: The mock session to configure
            query_results: Dictionary of query types to their expected results
                          Keys: 'scalar_one_or_none', 'scalar', 'all', 'first', 'fetchall', 'rowcount'
        """
        mock_result = mock_session._mock_result

        if "scalar_one_or_none" in query_results:
            mock_result.scalar_one_or_none.return_value = query_results["scalar_one_or_none"]

        if "scalar" in query_results:
            mock_result.scalar.return_value = query_results["scalar"]

        if "all" in query_results:
            mock_result.scalars.return_value.all.return_value = query_results["all"]

        if "first" in query_results:
            mock_result.first.return_value = query_results["first"]

        if "fetchall" in query_results:
            mock_result.fetchall.return_value = query_results["fetchall"]

        if "rowcount" in query_results:
            mock_result.rowcount = query_results["rowcount"]

    @staticmethod
    def create_mock_execute_sequence(results: list) -> list:
        """
        Create a sequence of mock results for multiple execute calls

        Args:
            results: List of result configurations, each can be:
                    - A dict with query result keys
                    - A mock object
                    - An exception to be raised

        Returns:
            list: List of configured mock results
        """
        mock_results = []

        for result_config in results:
            if isinstance(result_config, Exception):
                mock_results.append(result_config)
            elif isinstance(result_config, dict):
                mock_result = AsyncMock()
                for key, value in result_config.items():
                    if key == "scalar_one_or_none":
                        mock_result.scalar_one_or_none = MagicMock(return_value=value)  # Sync method
                    elif key == "scalar":
                        mock_result.scalar = MagicMock(return_value=value)  # Sync method
                    elif key == "all":
                        mock_result.scalars.return_value.all = MagicMock(return_value=value)
                    elif key == "first":
                        mock_result.first = MagicMock(return_value=value)
                    elif key == "fetchall":
                        mock_result.fetchall = MagicMock(return_value=value)
                    elif key == "rowcount":
                        mock_result.rowcount = value
                mock_results.append(mock_result)
            else:
                mock_results.append(result_config)

        return mock_results

    @staticmethod
    def create_isolated_mock_session() -> AsyncMock:
        """
        Create a completely isolated mock session with enhanced cleanup.

        This method creates a mock session with explicit isolation markers
        and built-in cleanup validation.
        """
        mock_session = DatabaseTestBase.create_mock_session()

        # Add isolation metadata
        mock_session._test_isolation_id = id(mock_session)
        mock_session._test_created_at = __import__("time").time()

        # Track mock calls for pollution detection
        original_execute = mock_session.execute
        call_count = {"count": 0}

        async def tracked_execute(*args, **kwargs):
            call_count["count"] += 1
            return await original_execute(*args, **kwargs)

        mock_session.execute = tracked_execute
        mock_session._test_call_count = call_count

        return mock_session

    @staticmethod
    def validate_mock_isolation(mock_session: AsyncMock) -> bool:
        """
        Validate that a mock session maintains proper isolation.

        Returns True if isolation is maintained, False otherwise.
        """
        try:
            # Check for required isolation metadata
            if not hasattr(mock_session, "_test_isolation_id"):
                return False

            if not hasattr(mock_session, "_test_created_at"):
                return False

            # Check for excessive call accumulation (potential pollution)
            if hasattr(mock_session, "_test_call_count") and mock_session._test_call_count["count"] > 1000:
                import warnings

                warnings.warn(
                    f"Mock session {mock_session._test_isolation_id} has "
                    f"excessive calls ({mock_session._test_call_count['count']}), "
                    "potential pollution detected",
                    UserWarning,
                    stacklevel=2,
                )
                return False

            return True

        except Exception:
            return False


class ServiceTestBase(DatabaseTestBase):
    """Base class for service layer tests with enhanced isolation"""

    @pytest.fixture
    def isolated_mock_session(self):
        """Provide a completely isolated mock session for each test"""
        return self.create_mock_session()

    def assert_session_operations(self, mock_session: AsyncMock, expected_operations: dict[str, int]):
        """
        Assert that specific session operations were called the expected number of times

        Args:
            mock_session: The mock session to check
            expected_operations: Dict mapping operation names to expected call counts
                               e.g., {'add': 1, 'commit': 1, 'rollback': 0}
        """
        for operation, expected_count in expected_operations.items():
            if hasattr(mock_session, operation):
                actual_count = getattr(mock_session, operation).call_count
                assert (
                    actual_count == expected_count
                ), f"Expected {operation} to be called {expected_count} times, but it was called {actual_count} times"
            else:
                raise ValueError(f"Unknown session operation: {operation}")


class RouteTestBase(DatabaseTestBase):
    """Base class for API route tests with database mocking"""

    @staticmethod
    def create_mock_session_context():
        """Create a mock session context manager for route testing"""
        mock_session = DatabaseTestBase.create_mock_session()

        # Create context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        return mock_context, mock_session
