"""Security utilities: Argon2id password hashing, session tokens, and path/filename validation."""

import hashlib
import re
import secrets
from pathlib import Path
from typing import Final

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.exceptions import InvalidFilenameError, PathTraversalError

# Argon2id password hasher with secure defaults
_hasher = PasswordHasher()

# Windows reserved device names that cannot be used as filenames or directories
WINDOWS_RESERVED_NAMES: Final[set[str]] = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Characters forbidden in Windows filenames: < > : " / \ | ? * and ASCII 0-31
FORBIDDEN_CHARS_PATTERN: Final[re.Pattern] = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_session_token() -> str:
    """Generate a high-entropy URL-safe random session token."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Hash a session token with SHA-256 for deterministic database lookup without storing raw tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_and_sanitize_filename(name: str) -> str:
    """Validate and sanitize a user-supplied filename or folder name.

    Ensures the name:
    - Is non-empty
    - Does not contain leading or trailing whitespace
    - Does not contain path traversal components (.. or .)
    - Does not contain Windows forbidden characters (< > : " / \\ | ? * and control chars)
    - Does not match Windows reserved device names (CON, NUL, AUX, PRN, COM1-9, LPT1-9)
    - Does not end with a dot or space (Windows restriction)
    - Does not exceed 255 characters
    - Does not contain UNC prefixes or drive specifications
    """
    if not name or not isinstance(name, str):
        raise InvalidFilenameError("Filename cannot be empty.")

    # Reject null bytes immediately
    if "\x00" in name:
        raise PathTraversalError("Null byte detected in filename.")

    # Reject leading or trailing whitespace
    if name != name.strip():
        raise InvalidFilenameError("Filename cannot contain leading or trailing whitespace.")

    # Check for empty string after strip
    if not name:
        raise InvalidFilenameError("Filename cannot be empty.")

    # Check length
    if len(name) > 255:
        raise InvalidFilenameError("Filename exceeds maximum allowed length of 255 characters.")

    # Check for traversal indicators
    if name in {".", ".."} or ".." in name or "/" in name or "\\" in name:
        raise PathTraversalError("Path traversal characters are not permitted in filenames.")

    # Check for drive colon or UNC
    if ":" in name or name.startswith("//") or name.startswith("\\\\"):
        raise PathTraversalError("Absolute or UNC paths are not permitted.")

    # Check for forbidden Windows characters
    if FORBIDDEN_CHARS_PATTERN.search(name):
        raise InvalidFilenameError("Filename contains illegal characters.")

    # Windows filenames cannot end in a trailing dot
    if name.endswith("."):
        raise InvalidFilenameError("Filename cannot end with a dot.")

    # Check for Windows reserved device names (e.g. 'CON', 'con.txt', 'NUL.tar.gz')
    base_name = name.split(".")[0].upper()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise InvalidFilenameError(f"'{base_name}' is a reserved Windows device name.")

    return name
