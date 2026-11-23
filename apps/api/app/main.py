from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Application factory for Opportunity OS FastAPI service."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Backend API and Agent Gateway for Opportunity OS",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix="/api")

    return app


app = create_application()
