"""API routers package."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.folders import router as folders_router
from app.api.system import system_router

# Master v1 API Router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(folders_router)
api_v1_router.include_router(files_router)
api_v1_router.include_router(system_router)

__all__ = ["api_v1_router", "auth_router", "folders_router", "files_router", "system_router"]
