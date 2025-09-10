"""
Centralized Logging Service for A1Decider
Provides structured logging with multiple output formats and destinations
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict


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
class LogConfig:
    """Configuration for logging service"""
    # Basic settings
    level: LogLevel = LogLevel.INFO
    format_type: LogFormat = LogFormat.DETAILED
    
    # Output destinations
    console_enabled: bool = True
    file_enabled: bool = True
    
    # File settings
    log_file_path: str = "logs/a1decider.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Advanced settings
    include_timestamps: bool = True
    include_thread_info: bool = False
    include_process_info: bool = False
    
    # Service-specific settings
    log_database_queries: bool = False
    log_authentication_events: bool = True
    log_filter_operations: bool = False
    log_user_actions: bool = True


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
        
        # Add thread/process info if available
        if hasattr(record, 'thread') and record.thread:
            log_entry["thread_id"] = record.thread
        if hasattr(record, 'process') and record.process:
            log_entry["process_id"] = record.process
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if enabled
        if self.include_extra_fields:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                             'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                             'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                             'message', 'exc_info', 'exc_text', 'stack_info']:
                    if not key.startswith('_'):
                        log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class LoggingService:
    """
    Centralized logging service for A1Decider
    Provides structured, configurable logging across all services
    """
    
    _instance: Optional['LoggingService'] = None
    _initialized: bool = False
    
    def __init__(self, config: Optional[LogConfig] = None):
        if LoggingService._initialized and LoggingService._instance:
            raise RuntimeError("LoggingService is a singleton. Use get_instance() instead.")
        
        self.config = config or LogConfig()
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
        LoggingService._instance = self
        LoggingService._initialized = True
    
    @classmethod
    def get_instance(cls, config: Optional[LogConfig] = None) -> 'LoggingService':
        """Get singleton instance of logging service"""
        if not cls._instance:
            cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)"""
        cls._instance = None
        cls._initialized = False
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if needed
        if self.config.file_enabled:
            log_dir = Path(self.config.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.level.value)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Setup formatters
        self._setup_formatters()
        
        # Setup handlers
        if self.config.console_enabled:
            self._setup_console_handler(root_logger)
        
        if self.config.file_enabled:
            self._setup_file_handler(root_logger)
    
    def _setup_formatters(self):
        """Setup different log formatters"""
        if self.config.format_type == LogFormat.SIMPLE:
            self.formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s'
            )
        elif self.config.format_type == LogFormat.DETAILED:
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            self.formatter = logging.Formatter(format_str)
        elif self.config.format_type == LogFormat.JSON:
            self.formatter = StructuredLogFormatter(include_extra_fields=True)
        elif self.config.format_type == LogFormat.STRUCTURED:
            self.formatter = StructuredLogFormatter(include_extra_fields=False)
        else:
            # Default to detailed
            self.formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
    
    def _setup_console_handler(self, logger: logging.Logger):
        """Setup console logging handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.level.value)
        
        # Use simpler format for console in non-JSON modes
        if self.config.format_type in [LogFormat.JSON, LogFormat.STRUCTURED]:
            console_handler.setFormatter(self.formatter)
        else:
            console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            console_handler.setFormatter(logging.Formatter(console_format))
        
        logger.addHandler(console_handler)
    
    def _setup_file_handler(self, logger: logging.Logger):
        """Setup file logging handler with rotation"""
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.config.log_file_path,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.config.level.value)
        file_handler.setFormatter(self.formatter)
        logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific service/module
        
        Args:
            name: Logger name (typically module or service name)
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def log_authentication_event(self, event_type: str, user_id: str, success: bool, 
                                additional_info: Optional[Dict[str, Any]] = None):
        """
        Log authentication-related events
        
        Args:
            event_type: Type of auth event (login, logout, register, etc.)
            user_id: User identifier
            success: Whether the event was successful
            additional_info: Additional context information
        """
        if not self.config.log_authentication_events:
            return
        
        logger = self.get_logger("auth")
        
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        # Add structured data to log record
        if success:
            logger.info(f"Auth event: {event_type} for user {user_id}", extra=log_data)
        else:
            logger.warning(f"Auth event failed: {event_type} for user {user_id}", extra=log_data)
    
    def log_user_action(self, user_id: str, action: str, resource: str, 
                       success: bool, additional_info: Optional[Dict[str, Any]] = None):
        """
        Log user actions for audit trails
        
        Args:
            user_id: User performing the action
            action: Action being performed (create, read, update, delete, etc.)
            resource: Resource being acted upon
            success: Whether the action was successful
            additional_info: Additional context information
        """
        if not self.config.log_user_actions:
            return
        
        logger = self.get_logger("user_actions")
        
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        if success:
            logger.info(f"User {user_id} {action} {resource}", extra=log_data)
        else:
            logger.warning(f"User {user_id} failed to {action} {resource}", extra=log_data)
    
    def log_database_operation(self, operation: str, table: str, duration_ms: float,
                              success: bool, additional_info: Optional[Dict[str, Any]] = None):
        """
        Log database operations for performance monitoring
        
        Args:
            operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
            table: Database table affected
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            additional_info: Additional context information
        """
        if not self.config.log_database_queries:
            return
        
        logger = self.get_logger("database")
        
        log_data = {
            "operation": operation,
            "table": table,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        level = logging.INFO if success else logging.ERROR
        logger.log(level, f"DB {operation} on {table} took {duration_ms:.2f}ms", extra=log_data)
    
    def log_filter_operation(self, filter_name: str, words_processed: int, 
                           words_filtered: int, duration_ms: float,
                           user_id: Optional[str] = None):
        """
        Log filter operations for performance and effectiveness monitoring
        
        Args:
            filter_name: Name of the filter
            words_processed: Number of words processed
            words_filtered: Number of words filtered out
            duration_ms: Processing duration in milliseconds
            user_id: User ID if applicable
        """
        if not self.config.log_filter_operations:
            return
        
        logger = self.get_logger("filters")
        
        filter_rate = words_filtered / words_processed if words_processed > 0 else 0
        
        log_data = {
            "filter_name": filter_name,
            "words_processed": words_processed,
            "words_filtered": words_filtered,
            "filter_rate": filter_rate,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id:
            log_data["user_id"] = user_id
        
        logger.info(f"Filter {filter_name} processed {words_processed} words, "
                   f"filtered {words_filtered} ({filter_rate:.2%})", extra=log_data)
    
    def log_error(self, logger_name: str, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log errors with full context and stack traces
        
        Args:
            logger_name: Name of the logger to use
            error: Exception that occurred
            context: Additional context information
        """
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
    
    def update_config(self, new_config: LogConfig):
        """
        Update logging configuration at runtime
        
        Args:
            new_config: New logging configuration
        """
        self.config = new_config
        self._setup_logging()
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics and configuration info
        
        Returns:
            Dictionary with logging statistics
        """
        return {
            "config": asdict(self.config),
            "active_loggers": list(self._loggers.keys()),
            "log_file_exists": Path(self.config.log_file_path).exists() if self.config.file_enabled else False,
            "log_file_size": Path(self.config.log_file_path).stat().st_size if 
                            (self.config.file_enabled and Path(self.config.log_file_path).exists()) else 0
        }
    
    def flush_logs(self):
        """Force flush all log handlers"""
        for handler in logging.getLogger().handlers:
            handler.flush()


# Convenience functions for easy access
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance from the logging service"""
    return LoggingService.get_instance().get_logger(name)


def setup_logging(config: Optional[LogConfig] = None) -> LoggingService:
    """Setup logging service with configuration"""
    return LoggingService.get_instance(config)


def log_auth_event(event_type: str, user_id: str, success: bool, **kwargs):
    """Convenience function for logging authentication events"""
    LoggingService.get_instance().log_authentication_event(
        event_type, user_id, success, kwargs if kwargs else None
    )


def log_user_action(user_id: str, action: str, resource: str, success: bool, **kwargs):
    """Convenience function for logging user actions"""
    LoggingService.get_instance().log_user_action(
        user_id, action, resource, success, kwargs if kwargs else None
    )


def log_error(logger_name: str, error: Exception, **context):
    """Convenience function for logging errors"""
    LoggingService.get_instance().log_error(
        logger_name, error, context if context else None
    )