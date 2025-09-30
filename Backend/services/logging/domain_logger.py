"""
Domain Logger Service
Handles domain-specific logging operations (authentication, user actions, database, filtering)
"""

import logging
from datetime import datetime
from typing import Any


class DomainLoggerService:
    """Service for domain-specific logging operations"""

    def __init__(self, get_logger_func, config):
        """
        Initialize domain logger service
        
        Args:
            get_logger_func: Function to get logger instances
            config: LogConfig instance
        """
        self.get_logger = get_logger_func
        self.config = config

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def _merge_log_data(self, base_data: dict, additional_info: dict | None) -> dict:
        """Merge additional info into base log data"""
        if additional_info:
            base_data.update(additional_info)
        return base_data

    def _log_with_status(self, logger: logging.Logger, message_success: str,
                        message_failure: str, success: bool, log_data: dict):
        """Log message based on success status"""
        if success:
            logger.info(message_success, extra=log_data)
        else:
            logger.warning(message_failure, extra=log_data)

    def log_authentication_event(self, event_type: str, user_id: str, success: bool,
                                additional_info: dict[str, Any] | None = None):
        """Log authentication-related events"""
        if not self.config.log_authentication_events:
            return

        logger = self.get_logger("auth")

        log_data = self._merge_log_data({
            "event_type": event_type,
            "user_id": user_id,
            "success": success,
            "timestamp": self._get_timestamp()
        }, additional_info)

        self._log_with_status(
            logger,
            f"Auth event: {event_type} for user {user_id}",
            f"Auth event failed: {event_type} for user {user_id}",
            success,
            log_data
        )

    def log_user_action(self, user_id: str, action: str, resource: str,
                       success: bool, additional_info: dict[str, Any] | None = None):
        """Log user actions for audit trails"""
        if not self.config.log_user_actions:
            return

        logger = self.get_logger("user_actions")

        log_data = self._merge_log_data({
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "success": success,
            "timestamp": self._get_timestamp()
        }, additional_info)

        self._log_with_status(
            logger,
            f"User {user_id} {action} {resource}",
            f"User {user_id} failed to {action} {resource}",
            success,
            log_data
        )

    def log_database_operation(self, operation: str, table: str, duration_ms: float,
                              success: bool, additional_info: dict[str, Any] | None = None):
        """Log database operations for performance monitoring"""
        if not self.config.log_database_queries:
            return

        logger = self.get_logger("database")

        log_data = self._merge_log_data({
            "operation": operation,
            "table": table,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": self._get_timestamp()
        }, additional_info)

        level = logging.INFO if success else logging.ERROR
        logger.log(level, f"DB {operation} on {table} took {duration_ms:.2f}ms", extra=log_data)

    def log_filter_operation(self, filter_name: str, words_processed: int,
                           words_filtered: int, duration_ms: float,
                           user_id: str | None = None):
        """Log filter operations for performance and effectiveness monitoring"""
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
            "timestamp": self._get_timestamp()
        }

        if user_id:
            log_data["user_id"] = user_id

        logger.info(f"Filter {filter_name} processed {words_processed} words, "
                   f"filtered {words_filtered} ({filter_rate:.2%})", extra=log_data)


# Service will be instantiated by facade with proper dependencies
