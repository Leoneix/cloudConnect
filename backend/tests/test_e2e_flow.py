"""End-to-end integration test exercising the full Definition of Done user journey."""

import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.user import User
from app.services.storage_service import StorageService


def test_full_definition_of_done_journey(
    client: TestClient,
    admin_user: User,
    db: Session,
    test_storage_service: StorageService,
):
    """Verifies the complete flow required by the MyCloud Definition of Done:

    Start -> Health Check -> Login -> Create Folder -> Upload File -> Verify on HDD ->
    List File -> Download File -> Rename File -> Delete File -> Storage Usage -> Logout
    """

    # 1. Health check
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # 2. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "adminuser", "password": "AdminPass123!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["username"] == "adminuser"
    assert "mycloud_session" in login_res.cookies

    # 3. Create folder
    folder_res = client.post(
        "/api/v1/folders",
        json={"name": "Documents", "parent_id": None},
    )
    assert folder_res.status_code == 201
    folder_id = folder_res.json()["id"]

    # 4. Upload file
    file_content = b"MyCloud Confidential MVP Document Content."
    upload_res = client.post(
        "/api/v1/files/upload",
        data={"folder_id": str(folder_id)},
        files={"file": ("report.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert upload_res.status_code == 201
    file_id = upload_res.json()["id"]
    assert upload_res.json()["name"] == "report.pdf"
    assert upload_res.json()["size"] == len(file_content)

    # 5. Verify physical file appears on HDD
    db_file = db.query(File).filter(File.id == file_id).first()
    assert db_file is not None
    physical_path = test_storage_service.resolve_user_file_path(admin_user.id, db_file.storage_name)
    assert physical_path.exists()
    assert physical_path.is_file()

    # 6. List file
    list_res = client.get(f"/api/v1/files?folder_id={folder_id}")
    assert list_res.status_code == 200
    files = list_res.json()["files"]
    assert any(f["id"] == file_id and f["name"] == "report.pdf" for f in files)

    # 7. Download file
    dl_res = client.get(f"/api/v1/files/{file_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.content == file_content
    assert "attachment" in dl_res.headers.get("content-disposition", "")

    # 8. Rename file
    rename_res = client.patch(
        f"/api/v1/files/{file_id}",
        json={"name": "final_report.pdf"},
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "final_report.pdf"

    # 9. Delete file (soft-delete)
    del_res = client.delete(f"/api/v1/files/{file_id}")
    assert del_res.status_code == 200

    # Ensure file is no longer listed
    list_after_res = client.get(f"/api/v1/files?folder_id={folder_id}")
    assert not any(f["id"] == file_id for f in list_after_res.json()["files"])

    # 10. Storage usage
    storage_res = client.get("/api/v1/system/storage")
    assert storage_res.status_code == 200
    usage = storage_res.json()
    assert usage["total_bytes"] > 0
    assert usage["free_bytes"] > 0
    assert 0.0 <= usage["usage_percent"] <= 100.0

    # 11. Logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # Verify session cookie is invalidated
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 401
