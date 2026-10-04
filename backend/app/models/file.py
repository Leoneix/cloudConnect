"""File database model."""

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class File(Base):
    """File metadata model mapping user filenames to isolated physical storage objects."""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # User visible name, e.g. "document.pdf"
    storage_name = Column(String(255), unique=True, index=True, nullable=False)  # e.g. "550e8400-e29b-41d4-a716-446655440000.pdf"
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    size = Column(BigInteger, nullable=False)  # File size in bytes
    mime_type = Column(String(128), nullable=True)
    extension = Column(String(32), nullable=True)
    checksum = Column(String(64), nullable=True, index=True)  # SHA-256 hex digest
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft-deletion

    # Relationships
    owner = relationship("User", back_populates="files")
    folder = relationship("Folder", back_populates="files")

    @property
    def is_deleted(self) -> bool:
        """Check if file has been soft-deleted."""
        return self.deleted_at is not None

    def __repr__(self) -> str:
        return f"<File(id={self.id}, name='{self.name}', storage_name='{self.storage_name}', owner_id={self.owner_id}, size={self.size})>"
