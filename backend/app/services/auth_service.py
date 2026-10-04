"""Authentication and Session Management Service."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ForbiddenError,
    InactiveUserError,
    SessionExpiredError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models.session import Session as UserSession
from app.models.user import User
from app.services.activity_service import log_activity

logger = logging.getLogger("mycloud.auth")


class AuthService:
    """Authentication and session lifecycle service."""

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user by username or email and verify Argon2 password hash.

        Returns User if valid, None otherwise without leaking user existence.
        """
        identifier = username_or_email.strip().lower()
        user = db.query(User).filter(
            or_(
                User.username.ilike(identifier),
                User.email.ilike(identifier),
            )
        ).first()

        if not user:
            logger.info("Authentication failed: user '%s' not found.", identifier)
            return None

        if not verify_password(password, user.password_hash):
            logger.info("Authentication failed: invalid password for user '%s'.", user.username)
            return None

        if not user.is_active:
            logger.warning("Authentication failed: user '%s' is inactive.", user.username)
            raise InactiveUserError("Your user account has been disabled.")

        # Update last login time
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)

        log_activity(db, action="LOGIN", user_id=user.id, resource_type="user", resource_id=str(user.id))
        return user

    @staticmethod
    def create_session(db: Session, user_id: int, expire_minutes: Optional[int] = None) -> tuple[UserSession, str]:
        """Generate a random session token, store its cryptographic hash in SQLite, and return (session, raw_token)."""
        settings = get_settings()
        minutes = expire_minutes or settings.SESSION_EXPIRE_MINUTES

        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=minutes)

        session_record = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=now,
            last_used_at=now,
        )
        db.add(session_record)
        db.commit()
        db.refresh(session_record)

        return session_record, raw_token

    @staticmethod
    def get_current_user_from_token(db: Session, raw_token: str) -> User:
        """Validate raw session token and return the active User.

        Checks:
        1. Token exists and hashes to valid record
        2. Session is not revoked
        3. Session is not expired
        4. User exists and is active
        """
        if not raw_token:
            raise UnauthorizedError("Authentication token is missing.")

        token_hash = hash_session_token(raw_token)
        session_record = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()

        if not session_record:
            raise UnauthorizedError("Invalid session.")

        if session_record.is_revoked:
            raise SessionExpiredError("Session has been revoked.")

        if session_record.is_expired:
            raise SessionExpiredError("Session has expired.")

        user = db.query(User).filter(User.id == session_record.user_id).first()
        if not user:
            raise UnauthorizedError("User account no longer exists.")

        if not user.is_active:
            raise InactiveUserError("User account is inactive.")

        # Touch last_used_at periodically (e.g. if > 1 minute old)
        now = datetime.now(timezone.utc)
        last_used = session_record.last_used_at
        if last_used.tzinfo is None:
            last_used = last_used.replace(tzinfo=timezone.utc)

        if (now - last_used).total_seconds() > 60:
            session_record.last_used_at = now
            db.commit()

        return user

    @staticmethod
    def revoke_session(db: Session, raw_token: str) -> bool:
        """Revoke a session by marking revoked_at timestamp in the database."""
        if not raw_token:
            return False

        token_hash = hash_session_token(raw_token)
        session_record = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        if session_record:
            session_record.revoked_at = datetime.now(timezone.utc)
            db.commit()
            log_activity(
                db,
                action="LOGOUT",
                user_id=session_record.user_id,
                resource_type="session",
                resource_id=str(session_record.id),
            )
            return True
        return False

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
        """Verify current password and set a newly hashed Argon2 password."""
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect.", code="INVALID_PASSWORD")

        if len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters long.")

        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)

        log_activity(db, action="CHANGE_PASSWORD", user_id=user.id, resource_type="user", resource_id=str(user.id))
        return user
