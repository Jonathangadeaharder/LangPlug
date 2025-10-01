"""Sentry configuration for error tracking"""

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from core.config import settings


def configure_sentry():
    """Configure Sentry for error tracking"""
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=None,  # Capture records from all levels
                event_level=None,  # Send no events from logging
            ),
            AsyncioIntegration(),
        ],
        traces_sample_rate=0.1,  # Capture 10% of transactions for performance monitoring
        environment=settings.environment,
        release=getattr(settings, "version", None),
        before_send=filter_sensitive_data,
    )


def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"

    # Remove sensitive form data
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]
        if isinstance(data, dict):
            sensitive_fields = ["password", "token", "secret", "key"]
            for field in sensitive_fields:
                if field in data:
                    data[field] = "[Filtered]"

    return event


def set_user_context(user_id: str, email: str | None = None):
    """Set user context for Sentry"""
    sentry_sdk.set_user({"id": user_id, "email": email})


def set_tag(key: str, value: str):
    """Set a tag for Sentry"""
    sentry_sdk.set_tag(key, value)


def set_context(key: str, context: dict):
    """Set context for Sentry"""
    sentry_sdk.set_context(key, context)


def capture_exception(error: Exception, **kwargs):
    """Capture an exception with Sentry"""
    return sentry_sdk.capture_exception(error, **kwargs)


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message with Sentry"""
    return sentry_sdk.capture_message(message, level=level, **kwargs)
