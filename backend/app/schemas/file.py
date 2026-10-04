"""File Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FileResponse(BaseModel):
    """File metadata returned to clients without internal storage paths or storage names."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    size: int
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    checksum: Optional[str] = None
    folder_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class FileUpdateRequest(BaseModel):
    """File update/rename payload."""

    name: str = Field(..., min_length=1, max_length=255, description="New filename")


class FileListResponse(BaseModel):
    """List of files with total count."""

    files: list[FileResponse]
    total: int
