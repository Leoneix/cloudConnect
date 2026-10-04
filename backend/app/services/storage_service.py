"""Storage Service: Centralized and strictly validated filesystem interface for MyCloud."""

import hashlib
import logging
import os
import shutil
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO, Optional, Union

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    FileTooLargeError,
    InsufficientStorageError,
    PathTraversalError,
    ResourceNotFoundError,
)

logger = logging.getLogger("mycloud.storage")


class StorageService:
    """The ONLY service authorized to perform direct filesystem operations against STORAGE_PATH."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._storage_root = self.settings.resolved_storage_path
        self._ensure_base_directories()

    def _ensure_base_directories(self) -> None:
        """Ensure storage root, users directory, and tmp upload directory exist."""
        try:
            self._storage_root.mkdir(parents=True, exist_ok=True)
            (self._storage_root / "users").mkdir(parents=True, exist_ok=True)
            (self._storage_root / "tmp").mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Failed to initialize storage directories at %s: %s", self._storage_root, exc)
            raise

    def get_storage_root(self) -> Path:
        """Get the fully resolved storage root path."""
        return self._storage_root

    def validate_path(self, target_path: Union[str, Path]) -> Path:
        """Validate that a target path strictly stays within the configured storage root.

        Raises PathTraversalError if target_path attempts to escape storage_root or represents root/parent navigation.
        """
        if not target_path:
            raise PathTraversalError("Path cannot be empty.")

        path_str = str(target_path).strip()
        if not path_str:
            raise PathTraversalError("Path cannot be blank.")

        if "\x00" in path_str:
            raise PathTraversalError("Null byte detected in path.")

        # Disallow bare current or parent directory references
        if path_str in {".", ".."}:
            raise PathTraversalError("Direct navigation to current or parent directory is not allowed.")

        # Disallow UNC and drive escape patterns in string check
        if path_str.startswith("//") or path_str.startswith("\\\\"):
            raise PathTraversalError("UNC paths are not permitted.")

        try:
            # If target_path is relative, resolve it relative to storage_root
            candidate = Path(target_path)
            if not candidate.is_absolute():
                resolved = (self._storage_root / candidate).resolve()
            else:
                resolved = candidate.resolve()
        except Exception as exc:
            raise PathTraversalError(f"Invalid path structure: {exc}") from exc

        # Strict containment check
        try:
            resolved.relative_to(self._storage_root)
        except ValueError as exc:
            logger.warning("Path traversal attempt detected: '%s' escapes root '%s'", target_path, self._storage_root)
            raise PathTraversalError("Path escapes the configured storage root.") from exc

        return resolved

    def resolve_user_dir(self, user_id: int) -> Path:
        """Resolve and ensure the directory for a specific user."""
        user_dir = self.validate_path(self._storage_root / "users" / str(user_id))
        user_files_dir = user_dir / "files"
        user_folders_dir = user_dir / "folders"
        user_files_dir.mkdir(parents=True, exist_ok=True)
        user_folders_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def resolve_user_file_path(self, user_id: int, storage_name: str) -> Path:
        """Safely resolve the physical path for a user's stored file."""
        if not storage_name or ".." in storage_name or "/" in storage_name or "\\" in storage_name:
            raise PathTraversalError("Invalid storage filename.")
        
        user_files_dir = self.resolve_user_dir(user_id) / "files"
        file_path = self.validate_path(user_files_dir / storage_name)
        return file_path

    def create_directory(self, path: Union[str, Path]) -> Path:
        """Safely create a directory inside the storage root."""
        valid_path = self.validate_path(path)
        valid_path.mkdir(parents=True, exist_ok=True)
        return valid_path

    def write_stream_to_temp(
        self,
        stream: BinaryIO,
        max_bytes: Optional[int] = None,
        chunk_size: int = 64 * 1024,
    ) -> tuple[Path, int, str]:
        """Write an incoming binary stream to a temporary file in chunked fashion.

        Simultaneously computes SHA-256 checksum and enforces max upload size.
        Returns: (temp_file_path, total_bytes_written, sha256_checksum)
        """
        if max_bytes is None:
            max_bytes = self.settings.max_upload_size_bytes

        temp_id = f"{uuid.uuid4().hex}.tmp"
        temp_path = self.validate_path(self._storage_root / "tmp" / temp_id)

        sha256 = hashlib.sha256()
        bytes_written = 0

        try:
            with open(temp_path, "wb") as f_out:
                while True:
                    chunk = stream.read(chunk_size)
                    if not chunk:
                        break
                    
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        raise FileTooLargeError(
                            f"Uploaded file exceeds maximum limit of {self.settings.MAX_UPLOAD_SIZE_MB} MB."
                        )
                    
                    sha256.update(chunk)
                    f_out.write(chunk)

            return temp_path, bytes_written, sha256.hexdigest()

        except Exception:
            # Clean up temporary file immediately on failure or error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def move_file(self, src_path: Path, dst_path: Path) -> None:
        """Safely move/rename a file within the storage root."""
        valid_src = self.validate_path(src_path)
        valid_dst = self.validate_path(dst_path)

        if not valid_src.exists():
            raise ResourceNotFoundError("Source file does not exist.")

        # Ensure destination parent directory exists
        valid_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(valid_src), str(valid_dst))

    def delete_file(self, path: Path) -> None:
        """Safely delete a physical file from the storage root."""
        valid_path = self.validate_path(path)
        if valid_path.exists() and valid_path.is_file():
            try:
                valid_path.unlink()
            except OSError as exc:
                logger.error("Failed to delete physical file %s: %s", valid_path, exc)
                raise

    def file_exists(self, path: Path) -> bool:
        """Check if a validated physical file exists on disk."""
        try:
            valid_path = self.validate_path(path)
            return valid_path.is_file()
        except PathTraversalError:
            return False

    def open_file_stream(self, path: Path, chunk_size: int = 64 * 1024) -> Generator[bytes, None, None]:
        """Stream a file chunk-by-chunk to prevent loading large files into memory."""
        valid_path = self.validate_path(path)
        if not valid_path.exists() or not valid_path.is_file():
            raise ResourceNotFoundError("Physical file not found on disk.")

        with open(valid_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def get_storage_usage(self) -> dict[str, Union[int, float]]:
        """Calculate disk usage stats for the configured storage directory."""
        try:
            usage = shutil.disk_usage(str(self._storage_root))
            total = usage.total
            used = usage.used
            free = usage.free
            usage_percent = round((used / total) * 100, 2) if total > 0 else 0.0

            return {
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "usage_percent": usage_percent,
            }
        except OSError as exc:
            logger.error("Error retrieving disk usage for %s: %s", self._storage_root, exc)
            raise InsufficientStorageError("Unable to retrieve storage drive metrics.") from exc
