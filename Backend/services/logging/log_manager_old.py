"""
Log Manager - Manages log configuration and core logging operations
Extracted from logging_service.py for better separation of concerns
"""

import logging
import logging.handlers
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from services.interfaces.base import IService
from .log_formatter import LogLevel, LogFormat, LogFormatter


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
    max_file_size_mb: int = 100
    backup_count: int = 5

    # Advanced settings
    enable_console_colors: bool = True
    enable_structured_logging: bool = False
    buffer_size: int = 0
    flush_interval: float = 5.0

    # Security settings
    mask_sensitive_data: bool = True
    mask_sensitive_fields: list = field(default_factory=list)


class LogManager(IService):
    """Service responsible for log management and configuration"""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config: LogConfig = None):
        self.config = config or LogConfig()
        self.formatter_service = LogFormatter()
        self.loggers = {}
        self._setup_logging()

    @classmethod
    def get_instance(cls, config: LogConfig = None) -> 'LogManager':
        """Get singleton instance of LogManager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (useful for testing)"""
        cls._instance = None

    def _setup_logging(self):
        """Setup logging configuration"""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.level.value)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Setup handlers
        if self.config.console_enabled:
            self._setup_console_handler(root_logger)

        if self.config.file_enabled:
            self._setup_file_handler(root_logger)

    def _setup_console_handler(self, logger: logging.Logger = None):
        """Setup console handler"""
        if logger is None:
            logger = logging.getLogger()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.level.value)

        formatter = self.formatter_service.get_formatter(self.config.format_type)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    def _setup_file_handler(self, logger: logging.Logger = None):
        """Setup rotating file handler"""
        if logger is None:
            logger = logging.getLogger()

        # Ensure log directory exists
        log_path = Path(self.config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.config.log_file_path,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count
        )
        file_handler.setLevel(self.config.level.value)

        formatter = self.formatter_service.get_formatter(self.config.format_type)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance for specified name"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            logger.setLevel(self.config.level.value)
            self.loggers[name] = logger

        return self.loggers[name]

    def update_config(self, new_config: LogConfig):
        """Update logging configuration"""
        self.config = new_config
        self._setup_logging()

    def get_log_stats(self) -> dict[str, Any]:
        """Get logging statistics"""
        return {
            "active_loggers": len(self.loggers),
            "log_level": self.config.level.name,
            "format_type": self.config.format_type.value,
            "console_enabled": self.config.console_enabled,
            "file_enabled": self.config.file_enabled,
            "log_file_path": self.config.log_file_path
        }

    def flush_logs(self):
        """Flush all log handlers"""
        for handler in logging.getLogger().handlers:
            handler.flush()

    def log(self, message: str, level: LogLevel = LogLevel.INFO, logger_name: str = ""):
        """Basic logging method"""
        logger = self.get_logger(logger_name or "app")

        # Convert LogLevel enum to logging level
        log_level = level.value
        logger.log(log_level, message)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check for the log manager service"""
        stats = self.get_log_stats()
        stats.update({
            "service": "LogManager",
            "status": "healthy"
        })
        return stats

    async def initialize(self) -> None:
        """Initialize log manager service resources"""
        pass

    async def cleanup(self) -> None:
        """Cleanup log manager service resources"""
        self.flush_logs()
        # Close all handlers
        for handler in logging.getLogger().handlers:
            handler.close()