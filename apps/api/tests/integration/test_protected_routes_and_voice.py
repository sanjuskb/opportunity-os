"""Integration tests for protected FastAPI routes, RFC 7807 errors, Redis tickets & Voice WS."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
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


def _build_test_client(ticket_ttl_seconds: int = 30) -> tuple[TestClient, VoiceTicketStore]:
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    ticket_store = VoiceTicketStore(ttl_seconds=ticket_ttl_seconds, environment="development")
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_voice_ticket_store] = lambda: ticket_store
    return TestClient(app), ticket_store


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
    client, _ = _build_test_client()
    with client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/opportunities").status_code == 200


def test_protected_endpoint_without_authorization_returns_401_rfc7807() -> None:
    client, _ = _build_test_client()
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
    client, _ = _build_test_client()
    token = _make_token(uuid4(), role="anon")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/users/me", headers=headers).status_code == 403
    assert (
        client.post("/api/v1/opportunities/discover", headers=headers, json={"query": "python"})
        .status_code
        == 403
    )
    assert client.post("/api/v1/voice/tickets", headers=headers).status_code == 403


def test_user_identity_derived_from_jwt_ignoring_client_user_id() -> None:
    client, _ = _build_test_client()
    real_user = uuid4()
    spoofed_user = uuid4()
    opp_id = uuid4()
    token = _make_token(real_user)

    resp = client.post(
        "/api/v1/eligibility/evaluate",
        headers={"Authorization": f"Bearer {token}"},
        json={"opportunityId": str(opp_id), "studentId": str(spoofed_user)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["studentId"] == str(real_user)
    assert data["studentId"] != str(spoofed_user)


def test_approval_endpoint_returns_404_for_missing_approval() -> None:
    client, _ = _build_test_client()
    token = _make_token(uuid4())

    with client:
        resp = client.post(
            f"/api/v1/agents/approvals/{uuid4()}/decision",
            headers={"Authorization": f"Bearer {token}"},
            json={"approved": True},
        )
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["type"] == "urn:problem:not_found"


def test_voice_websocket_binary_pcm_valid_json_malformed_json_and_single_use() -> None:
    client, _ = _build_test_client(ticket_ttl_seconds=30)
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
    with pytest.raises(WebSocketDisconnect) as exc_reuse, client.websocket_connect(
        f"/api/v1/voice/stream?ticket={ticket}"
    ):
        pass
    assert exc_reuse.value.code == 1008


def test_voice_ticket_expiration_rejected() -> None:
    client, _ = _build_test_client(ticket_ttl_seconds=-1)
    token = _make_token(uuid4())
    ticket_resp = client.post(
        "/api/v1/voice/tickets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ticket_resp.status_code == 200
    expired_ticket = ticket_resp.json()["ticket"]

    with pytest.raises(WebSocketDisconnect) as exc_exp, client.websocket_connect(
        f"/api/v1/voice/stream?ticket={expired_ticket}"
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
