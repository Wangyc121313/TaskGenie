import io
import sys
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import current_settings
from app.routers import ai_router, general_router, profile_router, task_router


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def create_app() -> FastAPI:
    app = FastAPI(
        title="TaskGenie API",
        description="AI-assisted task planning and scheduling API.",
        version=current_settings.APP_VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(task_router)
    app.include_router(ai_router)
    app.include_router(profile_router)
    app.include_router(general_router)

    @app.get("/")
    async def root():
        return {
            "message": "TaskGenie API v2.0",
            "description": current_settings.APP_DESCRIPTION,
            "features": [
                "task management",
                "AI task planning",
                "AI day scheduling",
                "task analytics",
            ],
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": current_settings.APP_VERSION,
            "timestamp": datetime.now().isoformat(),
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
