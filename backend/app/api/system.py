"""System monitoring and storage information API router."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, get_storage_service
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.system import HealthResponse, StorageResponse
from app.services.file_service import FileService
from app.services.storage_service import StorageService

logger = logging.getLogger("mycloud.api.system")

# Router for versioned system endpoints
system_router = APIRouter(prefix="/system", tags=["System"])


@system_router.get(
    "/storage",
    response_model=StorageResponse,
    status_code=status.HTTP_200_OK,
    summary="Storage Usage",
    description="Retrieve storage disk capacity and usage metrics from the configured storage drive.",
)
def get_storage_stats(
    current_user: User = Depends(get_current_active_user),
    storage_service: StorageService = Depends(get_storage_service),
) -> StorageResponse:
    stats = storage_service.get_storage_usage()
    return StorageResponse(**stats)


@system_router.post(
    "/rescan",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Rescan Storage",
    description="Reconcile the portal with the user's actual filesystem by importing missing files and hiding entries whose physical files were deleted.",
)
def rescan_storage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> MessageResponse:
    FileService.sync_physical_files_for_user(db, storage_service, current_user.id)
    from app.services.folder_service import FolderService

    FolderService.sync_physical_folders_for_user(db, storage_service, current_user.id)
    return MessageResponse(message="Storage rescan completed successfully.")
