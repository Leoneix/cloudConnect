"""Folder management API router."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, get_storage_service
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.file import FileResponse
from app.schemas.folder import (
    FolderContentsResponse,
    FolderCreateRequest,
    FolderResponse,
    FolderUpdateRequest,
)
from app.services.folder_service import FolderService
from app.services.storage_service import StorageService

logger = logging.getLogger("mycloud.api.folders")
router = APIRouter(prefix="/folders", tags=["Folders"])


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Folder",
    description="Create a new folder in the root or inside an existing parent folder.",
)
def create_folder(
    payload: FolderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> FolderResponse:
    folder = FolderService.create_folder(
        db=db,
        storage_service=storage_service,
        user_id=current_user.id,
        name=payload.name,
        parent_id=payload.parent_id,
    )
    return FolderResponse.model_validate(folder)


@router.get(
    "",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Root Folder Contents",
    description="Retrieve root directory subfolders and files.",
)
def get_root_folder_contents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FolderContentsResponse:
    current_folder, subfolders, files = FolderService.list_folder_contents(
        db=db,
        user_id=current_user.id,
        folder_id=None,
    )
    return FolderContentsResponse(
        folder=None,
        subfolders=[FolderResponse.model_validate(f) for f in subfolders],
        files=[FileResponse.model_validate(f) for f in files],
    )


@router.get(
    "/{folder_id}",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Folder Contents",
    description="Retrieve details of a folder along with its child subfolders and files.",
)
def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FolderContentsResponse:
    current_folder, subfolders, files = FolderService.list_folder_contents(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
    )
    return FolderContentsResponse(
        folder=FolderResponse.model_validate(current_folder) if current_folder else None,
        subfolders=[FolderResponse.model_validate(f) for f in subfolders],
        files=[FileResponse.model_validate(f) for f in files],
    )


@router.patch(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Rename Folder",
    description="Rename an existing folder.",
)
def rename_folder(
    folder_id: int,
    payload: FolderUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> FolderResponse:
    folder = FolderService.rename_folder(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
        new_name=payload.name,
        storage_service=storage_service,
    )
    return FolderResponse.model_validate(folder)


@router.delete(
    "/{folder_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Folder",
    description="Delete a folder and cascade deletion to all contained files and subfolders.",
)
def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> MessageResponse:
    FolderService.delete_folder(
        db=db,
        user_id=current_user.id,
        folder_id=folder_id,
        storage_service=storage_service,
    )
    return MessageResponse(message="Folder and its contents deleted successfully.")
