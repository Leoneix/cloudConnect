"""Authentication API router."""

import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_active_user, get_db, get_session_token
from app.core.exceptions import AuthenticationError
from app.models.user import User
from app.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger("mycloud.api.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate with username/email and password, returning user info and setting an HTTP-only session cookie.",
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    user = AuthService.authenticate_user(db, payload.username, payload.password)
    if not user:
        # Generic message to avoid username enumeration
        raise AuthenticationError("Invalid username or password.")

    session_record, raw_token = AuthService.create_session(db, user.id)

    max_age_seconds = settings.SESSION_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        max_age=max_age_seconds,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Login successful",
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Revoke the current session and clear the session cookie.",
)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    token: str = Depends(get_session_token),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    if token:
        AuthService.revoke_session(db, token)

    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
    description="Retrieve the profile details of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change the current user password after verifying the existing password.",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    AuthService.change_password(db, current_user, payload.current_password, payload.new_password)
    return MessageResponse(message="Password changed successfully.")
