"""Authentication and session management test suite."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_session_token, hash_password, verify_password
from app.models.session import Session as UserSession
from app.models.user import User


def test_login_success_username(client: TestClient, test_user: User, temp_environment: Settings):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "testuser@example.com"
    assert "password_hash" not in data["user"]
    assert temp_environment.COOKIE_NAME in response.cookies


def test_login_success_email(client: TestClient, test_user: User, temp_environment: Settings):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["id"] == test_user.id
    assert temp_environment.COOKIE_NAME in response.cookies


def test_login_invalid_username(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user", "password": "Password123!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_invalid_password(client: TestClient, test_user: User):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_create_initial_admin_updates_existing_admin_password(db: Session, temp_environment: Settings):
    existing = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("OldPassword123!"),
        role="admin",
        is_active=True,
    )
    db.add(existing)
    db.commit()
    db.refresh(existing)

    temp_environment.ADMIN_INITIAL_USERNAME = "admin"
    temp_environment.ADMIN_INITIAL_EMAIL = "admin@example.com"
    temp_environment.ADMIN_INITIAL_PASSWORD = "NewPassword123!"

    from app.db.init_db import create_initial_admin

    updated = create_initial_admin(db, temp_environment)
    assert updated.id == existing.id
    assert verify_password("NewPassword123!", updated.password_hash)
    assert not verify_password("OldPassword123!", updated.password_hash)


def test_get_me_authenticated(auth_client: TestClient, test_user: User):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "password_hash" not in data


def test_get_me_unauthenticated(client: TestClient):
    client.cookies.clear()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_logout_clears_cookie_and_revokes_session(
    auth_client: TestClient, db: Session, test_user: User, temp_environment: Settings
):
    token = auth_client.cookies.get(temp_environment.COOKIE_NAME)
    assert token is not None

    response = auth_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."

    # Session in DB should now be marked revoked
    token_hash = hash_session_token(token)
    session_rec = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
    assert session_rec is not None
    assert session_rec.revoked_at is not None

    # Subsequent request using the old token should be rejected
    auth_client.cookies.set(temp_environment.COOKIE_NAME, token)
    subsequent_response = auth_client.get("/api/v1/auth/me")
    assert subsequent_response.status_code == 401


def test_expired_session(client: TestClient, db: Session, test_user: User, temp_environment: Settings):
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    session_rec = UserSession(
        user_id=test_user.id,
        token_hash=hash_session_token("expired_raw_token"),
        expires_at=expired_time,
        created_at=expired_time - timedelta(hours=2),
        last_used_at=expired_time - timedelta(hours=2),
    )
    db.add(session_rec)
    db.commit()

    client.cookies.set(temp_environment.COOKIE_NAME, "expired_raw_token")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


def test_inactive_user_access(
    client: TestClient, db: Session, test_user: User, temp_environment: Settings
):
    # Disable user
    test_user.is_active = False
    db.commit()

    # Attempt login
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Password123!"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INACTIVE_USER"

    # Restore user active status
    test_user.is_active = True
    db.commit()


def test_change_password(auth_client: TestClient, client: TestClient, test_user: User):
    # 1. Reject invalid current password
    fail_res = auth_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongPassword!", "new_password": "NewSecretPassword123!"},
    )
    assert fail_res.status_code == 401

    # 2. Reject new password that is too short
    short_res = auth_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Password123!", "new_password": "short"},
    )
    assert short_res.status_code == 422

    # 3. Successful change
    ok_res = auth_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Password123!", "new_password": "NewSecretPassword123!"},
    )
    assert ok_res.status_code == 200

    # 4. Login with old password fails
    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Password123!"},
    )
    assert old_login.status_code == 401

    # 5. Login with new password succeeds
    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "NewSecretPassword123!"},
    )
    assert new_login.status_code == 200

    # Restore initial password for other tests
    auth_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "NewSecretPassword123!", "new_password": "Password123!"},
    )
