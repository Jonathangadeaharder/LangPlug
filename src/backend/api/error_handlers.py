"""
Standardized error handling utilities for API routes.

This module provides decorators and helpers to eliminate repetitive error handling code.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from core.config.logging_config import get_logger

logger = get_logger(__name__)


def handle_api_errors(
    operation_name: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, log_traceback: bool = True
):
    """
    Decorator to standardize error handling in API route handlers.

    This eliminates repetitive try-except-logger-raise patterns throughout the codebase.

    Args:
        operation_name: Human-readable name of the operation for logging/error messages
        status_code: HTTP status code to return on error (default: 500)
        log_traceback: Whether to include full traceback in logs (default: True)

    Example:
        @router.get("/example")
        @handle_api_errors("retrieving example data", status_code=404)
        async def get_example():
            return await some_operation()

    Before:
        async def get_stats():
            try:
                return await fetch_stats()
            except Exception as e:
                logger.error("Error retrieving stats", error=str(e), exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Error retrieving stats: {e!s}"
                ) from e

    After:
        @handle_api_errors("retrieving stats")
        async def get_stats():
            return await fetch_stats()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPException without wrapping
                raise
            except Exception as e:
                error_msg = f"Error {operation_name}: {e!s}"
                logger.error(error_msg, exc_info=log_traceback)
                raise HTTPException(status_code=status_code, detail=error_msg) from e

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPException without wrapping
                raise
            except Exception as e:
                error_msg = f"Error {operation_name}: {e!s}"
                logger.error(error_msg, exc_info=log_traceback)
                raise HTTPException(status_code=status_code, detail=error_msg) from e

        # Return appropriate wrapper based on whether function is async
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def raise_not_found(resource: str, identifier: str | None = None) -> None:
    """
    Raise a standardized 404 HTTPException.

    Args:
        resource: Type of resource not found (e.g., "Word", "User", "Video")
        identifier: Optional identifier of the resource (e.g., ID, name)

    Example:
        if not word:
            raise_not_found("Word", word_text)
    """
    detail = f"{resource} not found"
    if identifier:
        detail = f"{resource} not found: {identifier}"

    logger.warning("Not found", detail=detail)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_validation_error(message: str, field: str | None = None) -> None:
    """
    Raise a standardized 422 validation error.

    Args:
        message: Validation error message
        field: Optional field name that failed validation

    Example:
        if level not in VALID_LEVELS:
            raise_validation_error(f"Invalid level. Must be one of {VALID_LEVELS}", "level")
    """
    detail = message
    if field:
        detail = f"Validation error for '{field}': {message}"

    logger.warning("Validation error", detail=detail)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def raise_bad_request(message: str) -> None:
    """
    Raise a standardized 400 bad request error.

    Args:
        message: Error message describing what's wrong with the request

    Example:
        if not concept_id and not word:
            raise_bad_request("Either concept_id or word must be provided")
    """
    logger.warning("Bad request", message=message)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def raise_unauthorized(message: str = "Authentication required") -> None:
    """
    Raise a standardized 401 unauthorized error.

    Args:
        message: Error message (default: "Authentication required")
    """
    logger.warning("Unauthorized", message=message)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


def raise_forbidden(message: str = "Insufficient permissions") -> None:
    """
    Raise a standardized 403 forbidden error.

    Args:
        message: Error message (default: "Insufficient permissions")
    """
    logger.warning("Forbidden", message=message)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def raise_conflict(resource: str, identifier: str, message: str | None = None) -> None:
    """
    Raise a standardized 409 conflict error.

    Args:
        resource: Type of resource (e.g., "User", "Video")
        identifier: Identifier of the conflicting resource
        message: Optional additional context

    Example:
        if existing_user:
            raise_conflict("User", username, "Username already taken")
    """
    detail = f"{resource} already exists: {identifier}"
    if message:
        detail = f"{detail}. {message}"

    logger.warning("Conflict", detail=detail)
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
