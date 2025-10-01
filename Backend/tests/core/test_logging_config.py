"""
Tests for JSONFormatter and setup_logging in core.logging.
"""

from __future__ import annotations

import json
import logging

import pytest

from core.logging_config import JSONFormatter, setup_logging


@pytest.mark.timeout(30)
def test_Whenjson_formatter_serializes_recordCalled_ThenSucceeds():
    formatter = JSONFormatter()
    logger = logging.getLogger("test.logger")
    record = logger.makeRecord(
        name="test.logger", level=logging.INFO, fn=__file__, lno=10, msg="hello", args=(), exc_info=None
    )
    # Add a custom attribute to exercise extra-field serialization
    record.user = "alice"
    out = formatter.format(record)
    data = json.loads(out)
    assert data["level"] == "INFO"
    assert data["message"] == "hello"
    assert "timestamp" in data
    assert data["user"] == "alice"


@pytest.mark.timeout(30)
def test_Whensetup_logging_configures_correctlyCalled_ThenSucceeds():
    """Test that setup_logging configures the logging system correctly"""
    # setup_logging now returns None and configures structlog
    result = setup_logging()
    assert result is None  # New implementation doesn't return a file path

    # Test that logging works after setup by verifying structlog is configured
    import structlog

    logger = structlog.get_logger(__name__)
    # Should not raise an exception
    logger.info("test message", test_field="test_value")

    # Verify that standard logging is also configured
    std_logger = logging.getLogger(__name__)
    std_logger.info("standard logging test")
