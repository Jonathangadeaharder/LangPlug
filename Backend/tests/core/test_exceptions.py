"""
Tiny tests to exercise custom exception classes and their status codes.
"""

from __future__ import annotations

import pytest
from fastapi import status

from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    LangPlugException,
    NotFoundError,
    ProcessingError,
    ServiceUnavailableError,
    ValidationError,
)


@pytest.mark.timeout(30)
def test_Whenexception_status_codesCalled_ThenSucceeds():
    assert AuthenticationError().status_code == status.HTTP_401_UNAUTHORIZED
    assert AuthorizationError().status_code == status.HTTP_403_FORBIDDEN
    assert ValidationError().status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert NotFoundError("X").status_code == status.HTTP_404_NOT_FOUND
    assert ServiceUnavailableError().status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert ProcessingError().status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert ConfigurationError().status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Base class behavior
    e = LangPlugException("msg", 418)
    assert e.message == "msg" and e.status_code == 418
