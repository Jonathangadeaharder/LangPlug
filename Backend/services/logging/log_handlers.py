"""
Log Handlers Service
Handles setup and management of log handlers (console, file, rotating file)
"""

import logging
import logging.handlers
import sys
from pathlib import Path


class LogHandlerService:
    """Service for setting up and managing log handlers"""

    def setup_console_handler(self, logger, level, formatter):
        """Setup console logging handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    def setup_file_handler(self, logger, file_path, level, formatter, max_size_mb=10, backup_count=5):
        """Setup rotating file logging handler"""
        # Create logs directory if needed
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def clear_handlers(self, logger):
        """Clear all handlers from logger"""
        logger.handlers.clear()

    def flush_handlers(self, logger):
        """Flush all handlers"""
        for handler in logger.handlers:
            handler.flush()


# Singleton instance
log_handler_service = LogHandlerService()
