"""Structured logging configuration using structlog"""
import logging
import sys
from typing import Any

import structlog
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    add_log_level,
)
from structlog.stdlib import LoggerFactory

from core.config import settings


def configure_logging():
    """Configure structlog for the application"""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level,
        structlog.stdlib.add_log_level,
        TimeStamper(fmt="iso"),
        StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == "json":
        processors.append(JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Backward compatibility aliases
setup_logging = configure_logging


class JSONFormatter(logging.Formatter):
    """JSON formatter for backward compatibility with tests"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_data[key] = value

        import json
        return json.dumps(log_data)


def log_auth_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    user_id: str,
    success: bool,
    **kwargs
):
    """Log authentication events with structured data"""
    logger.info(
        "Authentication event",
        event_type=event_type,
        user_id=user_id,
        success=success,
        **kwargs
    )


def log_user_action(
    logger: structlog.stdlib.BoundLogger,
    user_id: str,
    action: str,
    resource: str,
    success: bool,
    **kwargs
):
    """Log user actions with structured data"""
    logger.info(
        "User action",
        user_id=user_id,
        action=action,
        resource=resource,
        success=success,
        **kwargs
    )


def log_database_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    table: str,
    duration_ms: float,
    success: bool,
    **kwargs
):
    """Log database operations with structured data"""
    logger.info(
        "Database operation",
        operation=operation,
        table=table,
        duration_ms=duration_ms,
        success=success,
        **kwargs
    )


def log_filter_operation(
    logger: structlog.stdlib.BoundLogger,
    filter_name: str,
    words_processed: int,
    words_filtered: int,
    duration_ms: float,
    user_id: str = None,
    **kwargs
):
    """Log filter operations with structured data"""
    logger.info(
        "Filter operation",
        filter_name=filter_name,
        words_processed=words_processed,
        words_filtered=words_filtered,
        duration_ms=duration_ms,
        user_id=user_id,
        **kwargs
    )


def log_error(
    logger: structlog.stdlib.BoundLogger,
    error: Exception,
    context: dict[str, Any] = None,
    **kwargs
):
    """Log errors with structured data and context"""
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        **kwargs,
        exc_info=True
    )
