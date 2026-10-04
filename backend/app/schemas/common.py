"""Common schemas across the application."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error information."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Optional extra error details")


class ErrorResponse(BaseModel):
    """Standardized API error response."""
    error: ErrorDetail


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str
