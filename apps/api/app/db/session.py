"""Async SQLAlchemy engine, session factory, lifespan management, and health check."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from urllib.parse import urlparse

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, settings
from app.core.errors import ProblemDetailError

logger = logging.getLogger("opportunity_os.db")


def normalize_async_database_url(raw_url: str) -> str:
    """Validate and normalize PostgreSQL URL to use the asyncpg driver."""
    stripped = raw_url.strip()
    if not stripped:
        raise ValueError("DATABASE_URL must not be empty.")

    parsed = urlparse(stripped)
    if parsed.scheme in ("postgresql", "postgres"):
        return f"postgresql+asyncpg://{stripped.split('://', 1)[1]}"
    if parsed.scheme == "postgresql+asyncpg":
        return stripped
    raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")


class DatabaseManager:
    """Manages async SQLAlchemy engine pooling, sessions, and graceful disposal."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        cfg = app_settings or settings
        url = normalize_async_database_url(cfg.DATABASE_URL)
        self._engine: AsyncEngine = create_async_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=False,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield an AsyncSession with rollback on error and guaranteed close."""
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self, timeout_seconds: float = 2.0) -> bool:
        """Execute bounded SELECT 1 against PostgreSQL without leaking credentials."""
        try:
            async def _ping() -> None:
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

            await asyncio.wait_for(_ping(), timeout=timeout_seconds)
            return True
        except (SQLAlchemyError, OSError, TimeoutError):
            logger.warning("Database health check failed.")
            return False

    async def dispose(self) -> None:
        """Dispose connection pool cleanly on application shutdown."""
        await self._engine.dispose()


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency providing an AsyncSession from app.state.db."""
    db: DatabaseManager | None = getattr(request.app.state, "db", None)
    if db is None:
        raise ProblemDetailError(
            status_code=503,
            problem_type="urn:problem:service_unavailable",
            title="Service Unavailable",
            detail="Database connection pool is not initialized.",
        )
    try:
        async for session in db.session():
            yield session
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("Database session error.")
        raise ProblemDetailError(
            status_code=503,
            problem_type="urn:problem:service_unavailable",
            title="Service Unavailable",
            detail="Database is temporarily unavailable.",
        ) from exc


async def check_db_health(db: DatabaseManager) -> bool:
    """Public helper for checking database connectivity."""
    return await db.health_check()
