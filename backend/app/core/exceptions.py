"""Application specific exceptions with structured error codes and messages."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception with error code, status code, and client-safe message."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


# Authentication & Authorization Errors (401, 403)
class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid authentication credentials.", code: str = "INVALID_CREDENTIALS"):
        super().__init__(code=code, message=message, status_code=401)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required.", code: str = "AUTHENTICATION_REQUIRED"):
        super().__init__(code=code, message=message, status_code=401)


class SessionExpiredError(AppException):
    def __init__(self, message: str = "Session has expired or is invalid.", code: str = "SESSION_EXPIRED"):
        super().__init__(code=code, message=message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "You do not have permission to access this resource.", code: str = "PERMISSION_DENIED"):
        super().__init__(code=code, message=message, status_code=403)


class InactiveUserError(AppException):
    def __init__(self, message: str = "User account is inactive.", code: str = "INACTIVE_USER"):
        super().__init__(code=code, message=message, status_code=403)


# Resource Not Found Errors (404)
class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Requested resource was not found.", code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=404)


class FileNotFoundAppError(ResourceNotFoundError):
    def __init__(self, message: str = "The requested file was not found.", code: str = "FILE_NOT_FOUND"):
        super().__init__(message=message, code=code)


class FolderNotFoundAppError(ResourceNotFoundError):
    def __init__(self, message: str = "The requested folder was not found.", code: str = "FOLDER_NOT_FOUND"):
        super().__init__(message=message, code=code)


# Conflict Errors (409)
class ConflictError(AppException):
    def __init__(self, message: str = "A conflict occurred with an existing resource.", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=409)


class DuplicateNameError(ConflictError):
    def __init__(self, message: str = "An item with this name already exists in this folder.", code: str = "DUPLICATE_NAME"):
        super().__init__(message=message, code=code)


# Validation & Bad Request Errors (400, 422)
class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed for the request data.", code: str = "VALIDATION_ERROR", details: Optional[Any] = None):
        super().__init__(code=code, message=message, status_code=422, details=details)


class InvalidFilenameError(AppException):
    def __init__(self, message: str = "The specified filename is invalid or contains forbidden characters.", code: str = "INVALID_FILENAME"):
        super().__init__(code=code, message=message, status_code=400)


class PathTraversalError(AppException):
    def __init__(self, message: str = "Access to the requested path is forbidden.", code: str = "PATH_TRAVERSAL_DETECTED"):
        super().__init__(code=code, message=message, status_code=400)


# Payload & Storage Limit Errors (413, 507)
class FileTooLargeError(AppException):
    def __init__(self, message: str = "Uploaded file exceeds the maximum allowed size.", code: str = "PAYLOAD_TOO_LARGE"):
        super().__init__(code=code, message=message, status_code=413)


class InsufficientStorageError(AppException):
    def __init__(self, message: str = "Insufficient storage space on the disk.", code: str = "INSUFFICIENT_STORAGE"):
        super().__init__(code=code, message=message, status_code=507)


class StorageInconsistencyError(AppException):
    def __init__(self, message: str = "Storage file inconsistency detected.", code: str = "STORAGE_INCONSISTENCY"):
        super().__init__(code=code, message=message, status_code=404)
