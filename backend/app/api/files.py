"""File management API router."""

import logging
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, File as FastApiFile, Form, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, get_storage_service
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.file import FileListResponse, FileResponse, FileUpdateRequest
from app.services.file_service import FileService
from app.services.storage_service import StorageService

logger = logging.getLogger("mycloud.api.files")
router = APIRouter(prefix="/files", tags=["Files"])


@router.get(
    "",
    response_model=FileListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Files",
    description="List active files in a specific folder or the root directory.",
)
def list_files(
    folder_id: Optional[int] = Query(None, description="Folder ID or null for root directory"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> FileListResponse:
    files = FileService.list_files(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
        storage_service=storage_service,
    )
    file_responses = [FileResponse.model_validate(f) for f in files]
    return FileListResponse(files=file_responses, total=len(file_responses))


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload File",
    description="Upload a new file using multipart form-data. Streamed safely through a temporary file before atomic persistence.",
)
def upload_file(
    file: UploadFile = FastApiFile(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    uploaded = FileService.upload_file(
        db=db,
        storage_service=storage_service,
        user_id=current_user.id,
        filename=file.filename or "unnamed_file",
        stream=file.file,
        content_type=file.content_type,
        folder_id=folder_id,
    )
    return FileResponse.model_validate(uploaded)


@router.get(
    "/{file_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download File",
    description="Stream a file download without reading the entire file into server memory.",
)
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
):
    file_record, stream_gen = FileService.get_file_download_stream(
        db=db,
        storage_service=storage_service,
        user_id=current_user.id,
        file_id=file_id,
    )

    # Encode filename for Content-Disposition header in RFC 5987 format
    encoded_filename = quote(file_record.name)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{file_record.name}\"; filename*=UTF-8''{encoded_filename}",
        "Content-Length": str(file_record.size),
    }

    return StreamingResponse(
        content=stream_gen,
        media_type=file_record.mime_type or "application/octet-stream",
        headers=headers,
    )


@router.patch(
    "/{file_id}",
    response_model=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename File",
    description="Rename an existing file.",
)
def rename_file(
    file_id: int,
    payload: FileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    file = FileService.rename_file(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        new_name=payload.name,
    )
    return FileResponse.model_validate(file)


@router.delete(
    "/{file_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete File",
    description="Soft-delete a file so that it no longer appears in listings.",
)
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> MessageResponse:
    FileService.delete_file(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        storage_service=storage_service,
    )
    return MessageResponse(message="File deleted successfully.")
