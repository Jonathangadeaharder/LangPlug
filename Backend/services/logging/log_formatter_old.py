"""
Log Formatter - Handles formatting and output for logging
Extracted from logging_service.py for better separation of concerns
"""

import json
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

from services.interfaces.base import IService


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """Log format enumeration"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LogContext:
    """Context information for log entries"""
    user_id: str = ""
    request_id: str = ""
    session_id: str = ""
    operation: str = ""


@dataclass
class LogRecord:
    """Structured log record"""
    timestamp: str = ""
    level: str = ""
    logger_name: str = ""
    message: str = ""
    context: LogContext = field(default_factory=LogContext)
    extra: dict[str, Any] = field(default_factory=dict)


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Extract context information
        context = LogContext(
            user_id=getattr(record, 'user_id', ''),
            request_id=getattr(record, 'request_id', ''),
            session_id=getattr(record, 'session_id', ''),
            operation=getattr(record, 'operation', '')
        )

        # Build structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add context if available
        if any([context.user_id, context.request_id, context.session_id, context.operation]):
            log_entry["context"] = {
                "user_id": context.user_id,
                "request_id": context.request_id,
                "session_id": context.session_id,
                "operation": context.operation
            }

        # Add extra fields if enabled
        if self.include_extra_fields:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                             'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                             'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process', 'getMessage',
                             'user_id', 'request_id', 'session_id', 'operation'}:
                    extra_fields[key] = value

            if extra_fields:
                log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str)


class LogFormatter(IService):
    """Service responsible for log formatting and output"""

    def __init__(self):
        self.formatters = self._setup_formatters()

    def _setup_formatters(self) -> dict[LogFormat, logging.Formatter]:
        """Setup different log formatters"""
        return {
            LogFormat.SIMPLE: logging.Formatter(
                fmt='%(levelname)s - %(message)s'
            ),
            LogFormat.DETAILED: logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ),
            LogFormat.JSON: StructuredLogFormatter(include_extra_fields=True),
            LogFormat.STRUCTURED: StructuredLogFormatter(include_extra_fields=False)
        }

    def get_formatter(self, format_type: LogFormat) -> logging.Formatter:
        """Get formatter for specified format type"""
        return self.formatters.get(format_type, self.formatters[LogFormat.DETAILED])

    def format_message(
        self,
        message: str,
        level: LogLevel,
        logger_name: str = "",
        context: LogContext = None,
        extra: dict[str, Any] = None
    ) -> LogRecord:
        """Format a message into a structured log record"""
        return LogRecord(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            logger_name=logger_name,
            message=message,
            context=context or LogContext(),
            extra=extra or {}
        )

    def mask_sensitive_data(self, data: dict[str, Any], sensitive_fields: list[str]) -> dict[str, Any]:
        """Mask sensitive data in log entries"""
        masked_data = data.copy()

        for field in sensitive_fields:
            if field in masked_data:
                if isinstance(masked_data[field], str):
                    masked_data[field] = "***MASKED***"
                else:
                    masked_data[field] = "***MASKED***"

        return masked_data

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the log formatter service"""
        return {
            "service": "LogFormatter",
            "status": "healthy",
            "formatters": list(self.formatters.keys())
        }

    async def initialize(self) -> None:
        """Initialize log formatter service resources"""
        pass

    async def cleanup(self) -> None:
        """Cleanup log formatter service resources"""
        pass