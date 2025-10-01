"""
Standardized mock patterns for test consistency
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock


class StandardMockPatterns:
    """Standard mock patterns for consistent testing across the codebase"""

    @staticmethod
    def mock_sqlalchemy_session() -> AsyncMock:
        """Create a standardized SQLAlchemy AsyncSession mock"""
        mock_session = AsyncMock()

        # Standard result mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_result.scalar = AsyncMock(return_value=None)
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(return_value=[])
        mock_result.scalars.return_value.first = MagicMock(return_value=None)
        mock_result.first = MagicMock(return_value=None)
        mock_result.fetchall = MagicMock(return_value=[])
        mock_result.rowcount = 0

        # Session methods
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.delete = MagicMock()
        mock_session.close = AsyncMock()

        # Store reference for customization
        mock_session._mock_result = mock_result

        return mock_session

    @staticmethod
    def mock_fastapi_dependency_context(mock_session: AsyncMock) -> AsyncMock:
        """Create a FastAPI dependency context manager mock"""
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        return mock_context

    @staticmethod
    def mock_auth_user(user_id: int = 1, username: str = "testuser") -> MagicMock:
        """Create a standardized auth user mock"""
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = username
        mock_user.email = f"{username}@example.com"
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.hashed_password = "mock_hash"
        return mock_user

    @staticmethod
    def mock_http_response(status_code: int = 200, json_data: dict[str, Any] | None = None) -> MagicMock:
        """Create a standardized HTTP response mock"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response

    @staticmethod
    def configure_session_query_results(mock_session: AsyncMock, results: dict[str, Any]) -> None:
        """Configure query results for a mock session"""
        mock_result = mock_session._mock_result

        for key, value in results.items():
            if key == "scalar_one_or_none":
                mock_result.scalar_one_or_none.return_value = value
            elif key == "scalar":
                mock_result.scalar.return_value = value
            elif key == "all":
                mock_result.scalars.return_value.all.return_value = value
            elif key == "first":
                mock_result.first.return_value = value
            elif key == "fetchall":
                mock_result.fetchall.return_value = value
            elif key == "rowcount":
                mock_result.rowcount = value

    @staticmethod
    def create_sequential_query_results(results: list[Any]) -> list[AsyncMock]:
        """Create a sequence of query results for multiple execute calls"""
        mock_results = []

        for result in results:
            if isinstance(result, Exception):
                mock_results.append(result)
            elif isinstance(result, dict):
                mock_result = AsyncMock()
                for key, value in result.items():
                    if key == "scalar_one_or_none":
                        mock_result.scalar_one_or_none = AsyncMock(return_value=value)
                    elif key == "scalar":
                        mock_result.scalar = AsyncMock(return_value=value)
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
                mock_results.append(result)

        return mock_results


class TestAssertions:
    """Standard test assertions for common patterns"""

    @staticmethod
    def assert_session_operations(mock_session: AsyncMock, expected_operations: dict[str, int]) -> None:
        """Assert that session operations were called the expected number of times"""
        for operation, expected_count in expected_operations.items():
            if hasattr(mock_session, operation):
                actual_count = getattr(mock_session, operation).call_count
                assert (
                    actual_count == expected_count
                ), f"Expected {operation} to be called {expected_count} times, but it was called {actual_count} times"
            else:
                raise ValueError(f"Unknown session operation: {operation}")

    @staticmethod
    def assert_http_response(response, expected_status: int, expected_keys: list[str] | None = None) -> None:
        """Assert HTTP response status and JSON keys"""
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"

        if expected_keys and response.status_code == 200:
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' in response data"

    @staticmethod
    def assert_mock_called_with_pattern(mock_obj, call_pattern: str) -> None:
        """Assert that a mock was called with arguments matching a pattern"""
        calls = [str(call) for call in mock_obj.call_args_list]
        matching_calls = [call for call in calls if call_pattern in call]
        assert (
            len(matching_calls) > 0
        ), f"Expected mock to be called with pattern '{call_pattern}', but actual calls were: {calls}"
