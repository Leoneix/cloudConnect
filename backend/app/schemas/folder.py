"""Folder Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.file import FileResponse


class FolderCreateRequest(BaseModel):
    """Folder creation payload."""

    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    parent_id: Optional[int] = Field(None, description="Parent folder ID or null for root directory")


class FolderUpdateRequest(BaseModel):
    """Folder update/rename payload."""

    name: str = Field(..., min_length=1, max_length=255, description="New folder name")


class FolderResponse(BaseModel):
    """Folder representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime


class FolderContentsResponse(BaseModel):
    """Folder details along with child subfolders and files."""

    folder: Optional[FolderResponse] = None
    subfolders: list[FolderResponse] = Field(default_factory=list)
    files: list[FileResponse] = Field(default_factory=list)
