"""Activity Log database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActivityLog(Base):
    """Audit log for user operations (upload, download, folder creation, auth, etc.)."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # LOGIN, LOGOUT, UPLOAD, DOWNLOAD, CREATE_FOLDER, RENAME, DELETE
    resource_type = Column(String(50), nullable=True)  # user, folder, file, session
    resource_id = Column(String(100), nullable=True)
    metadata_json = Column(Text, nullable=True)  # Non-sensitive JSON payload
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="activities")

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action='{self.action}', resource_type='{self.resource_type}')>"
