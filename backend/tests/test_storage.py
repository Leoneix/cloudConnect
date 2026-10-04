"""Storage service isolated unit tests."""

import io
import pytest
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import (
    FileTooLargeError,
    PathTraversalError,
    ResourceNotFoundError,
)
from app.services.storage_service import StorageService


def test_storage_root_resolution(test_storage_service: StorageService, temp_environment: Settings):
    root = test_storage_service.get_storage_root()
    assert root.is_dir()
    assert root == Path(temp_environment.STORAGE_PATH).resolve()


def test_create_directory(test_storage_service: StorageService):
    new_dir = test_storage_service.create_directory("custom_subfolder")
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_write_and_stream_file(test_storage_service: StorageService):
    content = b"MyCloud Storage Service Test Payload \x00\x01\x02"
    stream = io.BytesIO(content)

    temp_path, size, checksum = test_storage_service.write_stream_to_temp(stream)
    assert temp_path.exists()
    assert size == len(content)
    assert len(checksum) == 64  # SHA-256 hex string

    # Move to permanent location
    user_file_path = test_storage_service.resolve_user_file_path(1, "sample.bin")
    test_storage_service.move_file(temp_path, user_file_path)

    assert not temp_path.exists()
    assert user_file_path.exists()

    # Stream back
    read_chunks = list(test_storage_service.open_file_stream(user_file_path, chunk_size=8))
    full_read = b"".join(read_chunks)
    assert full_read == content

    # Delete
    test_storage_service.delete_file(user_file_path)
    assert not test_storage_service.file_exists(user_file_path)


def test_write_stream_exceeds_max_limit(test_storage_service: StorageService):
    large_content = b"A" * (1024 * 1024 + 10)  # ~1 MB
    stream = io.BytesIO(large_content)

    # Set tight limit of 500 KB
    with pytest.raises(FileTooLargeError):
        test_storage_service.write_stream_to_temp(stream, max_bytes=500 * 1024)


def test_storage_usage_metrics(test_storage_service: StorageService):
    metrics = test_storage_service.get_storage_usage()
    assert "total_bytes" in metrics
    assert "used_bytes" in metrics
    assert "free_bytes" in metrics
    assert "usage_percent" in metrics
    assert metrics["total_bytes"] > 0
    assert 0.0 <= metrics["usage_percent"] <= 100.0


def test_open_missing_file_raises_not_found(test_storage_service: StorageService):
    missing_path = test_storage_service.get_storage_root() / "users" / "1" / "files" / "nonexistent.bin"
    with pytest.raises(ResourceNotFoundError):
        list(test_storage_service.open_file_stream(missing_path))
