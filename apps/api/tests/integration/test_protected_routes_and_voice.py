"""Integration tests for protected FastAPI routes, RFC 7807 errors, Redis tickets & Voice WS."""

from __future__ import annotations

from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import get_db_session
from app.main import create_application
from app.voice.tickets import VoiceTicketStore, get_voice_ticket_store

TEST_SECRET = "test-super-secret-supabase-jwt-key-32-chars"
TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _make_token(
    user_id: UUID,
    *,
    role: str = "authenticated",
    exp_delta_seconds: int = 3600,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=exp_delta_seconds)).timestamp()),
            "role": role,
            "email": "student@iitb.ac.in",
        },
        TEST_SECRET,
        algorithm="HS256",
    )


class _FakeScalarSequence:
    def all(self) -> list[Any]:
        return []


class _FakeExecuteResult:
    def scalars(self) -> _FakeScalarSequence:
        return _FakeScalarSequence()

    def scalar_one_or_none(self) -> None:
        return None


class _FakeAsyncSession:
    """Minimal AsyncSession stub for DB-independent API & auth tests."""

    async def execute(self, _stmt: Any) -> _FakeExecuteResult:
        return _FakeExecuteResult()

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        return None


@contextmanager
def _isolated_test_client(
    ticket_ttl_seconds: int = 30,
) -> Generator[tuple[TestClient, VoiceTicketStore], None, None]:
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    ticket_store = VoiceTicketStore(ttl_seconds=ticket_ttl_seconds, environment="development")

    async def _override_db_session() -> AsyncIterator[_FakeAsyncSession]:
        yield _FakeAsyncSession()

    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_voice_ticket_store] = lambda: ticket_store
    app.dependency_overrides[get_db_session] = _override_db_session  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client, ticket_store
    finally:
        app.dependency_overrides.clear()


class _FakeAsyncRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.data: dict[str, tuple[str, int]] = {}
        self.fail = fail
        self.last_ex: int | None = None

    async def set(self, key: str, value: str, ex: int) -> None:
        if self.fail:
            raise RedisError("redis connection failed")
        self.last_ex = ex
        self.data[key] = (value, ex)

    async def getdel(self, key: str) -> str | None:
        if self.fail:
            raise RedisError("redis connection failed")
        entry = self.data.pop(key, None)
        return entry[0] if entry is not None else None


def test_public_endpoints_remain_accessible_without_auth() -> None:
    with _isolated_test_client() as (client, _):
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/opportunities").status_code == 200


def test_protected_endpoint_without_authorization_returns_401_rfc7807() -> None:
    with _isolated_test_client() as (client, _):
        for method, path in (
            ("GET", "/api/v1/users/me"),
            ("POST", "/api/v1/opportunities/discover"),
            ("POST", "/api/v1/eligibility/evaluate"),
            ("POST", "/api/v1/voice/tickets"),
        ):
            resp = client.request(method, path)
            assert resp.status_code == 401
            assert resp.headers["content-type"].startswith("application/problem+json")
            assert resp.json()["type"] == "urn:problem:unauthorized"


def test_anon_role_rejected_with_403_across_student_and_voice_endpoints() -> None:
    with _isolated_test_client() as (client, _):
        token = _make_token(uuid4(), role="anon")
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get("/api/v1/users/me", headers=headers).status_code == 403
        assert (
            client.post(
                "/api/v1/opportunities/discover", headers=headers, json={"query": "python"}
            ).status_code
            == 403
        )
        assert client.post("/api/v1/voice/tickets", headers=headers).status_code == 403


def test_get_me_uses_jwt_identity_and_rejects_non_bearer_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1 import router as router_module
    from app.schemas.common import ProfileResponse

    uid = uuid4()
    seen_user_ids: list[UUID] = []

    class _FakeProfileService:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_profile(self, current_user: Any) -> ProfileResponse:
            seen_user_ids.append(current_user.user_id)
            return ProfileResponse(
                user_id=current_user.user_id,
                email=current_user.email or "student@iitb.ac.in",
                full_name="Test Student",
                preferred_language="en",
                supabase_role=current_user.supabase_role,
            )

    monkeypatch.setattr(router_module, "ProfileService", _FakeProfileService)

    with _isolated_test_client() as (client, _):
        bad_scheme = client.get("/api/v1/users/me", headers={"Authorization": "Basic abc"})
        assert bad_scheme.status_code == 401

        token = _make_token(uid)
        resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["userId"] == str(uid)
        assert body["supabaseRole"] == "authenticated"
        assert seen_user_ids == [uid]


def test_user_identity_derived_from_jwt_ignoring_client_user_id() -> None:
    from app.models.entities import Opportunity

    with _isolated_test_client() as (client, _):
        real_user = uuid4()
        spoofed_user = uuid4()
        opp_id = uuid4()
        token = _make_token(real_user)

        fake_opp = Opportunity(
            id=opp_id,
            title="Backend API Intern",
            organization="NexteRaS",
            location="Remote",
            type="internship",
            description="Python & PostgreSQL internship",
            source_url="https://example.com/opp",
            source_provider="manual",
            is_active=True,
        )

        class _OppScalarSeq:
            def all(self) -> list[Any]:
                return []

        class _OppExecuteResult:
            def __init__(self, scalar: Any) -> None:
                self._scalar = scalar

            def scalars(self) -> _OppScalarSeq:
                return _OppScalarSeq()

            def scalar_one_or_none(self) -> Any:
                return self._scalar

        class _OppFakeSession(_FakeAsyncSession):
            def __init__(self) -> None:
                self._calls = 0

            async def execute(self, _stmt: Any) -> _OppExecuteResult:  # type: ignore[override]
                self._calls += 1
                # First execute in EligibilityService.evaluate loads Opportunity by id
                return _OppExecuteResult(fake_opp if self._calls == 1 else None)

        async def _override_opp_db() -> AsyncIterator[_OppFakeSession]:
            yield _OppFakeSession()

        from fastapi.testclient import TestClient

        # Override session for this request on the same app via dependency_overrides
        app_ref: Any = client.app
        app_ref.dependency_overrides[get_db_session] = _override_opp_db
        with TestClient(app_ref) as opp_client:
            resp = opp_client.post(
                "/api/v1/eligibility/evaluate",
                headers={"Authorization": f"Bearer {token}"},
                json={"opportunityId": str(opp_id), "studentId": str(spoofed_user)},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["studentId"] == str(real_user)
            assert data["studentId"] != str(spoofed_user)


def test_approval_endpoint_returns_404_for_missing_approval() -> None:
    with _isolated_test_client() as (client, _):
        token = _make_token(uuid4())
        resp = client.post(
            f"/api/v1/agents/approvals/{uuid4()}/decision",
            headers={"Authorization": f"Bearer {token}"},
            json={"approved": True},
        )
        assert resp.status_code == 404
        assert resp.headers["content-type"].startswith("application/problem+json")
        assert resp.json()["type"] == "urn:problem:not_found"


def test_voice_websocket_binary_pcm_valid_json_malformed_json_and_single_use() -> None:
    with _isolated_test_client(ticket_ttl_seconds=30) as (client, _):
        user_id = uuid4()
        token = _make_token(user_id)

        ticket_resp = client.post(
            "/api/v1/voice/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ticket_resp.status_code == 200
        ticket = ticket_resp.json()["ticket"]

        with client.websocket_connect(f"/api/v1/voice/stream?ticket={ticket}") as ws:
            ready = ws.receive_json()
            assert ready == {"event": "session_ready", "userId": str(user_id)}

            # Binary 16kHz PCM audio frame
            ws.send_bytes(b"\x01\x02" * 160)
            audio_ack = ws.receive_json()
            assert audio_ack == {"event": "audio_received", "bytes": 320}

            # Valid JSON control envelope
            ws.send_text('{"event": "session_init", "language": "hi"}')
            init_ack = ws.receive_json()
            assert init_ack == {
                "event": "session_acknowledged",
                "userId": str(user_id),
                "language": "hi",
            }

            # Malformed JSON handled gracefully without crashing socket
            ws.send_text("{not-valid-json")
            err = ws.receive_json()
            assert err == {"event": "error", "code": "invalid_json"}

        # Reusing the same ticket must fail
        with (
            pytest.raises(WebSocketDisconnect) as exc_reuse,
            client.websocket_connect(f"/api/v1/voice/stream?ticket={ticket}"),
        ):
            pass
        assert exc_reuse.value.code == 1008


def test_voice_ticket_expiration_rejected() -> None:
    with _isolated_test_client(ticket_ttl_seconds=-1) as (client, _):
        token = _make_token(uuid4())
        ticket_resp = client.post(
            "/api/v1/voice/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ticket_resp.status_code == 200
        expired_ticket = ticket_resp.json()["ticket"]

        with (
            pytest.raises(WebSocketDisconnect) as exc_exp,
            client.websocket_connect(f"/api/v1/voice/stream?ticket={expired_ticket}"),
        ):
            pass
        assert exc_exp.value.code == 1008


@pytest.mark.asyncio
async def test_redis_ticket_store_set_ex_getdel_and_prod_fail_closed() -> None:
    fake_redis = _FakeAsyncRedis()
    store = VoiceTicketStore(ttl_seconds=30, redis_client=fake_redis, environment="production")
    uid = uuid4()

    issued = await store.issue_ticket(uid)
    assert fake_redis.last_ex == 30
    consumed = await store.consume_ticket(issued.ticket)
    assert consumed is not None
    assert consumed.user_id == uid
    # Atomic GETDEL prevents replay
    assert await store.consume_ticket(issued.ticket) is None

    # Production must fail closed on RedisError (no silent memory fallback)
    broken_redis = _FakeAsyncRedis(fail=True)
    prod_store = VoiceTicketStore(
        ttl_seconds=30, redis_client=broken_redis, environment="production"
    )
    with pytest.raises(ProblemDetailError) as exc:
        await prod_store.issue_ticket(uid)
    assert exc.value.status_code == 503
    assert await prod_store.consume_ticket("any-ticket") is None

    # Development allows in-memory fallback when Redis is unreachable
    dev_store = VoiceTicketStore(
        ttl_seconds=30, redis_client=broken_redis, environment="development"
    )
    dev_ticket = await dev_store.issue_ticket(uid)
    assert dev_ticket.user_id == uid
