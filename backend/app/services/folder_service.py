"""Folder management service."""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateNameError,
    FolderNotFoundAppError,
    ForbiddenError,
    ValidationError,
)
from app.core.security import validate_and_sanitize_filename
from app.models.file import File
from app.models.folder import Folder
from app.services.activity_service import log_activity
from app.services.storage_service import StorageService

logger = logging.getLogger("mycloud.folder")


class FolderService:
    """Service managing virtual and physical folder operations."""

    @staticmethod
    def _resolve_folder_disk_path(db: Session, user_id: int, folder: Folder) -> str:
        """Build the corresponding physical folder path under the user's folder root."""
        parts: list[str] = []
        current = folder
        while current is not None:
            parts.insert(0, current.name)
            current = db.query(Folder).filter(Folder.id == current.parent_id).first() if current.parent_id is not None else None
        return "/".join(parts)

    @staticmethod
    def sync_physical_folders_for_user(
        db: Session,
        storage_service: StorageService,
        user_id: int,
    ) -> None:
        """Reconcile the folder metadata with the real directories inside the user's folder root."""
        folders_root = storage_service.resolve_user_dir(user_id) / "folders"
        if not folders_root.exists():
            # If the entire folder root is gone, remove any stale folder metadata as well.
            tracked_folders = db.query(Folder).filter(Folder.owner_id == user_id).all()
            for folder in tracked_folders:
                FolderService.delete_folder(db, user_id, folder.id, storage_service)
            return

        tracked_ids = {folder.id for folder in db.query(Folder).filter(Folder.owner_id == user_id).all()}

        # Remove stale folders whose physical directory no longer exists.
        for folder in list(db.query(Folder).filter(Folder.owner_id == user_id).all()):
            disk_path = folders_root / FolderService._resolve_folder_disk_path(db, user_id, folder)
            if not disk_path.exists():
                FolderService.delete_folder(db, user_id, folder.id, storage_service)
                tracked_ids.discard(folder.id)

        for folder_dir in sorted(folders_root.rglob("*"), key=lambda p: str(p).lower()):
            if not folder_dir.is_dir():
                continue
            if folder_dir == folders_root:
                continue

            rel_path = folder_dir.relative_to(folders_root)
            path_parts = rel_path.parts
            if not path_parts:
                continue

            name = path_parts[-1]
            parent_id = None
            current_rel = path_parts[:-1]
            if current_rel:
                parent_name = current_rel[-1]
                parent = db.query(Folder).filter(
                    Folder.owner_id == user_id,
                    Folder.parent_id == parent_id,
                    Folder.name == parent_name,
                ).first()
                if parent:
                    parent_id = parent.id

            existing = db.query(Folder).filter(
                Folder.owner_id == user_id,
                Folder.parent_id == parent_id,
                Folder.name == name,
            ).first()

            if existing:
                continue

            folder = Folder(name=name, parent_id=parent_id, owner_id=user_id)
            db.add(folder)
            db.commit()
            db.refresh(folder)
            tracked_ids.add(folder.id)

    @staticmethod
    def create_folder(
        db: Session,
        storage_service: StorageService,
        user_id: int,
        name: str,
        parent_id: Optional[int] = None,
    ) -> Folder:
        """Create a new folder for the user after validating name and parent existence."""
        clean_name = validate_and_sanitize_filename(name)

        # Validate parent folder if specified
        if parent_id is not None:
            parent = db.query(Folder).filter(Folder.id == parent_id).first()
            if not parent:
                raise FolderNotFoundAppError("Specified parent folder does not exist.")
            if parent.owner_id != user_id:
                raise ForbiddenError("You do not own the parent folder.")

        # Check for duplicate folder name under the same parent
        existing = db.query(Folder).filter(
            Folder.owner_id == user_id,
            Folder.parent_id == parent_id,
            Folder.name == clean_name,
        ).first()

        if existing:
            raise DuplicateNameError(f"A folder named '{clean_name}' already exists in this location.")

        # Create folder in database
        folder = Folder(
            name=clean_name,
            parent_id=parent_id,
            owner_id=user_id,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)

        # Ensure user folder directory structure exists on disk
        user_root = storage_service.resolve_user_dir(user_id)
        folder_dir = user_root / "folders"
        folder_dir.mkdir(parents=True, exist_ok=True)

        if parent_id is None:
            target_dir = folder_dir / clean_name
        else:
            parent_folder = FolderService.get_folder(db, user_id, parent_id)
            parent_path = user_root / "folders" / FolderService._resolve_folder_disk_path(db, user_id, parent_folder)
            target_dir = parent_path / clean_name
        target_dir.mkdir(parents=True, exist_ok=True)

        log_activity(
            db,
            action="CREATE_FOLDER",
            user_id=user_id,
            resource_type="folder",
            resource_id=str(folder.id),
            metadata={"folder_name": clean_name, "parent_id": parent_id},
        )
        return folder

    @staticmethod
    def get_folder(db: Session, user_id: int, folder_id: int) -> Folder:
        """Retrieve a folder by ID, verifying ownership."""
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise FolderNotFoundAppError("Folder not found.")
        if folder.owner_id != user_id:
            raise ForbiddenError("Access denied to requested folder.")
        return folder

    @staticmethod
    def list_folder_contents(
        db: Session,
        user_id: int,
        folder_id: Optional[int] = None,
    ) -> tuple[Optional[Folder], list[Folder], list[File]]:
        """List subfolders and non-deleted files inside the target folder (or root)."""
        current_folder = None
        if folder_id is not None:
            current_folder = FolderService.get_folder(db, user_id, folder_id)

        subfolders = (
            db.query(Folder)
            .filter(Folder.owner_id == user_id, Folder.parent_id == folder_id)
            .order_by(Folder.name.asc())
            .all()
        )

        files = (
            db.query(File)
            .filter(
                File.owner_id == user_id,
                File.folder_id == folder_id,
                File.deleted_at.is_(None),
            )
            .order_by(File.name.asc())
            .all()
        )

        return current_folder, subfolders, files

    @staticmethod
    def rename_folder(
        db: Session,
        user_id: int,
        folder_id: int,
        new_name: str,
        storage_service: Optional[StorageService] = None,
    ) -> Folder:
        """Rename an existing folder after validating name uniqueness."""
        folder = FolderService.get_folder(db, user_id, folder_id)
        clean_name = validate_and_sanitize_filename(new_name)

        if folder.name == clean_name:
            return folder

        # Check duplicate
        duplicate = db.query(Folder).filter(
            Folder.owner_id == user_id,
            Folder.parent_id == folder.parent_id,
            Folder.name == clean_name,
            Folder.id != folder_id,
        ).first()

        if duplicate:
            raise DuplicateNameError(f"A folder named '{clean_name}' already exists in this location.")

        old_name = folder.name
        if storage_service is not None:
            user_root = storage_service.resolve_user_dir(user_id)
            folders_root = user_root / "folders"
            old_path = folders_root / FolderService._resolve_folder_disk_path(db, user_id, folder)
            if old_path.exists():
                new_path = old_path.parent / clean_name
                old_path.rename(new_path)

        folder.name = clean_name
        folder.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(folder)

        log_activity(
            db,
            action="RENAME",
            user_id=user_id,
            resource_type="folder",
            resource_id=str(folder.id),
            metadata={"old_name": old_name, "new_name": clean_name},
        )
        return folder

    @staticmethod
    def delete_folder(
        db: Session,
        user_id: int,
        folder_id: int,
        storage_service: Optional[StorageService] = None,
    ) -> None:
        """Delete a folder, soft-delete nested files in the database, and remove physical files and directories from storage."""
        folder = FolderService.get_folder(db, user_id, folder_id)

        if storage_service is not None:
            folders_root = storage_service.resolve_user_dir(user_id) / "folders"
            disk_path = folders_root / FolderService._resolve_folder_disk_path(db, user_id, folder)
            if disk_path.exists():
                for child in sorted(disk_path.rglob("*"), reverse=True):
                    if child.is_file() or child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        child.rmdir()
                if disk_path.exists():
                    disk_path.rmdir()

        # Soft delete all nested files in this folder and subfolders
        now = datetime.now(timezone.utc)

        def _soft_delete_folder_files(f_id: int):
            files = db.query(File).filter(File.folder_id == f_id, File.deleted_at.is_(None)).all()
            for file in files:
                if storage_service is not None:
                    physical_path = FileService.resolve_physical_path_for_file(db, storage_service, user_id, file)
                    if storage_service.file_exists(physical_path):
                        storage_service.delete_file(physical_path)
                file.deleted_at = now
            children = db.query(Folder).filter(Folder.parent_id == f_id).all()
            for child in children:
                _soft_delete_folder_files(child.id)

        _soft_delete_folder_files(folder.id)

        # Remove folder record
        db.delete(folder)
        db.commit()

        log_activity(
            db,
            action="DELETE",
            user_id=user_id,
            resource_type="folder",
            resource_id=str(folder_id),
            metadata={"deleted_folder_name": folder.name},
        )
