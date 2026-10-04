"""Authentication Pydantic schemas."""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """User login payload supporting username or email."""

    username: str = Field(..., description="Username or email address", min_length=1, max_length=255)
    password: str = Field(..., description="Plaintext password", min_length=1)


class ChangePasswordRequest(BaseModel):
    """User change password payload."""

    current_password: str = Field(..., description="Current password", min_length=1)
    new_password: str = Field(..., description="New password", min_length=8, max_length=128)


class AuthResponse(BaseModel):
    """Successful authentication response."""

    user: UserResponse
    message: str = "Authenticated successfully"
