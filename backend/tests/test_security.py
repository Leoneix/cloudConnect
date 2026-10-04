"""Security validation and path traversal vulnerability test suite."""

import io
import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import InvalidFilenameError, PathTraversalError
from app.core.security import validate_and_sanitize_filename
from app.services.storage_service import StorageService


@pytest.mark.parametrize(
    "traversal_payload",
    [
        "../../Windows/System32",
        r"..\..\Windows\System32",
        r"..\..\..\etc\passwd",
        "C:\\Windows\\System32",
        "D:\\sensitive_data.txt",
        r"\\192.168.1.1\share\exploit.txt",
        r"//192.168.1.1/share/exploit.txt",
        "..",
        ".",
        "../test.txt",
        "..\\test.txt",
        "nested/../../secret.txt",
        "nested\\..\\..\\secret.txt",
    ],
)
def test_storage_service_rejects_path_traversal(
    test_storage_service: StorageService, traversal_payload: str
):
    with pytest.raises(PathTraversalError):
        test_storage_service.validate_path(traversal_payload)


@pytest.mark.parametrize(
    "invalid_name",
    [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM9",
        "LPT1",
        "LPT8",
        "con.txt",
        "aux.pdf",
        "NUL.tar.gz",
        "com1.doc",
        "file<name>.txt",
        "file>name.txt",
        "file:name.txt",
        'file"name.txt',
        "file/name.txt",
        "file\\name.txt",
        "file|name.txt",
        "file?name.txt",
        "file*name.txt",
        "trailing_dot.",
        "trailing_space ",
        "   ",
        "",
        "a" * 256,
    ],
)
def test_filename_validator_rejects_malicious_inputs(invalid_name: str):
    with pytest.raises((InvalidFilenameError, PathTraversalError)):
        validate_and_sanitize_filename(invalid_name)


def test_null_byte_rejection():
    with pytest.raises(PathTraversalError):
        validate_and_sanitize_filename("valid_name.txt\x00.exe")


def test_api_folder_creation_rejects_path_traversal(auth_client: TestClient):
    traversals = [
        "../../Windows/System32",
        r"..\..\Windows\System32",
        "C:\\Windows",
        "CON",
        "invalid|folder?name",
    ]
    for bad_name in traversals:
        res = auth_client.post("/api/v1/folders", json={"name": bad_name, "parent_id": None})
        assert res.status_code in {400, 422}
        assert res.json()["error"]["code"] in {"PATH_TRAVERSAL_DETECTED", "INVALID_FILENAME", "VALIDATION_ERROR"}


def test_api_file_upload_rejects_path_traversal(auth_client: TestClient):
    traversals = [
        "../../Windows/System32/cmd.exe",
        r"..\..\boot.ini",
        "CON.txt",
        "aux.dat",
        "bad:name.txt",
    ]
    for bad_filename in traversals:
        res = auth_client.post(
            "/api/v1/files/upload",
            files={"file": (bad_filename, io.BytesIO(b"malicious"), "text/plain")},
        )
        assert res.status_code in {400, 422}


def test_api_file_rename_rejects_path_traversal(auth_client: TestClient):
    # Upload a valid file first
    up_res = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("legit.txt", io.BytesIO(b"content"), "text/plain")},
    )
    file_id = up_res.json()["id"]

    # Try renaming to malicious targets
    bad_renames = [
        "../../Windows/calc.exe",
        r"..\..\autoexec.bat",
        "NUL.txt",
        "illegal*name.txt",
    ]
    for bad_name in bad_renames:
        res = auth_client.patch(f"/api/v1/files/{file_id}", json={"name": bad_name})
        assert res.status_code in {400, 422}


def test_cross_user_file_id_tampering_isolated(auth_client: TestClient, auth_client2: TestClient):
    # User 1 uploads confidential file
    res1 = auth_client.post(
        "/api/v1/files/upload",
        files={"file": ("financials.csv", io.BytesIO(b"secret salary data"), "text/csv")},
    )
    user1_file_id = res1.json()["id"]

    # User 2 tries to read/download/rename/delete
    dl_res = auth_client2.get(f"/api/v1/files/{user1_file_id}/download")
    assert dl_res.status_code == 403

    rename_res = auth_client2.patch(f"/api/v1/files/{user1_file_id}", json={"name": "leaked.csv"})
    assert rename_res.status_code == 403

    del_res = auth_client2.delete(f"/api/v1/files/{user1_file_id}")
    assert del_res.status_code == 403
