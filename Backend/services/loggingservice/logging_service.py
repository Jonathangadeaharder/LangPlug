"""
Centralized Logging Service for A1Decider (Facade)
Provides structured logging with multiple output formats and destinations
Delegates to focused sub-services for better separation of concerns
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# Sub-services
from services.logging.log_formatter import log_formatter_service, StructuredLogFormatter
from services.logging.log_handlers import log_handler_service
from services.logging.domain_logger import DomainLoggerService
from services.logging.log_manager import LogManagerService
from services.logging.log_config_manager import LogConfigManagerService


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
    include_caller_info: bool = False
    include_thread_info: bool = False
    include_process_info: bool = False

    # Service-specific settings
    log_database_queries: bool = False
    log_authentication_events: bool = True
    log_filter_operations: bool = False
    log_user_actions: bool = True
    mask_sensitive_fields: list = field(default_factory=list)


@dataclass
class LogContext:
    """Context information for structured logging"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class LogRecord:
    """Custom log record for structured logging"""
    timestamp: Any
    level: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line: Optional[int] = None
    context: Optional[LogContext] = None
    extra_data: Optional[dict] = None


class LoggingService:
    """
    Centralized logging service facade
    Delegates to specialized sub-services following Single Responsibility Principle
    """

    _instance: Optional['LoggingService'] = None
    _initialized: bool = False

    def __init__(self, config: LogConfig | None = None):
        # Allow direct instantiation during testing
        import sys
        if 'pytest' not in sys.modules and LoggingService._initialized and LoggingService._instance:
            raise RuntimeError("LoggingService is a singleton. Use get_instance() instead.")

        self.config = config or LogConfig()
        self._loggers: dict[str, logging.Logger] = {}
        self._logger = logging.getLogger(__name__)

        # Initialize sub-services
        self.formatter_service = log_formatter_service
        self.handler_service = log_handler_service
        self.domain_logger = DomainLoggerService(self.get_logger, self.config)
        self.log_manager = LogManagerService(self.get_logger, self.config)
        self.config_manager = LogConfigManagerService(self.config, self._loggers)

        self._setup_logging()
        LoggingService._instance = self
        LoggingService._initialized = True

    @classmethod
    def get_instance(cls, config: LogConfig | None = None) -> 'LoggingService':
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
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.level.value)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Get formatter
        formatter = self.formatter_service.create_formatter(self.config.format_type)

        # Setup handlers
        if self.config.console_enabled:
            self.handler_service.setup_console_handler(root_logger, self.config.level.value, formatter)

        if self.config.file_enabled:
            self.handler_service.setup_file_handler(
                root_logger,
                self.config.log_file_path,
                self.config.level.value,
                formatter,
                self.config.max_file_size_mb,
                self.config.backup_count
            )

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific service/module"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    # Configuration & Stats Management (delegate to config_manager)
    def update_config(self, new_config: LogConfig):
        """Update logging configuration at runtime"""
        self.config_manager.update_config(new_config)
        self.config = new_config
        self._setup_logging()

    def get_log_stats(self) -> dict[str, Any]:
        """Get logging statistics and configuration info"""
        return self.config_manager.get_log_stats()

    def get_stats(self) -> dict:
        """Get logging statistics"""
        return self.log_manager.get_stats()

    # Domain-Specific Logging (delegate to domain_logger)
    def log_authentication_event(self, event_type: str, user_id: str, success: bool,
                                additional_info: dict[str, Any] | None = None):
        """Log authentication-related events"""
        self.domain_logger.log_authentication_event(event_type, user_id, success, additional_info)

    def log_user_action(self, user_id: str, action: str, resource: str,
                       success: bool, additional_info: dict[str, Any] | None = None):
        """Log user actions for audit trails"""
        self.domain_logger.log_user_action(user_id, action, resource, success, additional_info)

    def log_database_operation(self, operation: str, table: str, duration_ms: float,
                              success: bool, additional_info: dict[str, Any] | None = None):
        """Log database operations for performance monitoring"""
        self.domain_logger.log_database_operation(operation, table, duration_ms, success, additional_info)

    def log_filter_operation(self, filter_name: str, words_processed: int,
                           words_filtered: int, duration_ms: float,
                           user_id: str | None = None):
        """Log filter operations for performance and effectiveness monitoring"""
        self.domain_logger.log_filter_operation(filter_name, words_processed, words_filtered, duration_ms, user_id)

    # Core Logging Operations (delegate to log_manager)
    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """Log a message at the specified level"""
        self.log_manager.log(message, level)

    def log_with_context(self, message: str, level: LogLevel, context: LogContext):
        """Log a message with context information"""
        self.log_manager.log_with_context(message, level, context)

    def log_error(self, message: str, exception: Exception = None):
        """Log an error message with optional exception"""
        self.log_manager.log_error(message, exception)

    def log_exception(self, logger_name: str, error: Exception, context: dict[str, Any] | None = None):
        """Log errors with full context and stack traces"""
        self.log_manager.log_exception(logger_name, error, context)

    def log_performance(self, operation: str, duration_ms: float, success: bool, metadata: dict = None):
        """Log performance metrics"""
        self.log_manager.log_performance(operation, duration_ms, success, metadata)

    def log_structured(self, message: str, data: dict):
        """Log structured data"""
        self.log_manager.log_structured(message, data)

    def log_batch(self, messages: list):
        """Log multiple messages in batch"""
        self.log_manager.log_batch(messages)

    def log_masked(self, message: str, data: dict):
        """Log data with sensitive fields masked"""
        self.log_manager.log_masked(message, data)

    def with_correlation_id(self, correlation_id: str):
        """Context manager for correlation ID"""
        return self.log_manager.with_correlation_id(correlation_id)

    def setup_async_logging(self):
        """Setup async logging with queue"""
        self.log_manager.setup_async_logging()

    # Handler Management (delegate to handler_service)
    def clear_handlers(self):
        """Clear all handlers from logger"""
        self.handler_service.clear_handlers(self._logger)

    def flush_logs(self):
        """Force flush all log handlers"""
        self.handler_service.flush_handlers(logging.getLogger())

    # Context Manager Support
    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.flush_logs()

    # Internal methods delegated to sub-services
    def _create_log_record(self, level: LogLevel, message: str, context: LogContext = None, extra_data: dict = None) -> LogRecord:
        """Create a log record structure"""
        return self.log_manager._create_log_record(level, message, context, extra_data)

    def _format_log_record(self, record: LogRecord) -> str:
        """Format a log record based on configuration"""
        return self.log_manager._format_log_record(record)