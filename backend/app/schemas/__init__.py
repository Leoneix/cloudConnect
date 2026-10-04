"""Pydantic schemas package."""

from app.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest
from app.schemas.common import ErrorDetail, ErrorResponse, MessageResponse
from app.schemas.file import FileListResponse, FileResponse, FileUpdateRequest
from app.schemas.folder import FolderContentsResponse, FolderCreateRequest, FolderResponse, FolderUpdateRequest
from app.schemas.system import HealthResponse, StorageResponse
from app.schemas.user import UserResponse

__all__ = [
    "AuthResponse",
    "ChangePasswordRequest",
    "ErrorDetail",
    "ErrorResponse",
    "FileListResponse",
    "FileResponse",
    "FileUpdateRequest",
    "FolderContentsResponse",
    "FolderCreateRequest",
    "FolderResponse",
    "FolderUpdateRequest",
    "HealthResponse",
    "LoginRequest",
    "MessageResponse",
    "StorageResponse",
    "UserResponse",
]
