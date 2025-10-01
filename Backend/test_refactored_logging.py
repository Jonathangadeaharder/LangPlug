"""
Architecture Verification Tests for Refactored Logging Service
Verifies the facade pattern and service separation are correct
"""

import os
import sys

# Add Backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.logging.domain_logger import DomainLoggerService
from services.logging.log_config_manager import LogConfigManagerService
from services.logging.log_formatter import LogFormatterService
from services.logging.log_handlers import LogHandlerService
from services.logging.log_manager import LogManagerService
from services.loggingservice.logging_service import LogConfig, LogFormat, LoggingService, LogLevel


def test_facade_initialization():
    """Test 1: Verify facade initializes with all sub-services"""

    # Reset singleton
    LoggingService.reset_instance()

    service = LoggingService.get_instance()

    assert hasattr(service, "formatter_service"), "Missing formatter_service"
    assert hasattr(service, "handler_service"), "Missing handler_service"
    assert hasattr(service, "domain_logger"), "Missing domain_logger"
    assert hasattr(service, "log_manager"), "Missing log_manager"
    assert hasattr(service, "config_manager"), "Missing config_manager"


def test_sub_service_types():
    """Test 2: Verify sub-services are correct types"""

    service = LoggingService.get_instance()

    assert isinstance(
        service.formatter_service, LogFormatterService
    ), f"formatter_service is {type(service.formatter_service)}, expected LogFormatterService"
    assert isinstance(
        service.handler_service, LogHandlerService
    ), f"handler_service is {type(service.handler_service)}, expected LogHandlerService"
    assert isinstance(
        service.domain_logger, DomainLoggerService
    ), f"domain_logger is {type(service.domain_logger)}, expected DomainLoggerService"
    assert isinstance(
        service.log_manager, LogManagerService
    ), f"log_manager is {type(service.log_manager)}, expected LogManagerService"
    assert isinstance(
        service.config_manager, LogConfigManagerService
    ), f"config_manager is {type(service.config_manager)}, expected LogConfigManagerService"


def test_facade_methods():
    """Test 3: Verify facade exposes all required methods"""

    service = LoggingService.get_instance()

    required_methods = [
        # Configuration & Stats
        "update_config",
        "get_log_stats",
        "get_stats",
        # Domain logging
        "log_authentication_event",
        "log_user_action",
        "log_database_operation",
        "log_filter_operation",
        # Core logging
        "log",
        "log_with_context",
        "log_error",
        "log_exception",
        "log_performance",
        "log_structured",
        "log_batch",
        "log_masked",
        # Utilities
        "get_logger",
        "flush_logs",
        "clear_handlers",
        "with_correlation_id",
        "setup_async_logging",
    ]

    for method_name in required_methods:
        assert hasattr(service, method_name), f"Missing method: {method_name}"
        assert callable(getattr(service, method_name)), f"Not callable: {method_name}"


def test_formatter_service_standalone():
    """Test 4: Verify LogFormatterService works standalone"""

    formatter_service = LogFormatterService()

    # Test different format types
    simple_fmt = formatter_service.create_formatter(LogFormat.SIMPLE)
    assert simple_fmt is not None, "Failed to create SIMPLE formatter"

    detailed_fmt = formatter_service.create_formatter(LogFormat.DETAILED)
    assert detailed_fmt is not None, "Failed to create DETAILED formatter"

    json_fmt = formatter_service.create_formatter(LogFormat.JSON)
    assert json_fmt is not None, "Failed to create JSON formatter"

    structured_fmt = formatter_service.create_formatter(LogFormat.STRUCTURED)
    assert structured_fmt is not None, "Failed to create STRUCTURED formatter"


def test_handler_service_standalone():
    """Test 5: Verify LogHandlerService works standalone"""

    import logging

    handler_service = LogHandlerService()

    # Create test logger
    test_logger = logging.getLogger("test_handler")
    test_logger.handlers.clear()

    # Test console handler setup
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler_service.setup_console_handler(test_logger, logging.INFO, formatter)
    assert len(test_logger.handlers) > 0, "Console handler not added"

    # Test handler clearing
    handler_service.clear_handlers(test_logger)
    assert len(test_logger.handlers) == 0, "Handlers not cleared"


def test_domain_logger_standalone():
    """Test 6: Verify DomainLoggerService works standalone"""

    import logging

    # Create mock get_logger function
    test_loggers = {}

    def mock_get_logger(name):
        if name not in test_loggers:
            test_loggers[name] = logging.getLogger(f"test_{name}")
        return test_loggers[name]

    # Create config
    config = LogConfig()
    config.log_authentication_events = True
    config.log_user_actions = True
    config.log_database_queries = True
    config.log_filter_operations = True

    domain_logger = DomainLoggerService(mock_get_logger, config)

    # Test each domain logging method (should not raise exceptions)
    try:
        domain_logger.log_authentication_event("login", "user123", True)
        domain_logger.log_user_action("user123", "create", "document", True)
        domain_logger.log_database_operation("SELECT", "users", 15.5, True)
        domain_logger.log_filter_operation("profanity_filter", 100, 5, 25.0, "user123")
    except Exception:
        raise


def test_log_manager_standalone():
    """Test 7: Verify LogManagerService works standalone"""

    import logging

    # Create mock get_logger function
    test_loggers = {}

    def mock_get_logger(name):
        if name not in test_loggers:
            test_loggers[name] = logging.getLogger(f"test_{name}")
        return test_loggers[name]

    config = LogConfig()
    log_manager = LogManagerService(mock_get_logger, config)

    # Test core logging methods (should not raise exceptions)
    try:
        log_manager.log("Test message", LogLevel.INFO)
        log_manager.log_error("Test error")
        log_manager.log_performance("test_op", 100.0, True)
        log_manager.log_structured("Test", {"key": "value"})
        log_manager.log_batch(["msg1", "msg2"])

        stats = log_manager.get_stats()
        assert isinstance(stats, dict), "get_stats should return dict"
        assert "total_logs" in stats, "Stats should have total_logs"

    except Exception:
        raise


def test_config_manager_standalone():
    """Test 8: Verify LogConfigManagerService works standalone"""

    config = LogConfig()
    loggers = {}
    config_manager = LogConfigManagerService(config, loggers)

    # Test config management
    assert config_manager.get_config() == config, "get_config failed"

    new_config = LogConfig()
    new_config.level = LogLevel.DEBUG
    config_manager.update_config(new_config)
    assert config_manager.config.level == LogLevel.DEBUG, "update_config failed"

    # Test stats
    stats = config_manager.get_log_stats()
    assert isinstance(stats, dict), "get_log_stats should return dict"
    assert "config" in stats, "Stats should have config"


def test_service_sizes():
    """Test 9: Verify service sizes are reasonable"""

    import os

    backend_path = os.path.dirname(os.path.abspath(__file__))

    files_to_check = {
        "Facade": os.path.join(backend_path, "services/loggingservice/logging_service.py"),
        "LogFormatterService": os.path.join(backend_path, "services/logging/log_formatter.py"),
        "LogHandlerService": os.path.join(backend_path, "services/logging/log_handlers.py"),
        "DomainLoggerService": os.path.join(backend_path, "services/logging/domain_logger.py"),
        "LogManagerService": os.path.join(backend_path, "services/logging/log_manager.py"),
        "LogConfigManagerService": os.path.join(backend_path, "services/logging/log_config_manager.py"),
    }

    sizes = {}
    for name, path in files_to_check.items():
        with open(path) as f:
            line_count = len(f.readlines())
        sizes[name] = line_count

    # Check targets
    assert sizes["Facade"] < 350, f"Facade too large: {sizes['Facade']} lines (target: <350)"
    assert sizes["LogFormatterService"] < 150, f"LogFormatterService too large: {sizes['LogFormatterService']} lines"
    assert sizes["LogHandlerService"] < 150, f"LogHandlerService too large: {sizes['LogHandlerService']} lines"
    assert sizes["DomainLoggerService"] < 200, f"DomainLoggerService too large: {sizes['DomainLoggerService']} lines"
    assert sizes["LogManagerService"] < 250, f"LogManagerService too large: {sizes['LogManagerService']} lines"
    assert (
        sizes["LogConfigManagerService"] < 100
    ), f"LogConfigManagerService too large: {sizes['LogConfigManagerService']} lines"

    sum(sizes.values())


def test_focused_responsibilities():
    """Test 10: Verify services have focused responsibilities"""

    service = LoggingService.get_instance()

    # LogFormatterService: formatting only
    formatter_methods = [m for m in dir(service.formatter_service) if not m.startswith("_")]
    assert "create_formatter" in formatter_methods, "LogFormatterService missing create_formatter"

    # LogHandlerService: handler setup only
    handler_methods = [m for m in dir(service.handler_service) if not m.startswith("_")]
    assert "setup_console_handler" in handler_methods, "LogHandlerService missing setup_console_handler"
    assert "setup_file_handler" in handler_methods, "LogHandlerService missing setup_file_handler"

    # DomainLoggerService: domain logging only
    domain_methods = [m for m in dir(service.domain_logger) if not m.startswith("_")]
    assert "log_authentication_event" in domain_methods, "DomainLoggerService missing log_authentication_event"
    assert "log_user_action" in domain_methods, "DomainLoggerService missing log_user_action"

    # LogManagerService: core logging only
    manager_methods = [m for m in dir(service.log_manager) if not m.startswith("_")]
    assert "log" in manager_methods, "LogManagerService missing log"
    assert "log_error" in manager_methods, "LogManagerService missing log_error"

    # LogConfigManagerService: config and stats only
    config_methods = [m for m in dir(service.config_manager) if not m.startswith("_")]
    assert "get_config" in config_methods, "LogConfigManagerService missing get_config"
    assert "update_config" in config_methods, "LogConfigManagerService missing update_config"


def run_all_tests():
    """Run all architecture tests"""

    tests = [
        test_facade_initialization,
        test_sub_service_types,
        test_facade_methods,
        test_formatter_service_standalone,
        test_handler_service_standalone,
        test_domain_logger_standalone,
        test_log_manager_standalone,
        test_config_manager_standalone,
        test_service_sizes,
        test_focused_responsibilities,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception:
            failed += 1

    if failed == 0:
        pass
    else:
        pass

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
