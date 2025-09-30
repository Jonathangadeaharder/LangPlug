"""
Log Config Manager Service
Handles configuration management and statistics
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any


class LogConfigManagerService:
    """Service for configuration and statistics management"""

    def __init__(self, config, loggers_dict):
        """
        Initialize config manager service
        
        Args:
            config: LogConfig instance
            loggers_dict: Dictionary of active loggers
        """
        self.config = config
        self._loggers = loggers_dict

    def get_config(self):
        """Get current logging configuration"""
        return self.config

    def update_config(self, new_config):
        """
        Update logging configuration
        
        Args:
            new_config: New LogConfig instance
            
        Note: Caller should trigger setup_logging() after this
        """
        self.config = new_config

    def get_log_stats(self) -> dict[str, Any]:
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

    def get_stats(self) -> dict[str, Any]:
        """Get logging statistics (alias for get_log_stats)"""
        return self.get_log_stats()


# Service will be instantiated by facade with proper dependencies
