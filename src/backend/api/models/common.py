"""
Common API models shared across the application
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Standard error detail structure"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Any | None = Field(None, description="Additional context about the error")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "The requested resource could not be found",
                "details": {"id": "123"},
                "timestamp": "2024-01-01T12:00:00.000000",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard API error response wrapper"""

    error: ErrorDetail = Field(..., description="Error details")
