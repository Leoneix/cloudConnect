"""Pytest configuration and global test fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.dependencies import get_db, get_storage_service
from app.core.security import hash_password
from app.db.database import Base
from app.main import create_app
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService


@pytest.fixture(scope="session")
def temp_environment():
    """Create temporary directories for database and storage testing."""
    temp_dir = tempfile.mkdtemp(prefix="mycloud_test_")
    db_path = Path(temp_dir) / "test_mycloud.db"
    storage_dir = Path(temp_dir) / "test_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    test_settings = Settings(
        APP_NAME="MyCloud-Test",
        APP_ENV="testing",
        DATABASE_URL=f"sqlite:///{db_path}",
        STORAGE_PATH=str(storage_dir),
        SECRET_KEY="test-secret-key-do-not-use-in-production",
        COOKIE_SECURE=False,
        MAX_UPLOAD_SIZE_MB=5,  # 5 MB for fast testing of limits
    )

    yield test_settings

    # Cleanup temp directory after test suite
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_engine(temp_environment: Settings):
    """Create SQLite engine for testing."""
    engine = create_engine(
        temp_environment.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    """Session factory for tests."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def test_storage_service(temp_environment: Settings) -> StorageService:
    """StorageService configured with temporary storage root."""
    return StorageService(settings=temp_environment)


@pytest.fixture
def db(TestingSessionLocal) -> Generator[Session, None, None]:
    """Provide a transactional database session per test function."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create or return a standard test user."""
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash=hash_password("Password123!"),
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def test_user2(db: Session) -> User:
    """Create or return a second test user for cross-user isolation tests."""
    user = db.query(User).filter(User.username == "seconduser").first()
    if not user:
        user = User(
            username="seconduser",
            email="seconduser@example.com",
            password_hash=hash_password("Password456!"),
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create or return an admin test user."""
    user = db.query(User).filter(User.username == "adminuser").first()
    if not user:
        user = User(
            username="adminuser",
            email="adminuser@example.com",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def app_instance(temp_environment: Settings, TestingSessionLocal, test_storage_service: StorageService):
    """FastAPI application instance with overridden dependencies."""
    application = create_app()

    def override_get_settings():
        return temp_environment

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_get_storage_service():
        return test_storage_service

    application.dependency_overrides[get_settings] = override_get_settings
    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_storage_service] = override_get_storage_service

    return application


@pytest.fixture
def client(app_instance) -> TestClient:
    """Unauthenticated HTTP TestClient."""
    return TestClient(app_instance)


@pytest.fixture
def auth_client(client: TestClient, db: Session, test_user: User, temp_environment: Settings) -> TestClient:
    """HTTP TestClient pre-authenticated as test_user via session cookie."""
    _, raw_token = AuthService.create_session(db, test_user.id)
    client.cookies.set(temp_environment.COOKIE_NAME, raw_token)
    return client


@pytest.fixture
def auth_client2(app_instance, db: Session, test_user2: User, temp_environment: Settings) -> TestClient:
    """HTTP TestClient pre-authenticated as test_user2."""
    cl = TestClient(app_instance)
    _, raw_token = AuthService.create_session(db, test_user2.id)
    cl.cookies.set(temp_environment.COOKIE_NAME, raw_token)
    return cl


@pytest.fixture
def admin_client(app_instance, db: Session, admin_user: User, temp_environment: Settings) -> TestClient:
    """HTTP TestClient pre-authenticated as admin_user."""
    cl = TestClient(app_instance)
    _, raw_token = AuthService.create_session(db, admin_user.id)
    cl.cookies.set(temp_environment.COOKIE_NAME, raw_token)
    return cl
