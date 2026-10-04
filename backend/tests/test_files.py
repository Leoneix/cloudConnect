"""File operations and lifecycle test suite."""

import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.file import File
from app.services.storage_service import StorageService


def test_upload_and_download_file(
    auth_client: TestClient,
    test_storage_service: StorageService,
    db: Session,
):
    file_bytes = b"Hello, MyCloud personal storage test content!"
    filename = "report.txt"

    # 1. Upload file
    upload_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": (filename, io.BytesIO(file_bytes), "text/plain")},
    )
    assert upload_res.status_code == 201
    file_data = upload_res.json()
    file_id = file_data["id"]
    assert file_data["name"] == filename
    assert file_data["size"] == len(file_bytes)
    assert file_data["mime_type"] == "text/plain"
    assert file_data["checksum"] is not None
    assert "storage_name" not in file_data

    # Verify physical file exists on disk
    db_file = db.query(File).filter(File.id == file_id).first()
    assert db_file is not None
    physical_path = test_storage_service.resolve_user_file_path(db_file.owner_id, db_file.storage_name)
    assert physical_path.exists()

    # 2. Download file
    dl_res = auth_client.get(f"/api/v1/files/{file_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.content == file_bytes
    assert "attachment" in dl_res.headers.get("content-disposition", "")


def test_upload_file_inside_folder_uses_folder_disk_path(
    auth_client: TestClient,
    db: Session,
    test_storage_service: StorageService,
):
    folder_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "ProjectDocs", "parent_id": None},
    )
    folder_id = folder_res.json()["id"]
    user = auth_client.get("/api/v1/auth/me").json()
    user_id = user["id"]

    upload_res = auth_client.post(
        "/api/v1/files/upload",
        data={"folder_id": str(folder_id)},
        files={"file": ("inside_folder.txt", io.BytesIO(b"folder content"), "text/plain")},
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["folder_id"] == folder_id

    db_file = db.query(File).filter(File.id == upload_res.json()["id"]).first()
    assert db_file is not None
    expected_path = test_storage_service.resolve_user_dir(user_id) / "folders" / "ProjectDocs" / db_file.storage_name
    assert expected_path.exists()

    list_res = auth_client.get(f"/api/v1/files?folder_id={folder_id}")
    assert list_res.status_code == 200
    assert any(f["name"] == "inside_folder.txt" for f in list_res.json()["files"])


def test_list_files(auth_client: TestClient):
    # Upload two files
    auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("file1.txt", io.BytesIO(b"content1"), "text/plain")},
    )
    auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("file2.txt", io.BytesIO(b"content2"), "text/plain")},
    )

    res = auth_client.get("/api/v1/files")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    filenames = [f["name"] for f in data["files"]]
    assert "file1.txt" in filenames
    assert "file2.txt" in filenames


def test_upload_duplicate_file_in_folder(auth_client: TestClient):
    auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("duplicate_file.txt", io.BytesIO(b"first"), "text/plain")},
    )
    dup_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("duplicate_file.txt", io.BytesIO(b"second"), "text/plain")},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "DUPLICATE_NAME"


def test_rename_file(auth_client: TestClient):
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("before_rename.txt", io.BytesIO(b"test"), "text/plain")},
    )
    file_id = up_res.json()["id"]

    patch_res = auth_client.patch(
        f"/api/v1/files/{file_id}",
        json={"name": "after_rename.txt"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "after_rename.txt"


def test_delete_file_soft_deletion(auth_client: TestClient):
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("to_be_deleted.txt", io.BytesIO(b"delete me"), "text/plain")},
    )
    file_id = up_res.json()["id"]

    # Delete
    del_res = auth_client.delete(f"/api/v1/files/{file_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "File deleted successfully."

    # File should not appear in active file listing
    list_res = auth_client.get("/api/v1/files")
    active_ids = [f["id"] for f in list_res.json()["files"]]
    assert file_id not in active_ids

    # Download should return 404
    dl_res = auth_client.get(f"/api/v1/files/{file_id}/download")
    assert dl_res.status_code == 404


def test_list_includes_untracked_physical_files(auth_client: TestClient, test_storage_service: StorageService):
    user = auth_client.get("/api/v1/auth/me").json()
    user_id = user["id"]
    user_files_dir = test_storage_service.resolve_user_dir(user_id) / "files"
    physical_file = user_files_dir / "existing_on_disk.txt"
    physical_file.write_bytes(b"on-disk-content")

    list_res = auth_client.get("/api/v1/files")
    assert list_res.status_code == 200
    names = [f["name"] for f in list_res.json()["files"]]
    assert "existing_on_disk.txt" in names


def test_delete_file_removes_physical_file(auth_client: TestClient, db: Session, test_storage_service: StorageService):
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("delete_from_disk.txt", io.BytesIO(b"remove me"), "text/plain")},
    )
    file_id = up_res.json()["id"]
    db_file = db.query(File).filter(File.id == file_id).first()
    physical_path = test_storage_service.resolve_user_file_path(db_file.owner_id, db_file.storage_name)
    assert physical_path.exists()

    del_res = auth_client.delete(f"/api/v1/files/{file_id}")
    assert del_res.status_code == 200
    assert not physical_path.exists()


def test_rescan_imports_untracked_physical_files(auth_client: TestClient, db: Session, test_storage_service: StorageService):
    user = auth_client.get("/api/v1/auth/me").json()
    user_id = user["id"]
    user_files_dir = test_storage_service.resolve_user_dir(user_id) / "files"
    physical_file = user_files_dir / "rescan_me.txt"
    physical_file.write_bytes(b"scan me")

    res = auth_client.post("/api/v1/system/rescan")
    assert res.status_code == 200
    assert res.json()["message"] == "Storage rescan completed successfully."

    list_res = auth_client.get("/api/v1/files")
    names = [f["name"] for f in list_res.json()["files"]]
    assert "rescan_me.txt" in names
    assert db.query(File).filter(File.owner_id == user_id, File.name == "rescan_me.txt").count() == 1


def test_unauthorized_file_access(auth_client: TestClient, auth_client2: TestClient):
    # User 1 uploads file
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("secret_user1.txt", io.BytesIO(b"confidential"), "text/plain")},
    )
    file_id = up_res.json()["id"]

    # User 2 attempts download
    dl_res = auth_client2.get(f"/api/v1/files/{file_id}/download")
    assert dl_res.status_code == 403

    # User 2 attempts rename
    patch_res = auth_client2.patch(f"/api/v1/files/{file_id}", json={"name": "hacked.txt"})
    assert patch_res.status_code == 403

    # User 2 attempts delete
    del_res = auth_client2.delete(f"/api/v1/files/{file_id}")
    assert del_res.status_code == 403


def test_storage_inconsistency_handling(
    auth_client: TestClient,
    test_storage_service: StorageService,
    db: Session,
):
    # Upload file
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("inconsistent.txt", io.BytesIO(b"will be deleted on disk"), "text/plain")},
    )
    file_id = up_res.json()["id"]

    # Manually delete physical file to simulate HDD corruption/manual deletion
    db_file = db.query(File).filter(File.id == file_id).first()
    physical_path = test_storage_service.resolve_user_file_path(db_file.owner_id, db_file.storage_name)
    if physical_path.exists():
        physical_path.unlink()

    # Attempt download -> should return 404 with STORAGE_INCONSISTENCY without crashing
    dl_res = auth_client.get(f"/api/v1/files/{file_id}/download")
    assert dl_res.status_code == 404
    assert dl_res.json()["error"]["code"] == "STORAGE_INCONSISTENCY"


def test_large_upload_rejection(auth_client: TestClient):
    # Environment max upload limit in test fixture is 5 MB
    large_payload = b"X" * (6 * 1024 * 1024)  # 6 MB
    res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("huge_file.dat", io.BytesIO(large_payload), "application/octet-stream")},
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
