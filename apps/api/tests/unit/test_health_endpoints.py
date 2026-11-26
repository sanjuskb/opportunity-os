from __future__ import annotations

from collections.abc import Generator
from types import TracebackType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import DatabaseManager
from app.main import create_application


class _FakeDbHealthy:
    async def health_check(self) -> bool:
        return True


class _FakeDbDown:
    async def health_check(self) -> bool:
        return False


class _FakeRedisHealthy:
    async def ping(self) -> bool:
        return True


class _FakeRedisDown:
    async def ping(self) -> bool:
        raise OSError("redis://:super-secret-redis-pass@127.0.0.1:6379/0 refused")


@pytest.fixture
def test_app_client() -> Generator[tuple[TestClient, Any], None, None]:
    settings = Settings(
        ENVIRONMENT="development",
        REDIS_URL="",
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:59999/postgres",
    )
    app = create_application(settings)
    with TestClient(app) as client:
        yield client, app


def test_liveness_returns_200_without_db_or_redis(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbDown()
    app.state.redis_client = _FakeRedisDown()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "development"
    assert "timestamp" in payload


def test_readiness_returns_200_when_db_and_redis_healthy(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbHealthy()
    app.state.redis_client = _FakeRedisHealthy()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["dependencies"] == {
        "database": "healthy",
        "redis": "healthy",
    }
    assert "timestamp" in payload


def test_readiness_returns_503_when_db_unavailable(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbDown()
    app.state.redis_client = _FakeRedisHealthy()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"] == {
        "database": "unavailable",
        "redis": "healthy",
    }


def test_readiness_returns_503_when_redis_unavailable(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbHealthy()
    app.state.redis_client = _FakeRedisDown()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"] == {
        "database": "healthy",
        "redis": "unavailable",
    }


def test_readiness_returns_503_when_both_unavailable(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbDown()
    app.state.redis_client = _FakeRedisDown()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"] == {
        "database": "unavailable",
        "redis": "unavailable",
    }


def test_readiness_does_not_leak_credentials_or_raw_exceptions(
    test_app_client: tuple[TestClient, Any],
) -> None:
    client, app = test_app_client
    app.state.db = _FakeDbDown()
    app.state.redis_client = _FakeRedisDown()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body_text = response.text
    assert "super-secret-redis-pass" not in body_text
    assert "redis://" not in body_text
    assert "refused" not in body_text
    assert "postgresql+asyncpg" not in body_text


@pytest.mark.asyncio
async def test_database_manager_health_check_releases_connection_and_hides_errors() -> None:
    events: list[str] = []

    class _FakeConn:
        async def execute(self, _stmt: Any) -> None:
            events.append("execute")

    class _FakeConnectCtx:
        def __init__(self, should_fail: bool = False) -> None:
            self._should_fail = should_fail

        async def __aenter__(self) -> _FakeConn:
            events.append("enter")
            if self._should_fail:
                raise OSError("postgresql+asyncpg://user:secret-password-123@host/db")
            return _FakeConn()

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            events.append("exit")

    class _FakeEngine:
        def __init__(self, should_fail: bool = False) -> None:
            self._should_fail = should_fail

        def connect(self) -> _FakeConnectCtx:
            return _FakeConnectCtx(should_fail=self._should_fail)

    db_settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:59999/postgres"
    )
    db_ok = DatabaseManager(db_settings)
    db_ok._engine = _FakeEngine(should_fail=False)  # type: ignore[assignment]
    assert await db_ok.health_check() is True
    assert events == ["enter", "execute", "exit"]

    events.clear()
    db_fail = DatabaseManager(db_settings)
    db_fail._engine = _FakeEngine(should_fail=True)  # type: ignore[assignment]
    assert await db_fail.health_check() is False
