from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.api.v1.router import v1_router
from app.core.config import Settings, settings
from app.core.errors import register_exception_handlers
from app.db.session import DatabaseManager
from app.voice.tickets import VoiceTicketStore


def create_application(app_settings: Settings | None = None) -> FastAPI:
    """Application factory for Opportunity OS FastAPI service."""
    cfg = app_settings or settings

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db_manager = DatabaseManager(cfg)
        redis_client: Redis | None = None
        if cfg.REDIS_URL:
            redis_client = Redis.from_url(
                cfg.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
        app.state.db = db_manager
        app.state.redis_client = redis_client
        app.state.voice_ticket_store = VoiceTicketStore(
            ttl_seconds=cfg.VOICE_TICKET_TTL_SECONDS,
            redis_client=redis_client,
            environment=cfg.ENVIRONMENT,
        )
        try:
            yield
        finally:
            if redis_client is not None:
                await redis_client.aclose()
            await db_manager.dispose()

    app = FastAPI(
        title=cfg.APP_NAME,
        version="0.1.0",
        description="Backend API and Agent Gateway for Opportunity OS",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix="/api")

    return app


app = create_application()
