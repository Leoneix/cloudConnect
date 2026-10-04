"""Database and storage directory initialization script."""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_password, verify_password
from app.db.database import Base, SessionLocal, engine
from app.models import User

# Ensure all models are imported so Base metadata knows about them
import app.models  # noqa: F401

logger = logging.getLogger("mycloud.init_db")


def init_storage_directories(settings: Settings) -> None:
    """Create the storage root directory and required internal subdirectories."""
    storage_root = Path(settings.STORAGE_PATH).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)

    # Subdirectories for organized data
    (storage_root / "users").mkdir(parents=True, exist_ok=True)
    (storage_root / "tmp").mkdir(parents=True, exist_ok=True)

    logger.info("Storage directories initialized at: %s", storage_root)


def create_initial_admin(db: Session, settings: Settings) -> Optional[User]:
    """Create the initial admin user if missing or resync the stored admin credentials to the current environment config."""
    existing_admin = db.query(User).filter(User.username == settings.ADMIN_INITIAL_USERNAME).first()
    if existing_admin:
        needs_update = (
            existing_admin.email != settings.ADMIN_INITIAL_EMAIL
            or existing_admin.username != settings.ADMIN_INITIAL_USERNAME
            or not verify_password(settings.ADMIN_INITIAL_PASSWORD, existing_admin.password_hash)
        )

        if needs_update:
            existing_admin.username = settings.ADMIN_INITIAL_USERNAME
            existing_admin.email = settings.ADMIN_INITIAL_EMAIL
            existing_admin.password_hash = hash_password(settings.ADMIN_INITIAL_PASSWORD)
            existing_admin.is_active = True
            existing_admin.role = "admin"
            db.commit()
            db.refresh(existing_admin)
            logger.info("Updated existing admin user credentials to match current environment configuration.")
        else:
            logger.info("Admin user '%s' already exists and matches the current configuration.", settings.ADMIN_INITIAL_USERNAME)
        return existing_admin

    admin_user = User(
        username=settings.ADMIN_INITIAL_USERNAME,
        email=settings.ADMIN_INITIAL_EMAIL,
        password_hash=hash_password(settings.ADMIN_INITIAL_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    logger.info("Created initial admin user: %s (%s)", admin_user.username, admin_user.email)
    return admin_user


def init_db(settings: Optional[Settings] = None, create_admin: bool = True) -> None:
    """Initialize database tables, storage directory structure, and seed initial admin."""
    if settings is None:
        settings = get_settings()

    # 1. Ensure storage paths exist
    init_storage_directories(settings)

    # 2. Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

    # 3. Create initial admin if requested
    if create_admin:
        db = SessionLocal()
        try:
            create_initial_admin(db, settings)
        finally:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    print("Initializing MyCloud database and storage...")
    init_db()
    print("Initialization complete.")
