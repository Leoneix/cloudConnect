"""File management service coordinating Database, StorageService, and validation."""

import hashlib
import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateNameError,
    FileNotFoundAppError,
    FolderNotFoundAppError,
    ForbiddenError,
    StorageInconsistencyError,
)
from app.core.security import validate_and_sanitize_filename
from app.models.file import File
from app.models.folder import Folder
from app.services.activity_service import log_activity
from app.services.storage_service import StorageService

logger = logging.getLogger("mycloud.file")


class FileService:
    """Business logic for file metadata, uploads, downloads, renames, and deletions."""

    @staticmethod
    def resolve_physical_path_for_file(
        db: Session,
        storage_service: StorageService,
        user_id: int,
        file_record: File,
    ) -> Path:
        """Resolve the real disk path for a user file, including files in nested folders."""
        user_dir = storage_service.resolve_user_dir(user_id)
        if file_record.folder_id is None:
            return storage_service.resolve_user_file_path(user_id, file_record.storage_name)

        folder = db.query(Folder).filter(
            Folder.id == file_record.folder_id,
            Folder.owner_id == user_id,
        ).first()
        if folder is None:
            raise FolderNotFoundAppError("Target folder does not exist.")

        parts: list[str] = []
        current = folder
        while current is not None:
            parts.insert(0, current.name)
            if current.parent_id is None:
                break
            current = db.query(Folder).filter(
                Folder.id == current.parent_id,
                Folder.owner_id == user_id,
            ).first()

        folder_path = user_dir / "folders" / Path(*parts)
        return storage_service.validate_path(folder_path / file_record.storage_name)

    @staticmethod
    def _resolve_folder_id_for_directory(
        db: Session,
        user_id: int,
        folders_root: Path,
        folder_dir: Path,
    ) -> Optional[int]:
        """Look up the database folder id matching the given physical folder directory."""
        try:
            rel_path = folder_dir.relative_to(folders_root)
        except ValueError:
            return None

        current_parent_id: Optional[int] = None
        for segment in rel_path.parts:
            folder = db.query(Folder).filter(
                Folder.owner_id == user_id,
                Folder.parent_id == current_parent_id,
                Folder.name == segment,
            ).first()
            if folder is None:
                return None
            current_parent_id = folder.id
        return current_parent_id

    @staticmethod
    def sync_physical_files_for_user(
        db: Session,
        storage_service: StorageService,
        user_id: int,
    ) -> None:
        """Reconcile the database inventory with the user's actual files on disk."""
        user_dir = storage_service.resolve_user_dir(user_id)
        folders_root = user_dir / "folders"
        user_files_dir = user_dir / "files"

        tracked_rows = db.query(File).filter(File.owner_id == user_id).all()
        tracked_storage_names = {row.storage_name for row in tracked_rows}
        now = datetime.now(timezone.utc)

        for row in tracked_rows:
            if row.deleted_at is not None:
                continue
            physical_path = FileService.resolve_physical_path_for_file(db, storage_service, user_id, row)
            if not storage_service.file_exists(physical_path):
                row.deleted_at = now

        scan_roots: list[tuple[Path, Optional[int]]] = [(user_files_dir, None)]
        if folders_root.exists():
            for folder_dir in sorted(folders_root.rglob("*"), key=lambda p: str(p).lower()):
                if not folder_dir.is_dir():
                    continue
                folder_id = FileService._resolve_folder_id_for_directory(db, user_id, folders_root, folder_dir)
                scan_roots.append((folder_dir, folder_id))

        for directory, parent_folder_id in scan_roots:
            if not directory.exists():
                continue
            for physical_file in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
                if not physical_file.is_file():
                    continue
                if physical_file.name in tracked_storage_names:
                    continue

                size = physical_file.stat().st_size
                extension = Path(physical_file.name).suffix.lower() or None
                mime, _ = mimetypes.guess_type(physical_file.name)
                checksum = hashlib.sha256()
                with open(physical_file, "rb") as fh:
                    for chunk in iter(lambda: fh.read(64 * 1024), b""):
                        checksum.update(chunk)

                db_file = File(
                    name=physical_file.name,
                    storage_name=physical_file.name,
                    folder_id=parent_folder_id,
                    owner_id=user_id,
                    size=size,
                    mime_type=mime or "application/octet-stream",
                    extension=extension,
                    checksum=checksum.hexdigest(),
                )
                db.add(db_file)
                tracked_storage_names.add(physical_file.name)

        db.commit()

    @staticmethod
    def list_files(
        db: Session,
        user_id: int,
        folder_id: Optional[int] = None,
        storage_service: Optional[StorageService] = None,
    ) -> list[File]:
        """List all active files for a user, reconciling them with the physical storage directory."""
        if storage_service is not None:
            FileService.sync_physical_files_for_user(db, storage_service, user_id)

        query = db.query(File).filter(
            File.owner_id == user_id,
            File.folder_id == folder_id,
            File.deleted_at.is_(None),
        ).order_by(File.name.asc())
        return query.all()

    @staticmethod
    def get_file(db: Session, user_id: int, file_id: int) -> File:
        """Get file by ID and verify ownership and non-deleted status."""
        file = db.query(File).filter(File.id == file_id).first()
        if not file or file.is_deleted:
            raise FileNotFoundAppError("The requested file was not found.")
        if file.owner_id != user_id:
            raise ForbiddenError("Access denied to requested file.")
        return file

    @staticmethod
    def upload_file(
        db: Session,
        storage_service: StorageService,
        user_id: int,
        filename: str,
        stream: BinaryIO,
        content_type: Optional[str] = None,
        folder_id: Optional[int] = None,
    ) -> File:
        """Upload a file using two-phase temporary write and atomic move."""
        clean_name = validate_and_sanitize_filename(filename)

        if folder_id is not None:
            folder = db.query(Folder).filter(Folder.id == folder_id).first()
            if not folder:
                raise FolderNotFoundAppError("Target folder does not exist.")
            if folder.owner_id != user_id:
                raise ForbiddenError("You do not own the destination folder.")

        duplicate = db.query(File).filter(
            File.owner_id == user_id,
            File.folder_id == folder_id,
            File.name == clean_name,
            File.deleted_at.is_(None),
        ).first()
        if duplicate:
            raise DuplicateNameError(f"A file named '{clean_name}' already exists in this folder.")

        temp_path, total_size, checksum = storage_service.write_stream_to_temp(stream)
        ext = Path(clean_name).suffix.lower()
        mime = content_type
        if not mime or mime == "application/octet-stream":
            guessed_mime, _ = mimetypes.guess_type(clean_name)
            mime = guessed_mime or "application/octet-stream"

        storage_filename = f"{uuid.uuid4().hex}{ext}"
        if folder_id is None:
            final_dir = storage_service.resolve_user_dir(user_id) / "files"
        else:
            folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == user_id).first()
            if not folder:
                raise FolderNotFoundAppError("Target folder does not exist.")
            relative_parts: list[str] = []
            current = folder
            while current is not None:
                relative_parts.insert(0, current.name)
                if current.parent_id is None:
                    break
                current = db.query(Folder).filter(
                    Folder.id == current.parent_id,
                    Folder.owner_id == user_id,
                ).first()
            final_dir = storage_service.resolve_user_dir(user_id) / "folders" / Path(*relative_parts)
        final_dir.mkdir(parents=True, exist_ok=True)
        final_path = storage_service.validate_path(final_dir / storage_filename)

        try:
            storage_service.move_file(temp_path, final_path)
            db_file = File(
                name=clean_name,
                storage_name=storage_filename,
                folder_id=folder_id,
                owner_id=user_id,
                size=total_size,
                mime_type=mime,
                extension=ext if ext else None,
                checksum=checksum,
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)

            log_activity(
                db,
                action="UPLOAD",
                user_id=user_id,
                resource_type="file",
                resource_id=str(db_file.id),
                metadata={"filename": clean_name, "size": total_size, "folder_id": folder_id},
            )
            return db_file
        except Exception as exc:
            db.rollback()
            if storage_service.file_exists(final_path):
                try:
                    storage_service.delete_file(final_path)
                except Exception:
                    pass
            logger.error("Failed to complete file upload for user %s: %s", user_id, exc)
            raise

    @staticmethod
    def get_file_download_stream(
        db: Session,
        storage_service: StorageService,
        user_id: int,
        file_id: int,
    ) -> tuple[File, any]:
        """Verify file existence and return metadata with chunked generator."""
        file = FileService.get_file(db, user_id, file_id)
        physical_path = FileService.resolve_physical_path_for_file(db, storage_service, user_id, file)

        if not storage_service.file_exists(physical_path):
            logger.warning(
                "Storage inconsistency: file ID %s metadata exists but physical file %s is missing.",
                file.id,
                physical_path,
            )
            raise StorageInconsistencyError("File storage inconsistency: physical file is missing.")

        stream_gen = storage_service.open_file_stream(physical_path)

        log_activity(
            db,
            action="DOWNLOAD",
            user_id=user_id,
            resource_type="file",
            resource_id=str(file.id),
            metadata={"filename": file.name, "size": file.size},
        )

        return file, stream_gen

    @staticmethod
    def rename_file(db: Session, user_id: int, file_id: int, new_name: str) -> File:
        """Rename an existing file after validating name syntax and folder uniqueness."""
        file = FileService.get_file(db, user_id, file_id)
        clean_name = validate_and_sanitize_filename(new_name)

        if file.name == clean_name:
            return file

        duplicate = db.query(File).filter(
            File.owner_id == user_id,
            File.folder_id == file.folder_id,
            File.name == clean_name,
            File.id != file_id,
            File.deleted_at.is_(None),
        ).first()
        if duplicate:
            raise DuplicateNameError(f"A file named '{clean_name}' already exists in this folder.")

        old_name = file.name
        file.name = clean_name
        file.extension = Path(clean_name).suffix.lower() or None
        file.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(file)

        log_activity(
            db,
            action="RENAME",
            user_id=user_id,
            resource_type="file",
            resource_id=str(file.id),
            metadata={"old_name": old_name, "new_name": clean_name},
        )

        return file

    @staticmethod
    def delete_file(
        db: Session,
        user_id: int,
        file_id: int,
        storage_service: Optional[StorageService] = None,
    ) -> File:
        """Soft-delete a file and remove the physical file from the configured storage path."""
        file = FileService.get_file(db, user_id, file_id)

        if storage_service is not None:
            physical_path = FileService.resolve_physical_path_for_file(db, storage_service, user_id, file)
            if storage_service.file_exists(physical_path):
                storage_service.delete_file(physical_path)

        file.deleted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(file)

        log_activity(
            db,
            action="DELETE",
            user_id=user_id,
            resource_type="file",
            resource_id=str(file.id),
            metadata={"filename": file.name},
        )

        return file
