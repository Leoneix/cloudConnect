"""FastAPI dependency injection providers for database, security, and services."""

from typing import Optional
from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, InactiveUserError, UnauthorizedError
from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService

_storage_service_instance: Optional[StorageService] = None


def get_storage_service(settings: Settings = Depends(get_settings)) -> StorageService:
    """Return a singleton or injected StorageService instance."""
    global _storage_service_instance
    if _storage_service_instance is None:
        _storage_service_instance = StorageService(settings=settings)
    return _storage_service_instance


def get_session_token(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    """Extract session token from HTTP-only cookie or Authorization Bearer header."""
    # 1. Primary: Cookie
    cookie_token = request.cookies.get(settings.COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # 2. Secondary: Bearer header (allows CLI / automated scripts / Tailscale tools)
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return None


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_session_token),
) -> User:
    """Retrieve and validate the current authenticated user from session token."""
    if not token:
        raise UnauthorizedError("Authentication session is required.")

    return AuthService.get_current_user_from_token(db, token)


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure that the authenticated user is currently active."""
    if not current_user.is_active:
        raise InactiveUserError("Your account is disabled.")
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure that the authenticated user has the 'admin' role."""
    if current_user.role != "admin":
        raise ForbiddenError("Administrative privileges required.")
    return current_user
