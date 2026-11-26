"""Unit tests for async database URL normalization, session errors, and cursor encoding."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.errors import ProblemDetailError
from app.db.session import DatabaseManager, get_db_session, normalize_async_database_url
from app.repositories.opportunities import decode_opportunity_cursor, encode_opportunity_cursor


def test_normalize_async_database_url() -> None:
    assert (
        normalize_async_database_url("postgresql://user:pass@localhost:54322/postgres")
        == "postgresql+asyncpg://user:pass@localhost:54322/postgres"
    )
    assert (
        normalize_async_database_url("postgres://user:pass@localhost:54322/postgres")
        == "postgresql+asyncpg://user:pass@localhost:54322/postgres"
    )
    assert (
        normalize_async_database_url("postgresql+asyncpg://user:pass@localhost:54322/postgres")
        == "postgresql+asyncpg://user:pass@localhost:54322/postgres"
    )

    with pytest.raises(ValueError, match="must not be empty"):
        normalize_async_database_url("")

    with pytest.raises(ValueError, match="Unsupported DATABASE_URL scheme"):
        normalize_async_database_url("mysql://user:pass@localhost/db")


@pytest.mark.asyncio
async def test_database_health_check_handles_connection_failure_safely() -> None:
    db = DatabaseManager(
        Settings(DATABASE_URL="postgresql+asyncpg://postgres:secret@127.0.0.1:59999/postgres")
    )
    try:
        healthy = await db.health_check()
        assert healthy is False
    finally:
        await db.dispose()


@pytest.mark.asyncio
async def test_get_db_session_raises_503_when_uninitialized() -> None:
    fake_request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    gen = get_db_session(fake_request)  # type: ignore[arg-type]
    with pytest.raises(ProblemDetailError) as exc:
        await anext(gen)
    assert exc.value.status_code == 503


def test_opportunity_cursor_round_trip() -> None:
    ts = datetime(2026, 11, 26, 3, 15, 0, tzinfo=UTC)
    uid = uuid4()
    cursor = encode_opportunity_cursor(ts, uid)
    decoded_ts, decoded_uid = decode_opportunity_cursor(cursor)
    assert decoded_ts == ts
    assert decoded_uid == uid
