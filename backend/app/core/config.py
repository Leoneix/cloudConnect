"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Config
    APP_NAME: str = "MyCloud"
    APP_ENV: Literal["development", "production", "testing"] = "development"

    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./data/mycloud.db"

    # Storage Path (Dedicated external HDD root or local dev folder)
    STORAGE_PATH: str = "./data/storage"

    # Session & Security
    SESSION_EXPIRE_MINUTES: int = 10080  # 7 days
    MAX_UPLOAD_SIZE_MB: int = 5120  # 5 GB
    SECRET_KEY: str = "change-this-in-production-to-a-secure-random-string"

    # Cookie Settings
    COOKIE_NAME: str = "mycloud_session"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_HTTPONLY: bool = True
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173,http://100.99.177.87:5173"

    # Initial Admin Setup
    ADMIN_INITIAL_USERNAME: str = "admin"
    ADMIN_INITIAL_EMAIL: str = "admin@example.com"
    ADMIN_INITIAL_PASSWORD: str = "Admin123456!"

    @property
    def max_upload_size_bytes(self) -> int:
        """Calculate max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured CORS origins as a clean list of strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def resolved_storage_path(self) -> Path:
        """Return the fully resolved absolute Path for the configured storage directory."""
        return Path(self.STORAGE_PATH).resolve()


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
