"""
Log Formatter Service  
Handles creation and management of log formatters
"""

import json
import logging
from datetime import datetime


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""

    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if hasattr(record, 'thread') and record.thread:
            log_entry["thread_id"] = record.thread
        if hasattr(record, 'process') and record.process:
            log_entry["process_id"] = record.process

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if self.include_extra_fields:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                             'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                             'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                             'message', 'exc_info', 'exc_text', 'stack_info']:
                    if not key.startswith('_'):
                        log_entry[key] = value

        return json.dumps(log_entry, default=str)


class LogFormatterService:
    """Service for creating and managing log formatters"""

    def create_formatter(self, format_type, include_extra_fields=True):
        """Create formatter based on format type"""
        from ..loggingservice.logging_service import LogFormat
        
        if format_type == LogFormat.SIMPLE:
            return logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        elif format_type == LogFormat.DETAILED:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        elif format_type == LogFormat.JSON:
            return StructuredLogFormatter(include_extra_fields=True)
        elif format_type == LogFormat.STRUCTURED:
            return StructuredLogFormatter(include_extra_fields=False)
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )


# Singleton instance
log_formatter_service = LogFormatterService()
