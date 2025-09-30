"""
Log Handlers - Specialized logging operations for different domains
Extracted from logging_service.py for better separation of concerns
"""

import logging
from typing import Any, Optional

from services.interfaces.base import IService
from .log_formatter import LogLevel, LogContext
from .log_manager import LogManager


class LogHandlers(IService):
    """Service responsible for specialized logging operations"""

    def __init__(self, log_manager: LogManager = None):
        self.log_manager = log_manager or LogManager.get_instance()

    def log_authentication_event(
        self,
        event_type: str,
        user_id: str,
        success: bool,
        ip_address: str = "",
        user_agent: str = "",
        additional_data: dict[str, Any] = None
    ):
        """Log authentication-related events"""
        logger = self.log_manager.get_logger("auth")

        context_data = {
            "event_type": event_type,
            "user_id": user_id,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        if additional_data:
            context_data.update(additional_data)

        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Authentication {event_type}: {'Success' if success else 'Failed'} for user {user_id}"

        logger.log(
            level.value,
            message,
            extra={
                "user_id": user_id,
                "operation": "authentication",
                **context_data
            }
        )

    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success",
        duration_ms: Optional[float] = None,
        additional_data: dict[str, Any] = None
    ):
        """Log user actions and activities"""
        logger = self.log_manager.get_logger("user_activity")

        context_data = {
            "action": action,
            "resource": resource,
            "result": result,
            "user_id": user_id
        }

        if duration_ms is not None:
            context_data["duration_ms"] = duration_ms

        if additional_data:
            context_data.update(additional_data)

        level = LogLevel.INFO if result == "success" else LogLevel.WARNING
        message = f"User {user_id} performed {action} on {resource}: {result}"

        logger.log(
            level.value,
            message,
            extra={
                "user_id": user_id,
                "operation": "user_action",
                **context_data
            }
        )

    def log_database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        affected_rows: int = 0,
        user_id: str = "",
        success: bool = True,
        additional_data: dict[str, Any] = None
    ):
        """Log database operations with performance metrics"""
        logger = self.log_manager.get_logger("database")

        context_data = {
            "operation": operation,
            "table": table,
            "duration_ms": duration_ms,
            "affected_rows": affected_rows,
            "success": success
        }

        if user_id:
            context_data["user_id"] = user_id

        if additional_data:
            context_data.update(additional_data)

        # Determine log level based on performance and success
        if not success:
            level = LogLevel.ERROR
        elif duration_ms > 1000:  # Slow query threshold
            level = LogLevel.WARNING
        else:
            level = LogLevel.INFO

        message = f"Database {operation} on {table}: {duration_ms:.2f}ms, {affected_rows} rows"

        logger.log(
            level.value,
            message,
            extra={
                "operation": "database",
                **context_data
            }
        )

    def log_filter_operation(
        self,
        filter_name: str,
        words_processed: int,
        words_filtered: int,
        duration_ms: float,
        user_id: str = "",
        language: str = "",
        level: str = "",
        success: bool = True,
        additional_data: dict[str, Any] = None
    ):
        """Log filtering operations with metrics"""
        logger = self.log_manager.get_logger("filtering")

        context_data = {
            "filter_name": filter_name,
            "words_processed": words_processed,
            "words_filtered": words_filtered,
            "duration_ms": duration_ms,
            "success": success
        }

        if user_id:
            context_data["user_id"] = user_id
        if language:
            context_data["language"] = language
        if level:
            context_data["level"] = level

        if additional_data:
            context_data.update(additional_data)

        # Determine log level
        log_level = LogLevel.INFO if success else LogLevel.ERROR

        message = f"Filter {filter_name}: {words_filtered}/{words_processed} words in {duration_ms:.2f}ms"

        logger.log(
            log_level.value,
            message,
            extra={
                "operation": "filtering",
                **context_data
            }
        )

    def log_error(
        self,
        logger_name: str,
        error: Exception,
        context: dict[str, Any] = None
    ):
        """Log errors with full context and stack trace"""
        logger = self.log_manager.get_logger(logger_name)

        context_data = {
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        if context:
            context_data.update(context)

        message = f"Error in {logger_name}: {str(error)}"

        logger.error(
            message,
            extra={
                "operation": "error_handling",
                **context_data
            },
            exc_info=True
        )

    def log_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        component: str = "",
        user_id: str = "",
        additional_metrics: dict[str, Any] = None
    ):
        """Log performance metrics"""
        logger = self.log_manager.get_logger("performance")

        context_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            "component": component
        }

        if user_id:
            context_data["user_id"] = user_id

        if additional_metrics:
            context_data.update(additional_metrics)

        # Determine log level based on performance
        if duration_ms > 5000:  # Very slow
            level = LogLevel.WARNING
        elif duration_ms > 1000:  # Slow
            level = LogLevel.INFO
        else:  # Normal
            level = LogLevel.DEBUG

        message = f"Performance: {operation} completed in {duration_ms:.2f}ms"

        logger.log(
            level.value,
            message,
            extra={
                "operation": "performance_monitoring",
                **context_data
            }
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: str = "",
        ip_address: str = "",
        additional_data: dict[str, Any] = None
    ):
        """Log security-related events"""
        logger = self.log_manager.get_logger("security")

        context_data = {
            "event_type": event_type,
            "severity": severity,
            "description": description
        }

        if user_id:
            context_data["user_id"] = user_id
        if ip_address:
            context_data["ip_address"] = ip_address

        if additional_data:
            context_data.update(additional_data)

        # Map severity to log level
        severity_mapping = {
            "low": LogLevel.INFO,
            "medium": LogLevel.WARNING,
            "high": LogLevel.ERROR,
            "critical": LogLevel.CRITICAL
        }
        level = severity_mapping.get(severity.lower(), LogLevel.WARNING)

        message = f"Security event ({severity}): {description}"

        logger.log(
            level.value,
            message,
            extra={
                "operation": "security_monitoring",
                **context_data
            }
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the log handlers service"""
        return {
            "service": "LogHandlers",
            "status": "healthy",
            "log_manager": "available"
        }

    async def initialize(self) -> None:
        """Initialize log handlers service resources"""
        pass

    async def cleanup(self) -> None:
        """Cleanup log handlers service resources"""
        pass