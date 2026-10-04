"""MyCloud Backend entry point.

Starts the Uvicorn ASGI server with the configuration specified in settings / .env.
"""

import logging
import sys
import uvicorn

from app.core.config import get_settings


def main():
    settings = get_settings()
    log_level = "debug" if settings.APP_ENV == "development" else "info"

    print(f"Starting {settings.APP_NAME} ({settings.APP_ENV}) on http://{settings.HOST}:{settings.PORT}")
    print(f"Storage path configured: {settings.STORAGE_PATH}")
    print(f"Interactive API docs available at: http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
