"""Activity logging service for auditing user and system actions."""

import json
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog

logger = logging.getLogger("mycloud.activity")

# Sensitive fields that must never be recorded in audit logs
SENSITIVE_KEYS = {"password", "token", "session_token", "secret", "secret_key", "password_hash", "current_password", "new_password"}


def _sanitize_metadata(data: Optional[dict[str, Any]]) -> Optional[str]:
    """Sanitize metadata dictionary and serialize to JSON, stripping sensitive fields."""
    if not data:
        return None

    sanitized = {}
    for k, v in data.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v

    try:
        return json.dumps(sanitized)
    except Exception:
        return None


def log_activity(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ActivityLog:
    """Create and persist an activity log entry."""
    meta_json = _sanitize_metadata(metadata)
    log_entry = ActivityLog(
        user_id=user_id,
        action=action.upper(),
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        metadata_json=meta_json,
    )
    try:
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to persist activity log (%s): %s", action, exc)

    return log_entry
