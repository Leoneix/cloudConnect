"""System and storage information schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health check response."""

    status: str = "ok"


class StorageResponse(BaseModel):
    """Storage statistics computed from the configured storage disk."""

    total_bytes: int = Field(..., description="Total storage capacity in bytes")
    used_bytes: int = Field(..., description="Used storage capacity in bytes")
    free_bytes: int = Field(..., description="Free storage capacity in bytes")
    usage_percent: float = Field(..., description="Storage usage percentage (0-100)")
