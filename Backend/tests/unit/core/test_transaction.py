"""
Unit tests for transaction management utilities

Tests the @transactional decorator and TransactionContext for ensuring
database operations are atomic with proper rollback on errors.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.transaction import TransactionContext, transactional


class TestTransactionalDecorator:
    """Test @transactional decorator for automatic transaction management"""

    @pytest.mark.asyncio
    async def test_decorator_finds_session_in_args(self, mock_db_session):
        """Decorator should find AsyncSession in positional arguments"""

        @transactional
        async def test_func(session: AsyncSession, data: str):
            return f"processed: {data}"

        result = await test_func(mock_db_session, "test_data")

        assert result == "processed: test_data"
        mock_db_session.begin_nested.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_finds_session_in_kwargs(self, mock_db_session):
        """Decorator should find AsyncSession in keyword arguments"""

        @transactional
        async def test_func(data: str, session: AsyncSession = None):
            return f"processed: {data}"

        result = await test_func(data="test_data", session=mock_db_session)

        assert result == "processed: test_data"
        mock_db_session.begin_nested.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_commits_on_success(self):
        """Decorator should commit transaction on successful function execution"""
        mock_session = Mock(spec=AsyncSession)
        mock_nested = AsyncMock()
        mock_session.begin_nested = Mock(return_value=mock_nested)

        @transactional
        async def test_func(session: AsyncSession):
            return "success"

        result = await test_func(mock_session)

        assert result == "success"
        # Verify context manager was entered and exited
        mock_nested.__aenter__.assert_called_once()
        mock_nested.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_rolls_back_on_exception(self):
        """Decorator should rollback transaction when exception occurs"""
        mock_session = Mock(spec=AsyncSession)
        mock_nested = AsyncMock()
        mock_session.begin_nested = Mock(return_value=mock_nested)

        @transactional
        async def test_func(session: AsyncSession):
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await test_func(mock_session)

        # Verify context manager was entered and exited (with exception)
        mock_nested.__aenter__.assert_called_once()
        mock_nested.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_without_session_logs_warning(self):
        """Decorator should log warning and execute normally if no session found"""
        with patch("core.transaction.logger") as mock_logger:

            @transactional
            async def test_func(data: str):
                return f"processed: {data}"

            result = await test_func("test_data")

            assert result == "processed: test_data"
            mock_logger.warning.assert_called()
            assert "No AsyncSession found" in str(mock_logger.warning.call_args)

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Decorator should preserve original function name and docstring"""

        @transactional
        async def my_database_function(session: AsyncSession, value: int):
            """This is a database function"""
            return value * 2

        assert my_database_function.__name__ == "my_database_function"
        assert "database function" in my_database_function.__doc__

    @pytest.mark.asyncio
    async def test_decorator_with_multiple_args_finds_session(self, mock_db_session):
        """Decorator should find session among multiple arguments"""

        @transactional
        async def test_func(arg1: str, arg2: int, session: AsyncSession, arg3: bool):
            return f"{arg1}-{arg2}-{arg3}"

        result = await test_func("test", 42, mock_db_session, True)

        assert result == "test-42-True"
        mock_db_session.begin_nested.assert_called_once()


class TestTransactionContext:
    """Test TransactionContext context manager"""

    @pytest.mark.asyncio
    async def test_context_manager_commits_on_success(self):
        """Context manager should commit transaction on successful exit"""
        mock_session = Mock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_session.begin_nested = AsyncMock(return_value=mock_transaction)

        async with TransactionContext(mock_session) as ctx:
            pass  # Successful execution

        mock_session.begin_nested.assert_called_once()
        mock_transaction.commit.assert_called_once()
        mock_transaction.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_rolls_back_on_exception(self):
        """Context manager should rollback transaction on exception"""
        mock_session = Mock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_session.begin_nested = AsyncMock(return_value=mock_transaction)

        with pytest.raises(ValueError, match="Test error"):
            async with TransactionContext(mock_session):
                raise ValueError("Test error")

        mock_session.begin_nested.assert_called_once()
        mock_transaction.commit.assert_not_called()
        mock_transaction.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_does_not_suppress_exception(self):
        """Context manager should not suppress exceptions (return False from __aexit__)"""
        mock_session = Mock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_session.begin_nested = AsyncMock(return_value=mock_transaction)

        with pytest.raises(RuntimeError, match="Critical error"):
            async with TransactionContext(mock_session):
                raise RuntimeError("Critical error")

        # Exception should have propagated
        mock_transaction.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_logs_rollback(self):
        """Context manager should log when rolling back transaction"""
        mock_session = Mock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_session.begin_nested = AsyncMock(return_value=mock_transaction)

        with patch("core.transaction.logger") as mock_logger:
            with pytest.raises(ValueError):
                async with TransactionContext(mock_session):
                    raise ValueError("Test error")

            mock_logger.error.assert_called()
            assert "rolled back" in str(mock_logger.error.call_args).lower()


class TestNestedTransactions:
    """Test nested transaction (savepoint) behavior"""

    @pytest.mark.asyncio
    async def test_decorator_uses_savepoint_for_nesting(self, mock_db_session):
        """Decorator should use begin_nested() which creates savepoints"""

        @transactional
        async def test_func(session: AsyncSession):
            return "success"

        await test_func(mock_db_session)

        # Should call begin_nested, not begin
        mock_db_session.begin_nested.assert_called_once()


class TestRealWorldScenarios:
    """Test realistic database operation scenarios"""

    @pytest.mark.asyncio
    async def test_multiple_db_operations_in_transaction(self, mock_db_session):
        """Multiple operations should be wrapped in single transaction"""

        @transactional
        async def create_user_with_profile(session: AsyncSession, username: str):
            # Simulate creating user
            session.add({"username": username})
            # Simulate creating profile
            await session.execute("INSERT INTO profile...")
            return "created"

        result = await create_user_with_profile(mock_db_session, "testuser")

        assert result == "created"
        mock_db_session.begin_nested.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_rollback_on_error(self):
        """Operations before error should rollback when exception occurs"""
        mock_session = Mock(spec=AsyncSession)
        mock_nested = AsyncMock()
        mock_session.begin_nested = Mock(return_value=mock_nested)
        mock_session.add = Mock()

        @transactional
        async def failing_operation(session: AsyncSession):
            session.add({"item": "1"})
            session.add({"item": "2"})
            raise RuntimeError("Database constraint violation")

        with pytest.raises(RuntimeError):
            await failing_operation(mock_session)

        # Both adds should have been called
        assert mock_session.add.call_count == 2
        # But transaction should have been rolled back
        mock_nested.__aexit__.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_decorator_with_no_arguments(self):
        """Decorator should handle functions with no arguments"""

        @transactional
        async def test_func():
            return "no args"

        with patch("core.transaction.logger") as mock_logger:
            result = await test_func()

            assert result == "no args"
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_decorator_with_self_parameter(self, mock_db_session):
        """Decorator should work with class methods (self parameter)"""

        class MyService:
            def __init__(self, session: AsyncSession):
                self.session = session

            @transactional
            async def process_data(self, session: AsyncSession, data: str):
                return f"processed: {data}"

        service = MyService(mock_db_session)
        result = await service.process_data(mock_db_session, "test")

        assert result == "processed: test"
        mock_db_session.begin_nested.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_none_session(self):
        """Context manager should handle None session gracefully"""
        # This should raise an AttributeError when trying to call begin_nested
        with pytest.raises(AttributeError):
            async with TransactionContext(None):
                pass
