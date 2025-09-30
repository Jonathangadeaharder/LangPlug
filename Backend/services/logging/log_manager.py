"""
Log Manager Service
Handles core logging operations (log, log_with_context, log_error, log_performance, etc.)
"""

import json
import contextlib
import queue
from dataclasses import asdict
from datetime import datetime
from typing import Any


class LogManagerService:
    """Service for core logging operations and utilities"""

    def __init__(self, get_logger_func, config):
        """
        Initialize log manager service
        
        Args:
            get_logger_func: Function to get logger instances
            config: LogConfig instance
        """
        self.get_logger = get_logger_func
        self.config = config
        self._correlation_id = None
        self._stats = {
            "total_logs": 0,
            "errors": 0,
            "warnings": 0
        }
        self._log_queue = None

    def log(self, message: str, level):
        """Log a message at the specified level"""
        from ..loggingservice.logging_service import LogLevel
        
        self._stats["total_logs"] += 1
        if level == LogLevel.ERROR:
            self._stats["errors"] += 1
        elif level == LogLevel.WARNING:
            self._stats["warnings"] += 1

        logger = self.get_logger("app")

        if level == LogLevel.DEBUG:
            logger.debug(message)
        elif level == LogLevel.INFO:
            logger.info(message)
        elif level == LogLevel.WARNING:
            logger.warning(message)
        elif level == LogLevel.ERROR:
            logger.error(message)
        elif level == LogLevel.CRITICAL:
            logger.critical(message)

    def log_with_context(self, message: str, level, context):
        """Log a message with context information"""
        context_str = f"[{context.user_id or 'N/A'}][{context.session_id or 'N/A'}]"
        full_message = f"{context_str} {message}"
        self.log(full_message, level)

    def log_error(self, message: str, exception=None):
        """Log an error message with optional exception"""
        from ..loggingservice.logging_service import LogLevel
        
        if exception:
            error_msg = f"{message}: {str(exception)}"
        else:
            error_msg = message
        try:
            self.log(error_msg, LogLevel.ERROR)
        except Exception:
            import sys
            print(f"EMERGENCY LOG: {error_msg}", file=sys.stderr)

    def log_exception(self, logger_name: str, error: Exception, context: dict[str, Any] | None = None):
        """Log errors with full context and stack traces"""
        logger = self.get_logger(logger_name)

        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }

        if context:
            log_data.update(context)

        logger.error(f"Error: {type(error).__name__}: {error}",
                    extra=log_data, exc_info=True)

    def log_performance(self, operation: str, duration_ms: float, success: bool, metadata: dict = None):
        """Log performance metrics"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Performance: {operation} took {duration_ms}ms - {status}"
        if metadata:
            message += f" - {metadata}"
        
        from ..loggingservice.logging_service import LogLevel
        self.log(message, LogLevel.INFO)

    def log_structured(self, message: str, data: dict):
        """Log structured data"""
        formatted_data = json.dumps(data, indent=2)
        full_message = f"{message}\n{formatted_data}"
        
        from ..loggingservice.logging_service import LogLevel
        self.log(full_message, LogLevel.INFO)

    def log_batch(self, messages: list):
        """Log multiple messages in batch"""
        from ..loggingservice.logging_service import LogLevel
        for message in messages:
            self.log(message, LogLevel.INFO)

    def log_masked(self, message: str, data: dict):
        """Log data with sensitive fields masked"""
        masked_data = data.copy()
        for field in self.config.mask_sensitive_fields:
            if field in masked_data:
                masked_data[field] = "***MASKED***"
        self.log_structured(message, masked_data)

    @contextlib.contextmanager
    def with_correlation_id(self, correlation_id: str):
        """Context manager for correlation ID"""
        old_id = self._correlation_id
        self._correlation_id = correlation_id
        try:
            yield
        finally:
            self._correlation_id = old_id

    def setup_async_logging(self):
        """Setup async logging with queue"""
        self._log_queue = queue.Queue()

    def get_stats(self) -> dict:
        """Get logging statistics"""
        return self._stats.copy()

    def _create_log_record(self, level, message: str, context=None, extra_data: dict = None):
        """Create a log record structure"""
        from ..loggingservice.logging_service import LogRecord
        return LogRecord(
            timestamp=datetime.now(),
            level=level.name,
            message=message,
            context=context,
            extra_data=extra_data or {}
        )

    def _format_log_record(self, record) -> str:
        """Format a log record based on configuration"""
        from ..loggingservice.logging_service import LogFormat
        
        if self.config.format_type == LogFormat.JSON:
            return json.dumps({
                "timestamp": record.timestamp.isoformat(),
                "level": record.level,
                "message": record.message,
                "context": asdict(record.context) if record.context else None,
                "extra": record.extra_data
            })
        elif self.config.format_type == LogFormat.SIMPLE:
            return f"{record.level}: {record.message}"
        else:
            timestamp = record.timestamp.isoformat() if self.config.include_timestamps else ""
            return f"{timestamp} [{record.level}] {record.message}"


# Service will be instantiated by facade with proper dependencies
