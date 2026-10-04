"""Folder API and management test suite."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.models.file import File
from app.services.folder_service import FolderService
from app.services.storage_service import StorageService


def test_create_folder_root(auth_client: TestClient):
    response = auth_client.post(
        "/api/v1/folders",
        json={"name": "Documents", "parent_id": None},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Documents"
    assert data["parent_id"] is None
    assert "id" in data


def test_create_nested_folder(auth_client: TestClient):
    # 1. Parent folder
    p_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "Projects", "parent_id": None},
    )
    assert p_res.status_code == 201
    parent_id = p_res.json()["id"]

    # 2. Child folder
    c_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "MyCloud-MVP", "parent_id": parent_id},
    )
    assert c_res.status_code == 201
    assert c_res.json()["parent_id"] == parent_id

    # 3. Verify parent folder contents
    contents_res = auth_client.get(f"/api/v1/folders/{parent_id}")
    assert contents_res.status_code == 200
    subfolders = contents_res.json()["subfolders"]
    assert any(sf["name"] == "MyCloud-MVP" for sf in subfolders)


def test_create_duplicate_folder_name(auth_client: TestClient):
    auth_client.post(
        "/api/v1/folders",
        json={"name": "UniqueFolder", "parent_id": None},
    )
    dup_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "UniqueFolder", "parent_id": None},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "DUPLICATE_NAME"


def test_create_folder_invalid_parent(auth_client: TestClient):
    res = auth_client.post(
        "/api/v1/folders",
        json={"name": "GhostChild", "parent_id": 99999},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "FOLDER_NOT_FOUND"


def test_rename_folder(auth_client: TestClient):
    res = auth_client.post(
        "/api/v1/folders",
        json={"name": "OldFolderName", "parent_id": None},
    )
    folder_id = res.json()["id"]

    rename_res = auth_client.patch(
        f"/api/v1/folders/{folder_id}",
        json={"name": "NewFolderName"},
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "NewFolderName"


def test_delete_folder(auth_client: TestClient, db: Session):
    res = auth_client.post(
        "/api/v1/folders",
        json={"name": "FolderToDelete", "parent_id": None},
    )
    folder_id = res.json()["id"]

    del_res = auth_client.delete(f"/api/v1/folders/{folder_id}")
    assert del_res.status_code == 200

    # Ensure folder is gone
    get_res = auth_client.get(f"/api/v1/folders/{folder_id}")
    assert get_res.status_code == 404


def test_rescan_removes_folder_deleted_from_disk(auth_client: TestClient, db: Session, test_user, temp_environment):
    create_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "DeletedOnDisk", "parent_id": None},
    )
    assert create_res.status_code == 201
    folder_id = create_res.json()["id"]

    storage_service = StorageService(settings=temp_environment)
    disk_path = storage_service.resolve_user_dir(test_user.id) / "folders" / "DeletedOnDisk"
    assert disk_path.exists()

    # Simulate user deleting the folder from disk without using the portal
    for child in sorted(disk_path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    if disk_path.exists():
        disk_path.rmdir()

    FolderService.sync_physical_folders_for_user(db, storage_service, test_user.id)

    assert db.query(Folder).filter(Folder.id == folder_id).first() is None
    assert db.query(File).filter(File.folder_id == folder_id).count() == 0


def test_unauthorized_folder_access(auth_client: TestClient, auth_client2: TestClient):
    # User 1 creates folder
    create_res = auth_client.post(
        "/api/v1/folders",
        json={"name": "User1PrivateFolder", "parent_id": None},
    )
    folder_id = create_res.json()["id"]

    # User 2 attempts access
    get_res = auth_client2.get(f"/api/v1/folders/{folder_id}")
    assert get_res.status_code == 403

    # User 2 attempts rename
    patch_res = auth_client2.patch(f"/api/v1/folders/{folder_id}", json={"name": "HackedFolder"})
    assert patch_res.status_code == 403

    # User 2 attempts delete
    del_res = auth_client2.delete(f"/api/v1/folders/{folder_id}")
    assert del_res.status_code == 403
