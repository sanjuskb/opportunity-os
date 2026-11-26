"""Unit, WebSocket, and live smoke tests for WS6: 9-language Gemini REST & Live Voice."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import get_db_session
from app.integrations.gemini import GeminiClient, GeminiLiveRelay
from app.main import create_application

JWT_SECRET = "test-ws6-secret-32-bytes-minimum-len"


def _make_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "role": "authenticated",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        JWT_SECRET,
        algorithm="HS256",
    )


def test_gemini_live_setup_payload_contains_audio_and_tools() -> None:
    relay = GeminiLiveRelay(api_key="dummy-key")
    setup = relay.build_setup_payload(language="mr", enable_tools=True)
    assert setup["setup"]["model"].startswith("models/gemini-2.5-flash")
    assert setup["setup"]["generationConfig"]["responseModalities"] == ["AUDIO"]
    tool_names = [t["name"] for t in setup["setup"]["tools"][0]["functionDeclarations"]]
    assert {"search_opportunities", "check_eligibility", "get_career_passport"}.issubset(
        set(tool_names)
    )


@pytest.mark.asyncio
async def test_gemini_client_function_calling_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    class _FakeHttpClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, params=None, headers=None, json=None):
            nonlocal call_count
            assert "key=" not in str(url)
            assert headers and "x-goog-api-key" in headers
            call_count += 1
            if call_count == 1:
                body = {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "functionCall": {
                                            "name": "search_opportunities",
                                            "args": {"query": "FastAPI"},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            else:
                body = {
                    "candidates": [
                        {"content": {"parts": [{"text": "Found FastAPI Backend Intern role."}]}}
                    ]
                }
            return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "AsyncClient", _FakeHttpClient)
    executed: list[str] = []

    async def _exec(name: str, args: dict):
        executed.append(name)
        return {"opportunities": [{"title": "FastAPI Backend Intern"}]}

    res = await GeminiClient(api_key="test-key").chat_with_tools(
        user_message="मला FastAPI इंटर्नशिप पाहिजे आहे",
        language="mr",
        tool_executor=_exec,
    )
    assert executed == ["search_opportunities"]
    assert res.provider == "gemini"
    assert "FastAPI Backend Intern" in res.reply


def test_ai_chat_and_websocket_text_turn_offline_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_local_rate_limits()
    monkeypatch.setattr(
        "app.api.v1.voice.settings",
        Settings(ENVIRONMENT="development", REDIS_URL="", GEMINI_API_KEY=""),
    )
    monkeypatch.setattr(
        "app.integrations.gemini.settings",
        Settings(ENVIRONMENT="development", REDIS_URL="", GEMINI_API_KEY=""),
    )
    cfg = Settings(
        ENVIRONMENT="development",
        REDIS_URL="",
        SUPABASE_JWT_SECRET=JWT_SECRET,
        SUPABASE_JWT_ISSUER="https://example.supabase.co/auth/v1",
        GEMINI_API_KEY="",
    )
    app = create_application(cfg)
    user_id = uuid4()
    conv_id = uuid4()

    class _ScalarList:
        def all(self):
            return []

    class _Res:
        def __init__(self, obj=None):
            self._obj = obj

        def scalar_one_or_none(self):
            return self._obj

        def scalars(self):
            return _ScalarList()

    class _FakeDb:
        def __init__(self):
            self.added = []

        def add(self, obj):
            if getattr(obj, "id", None) is None:
                obj.id = conv_id if obj.__class__.__name__ == "Conversation" else uuid4()
            self.added.append(obj)

        async def flush(self):
            return None

        async def refresh(self, obj):
            return None

        async def commit(self):
            return None

        async def execute(self, stmt):
            return _Res(None)

    async def _override_db():
        yield _FakeDb()

    app.dependency_overrides[get_db_session] = _override_db
    verifier = SupabaseJWTVerifier(cfg)
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    token = _make_token(user_id)

    with TestClient(app) as client:
        chat_resp = client.post(
            "/api/v1/ai/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Show Python internships", "language": "gu"},
        )
        assert chat_resp.status_code == 200
        body = chat_resp.json()
        assert body["language"] == "gu"
        assert body["conversationId"] == str(conv_id)

        ticket_resp = client.post(
            "/api/v1/voice/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ticket_resp.status_code == 200
        ticket = ticket_resp.json()["ticket"]

        with client.websocket_connect(f"/api/v1/voice/stream?ticket={ticket}") as ws:
            assert ws.receive_json()["event"] == "session_ready"
            ws.send_text('{"event": "session_init", "language": "mr"}')
            ack = ws.receive_json()
            assert ack["language"] == "mr"
            ws.send_text('{"event": "text_turn", "text": "Hello", "language": "mr"}')
            tx = ws.receive_json()
            assert tx["event"] == "ai_transcript"
            assert ws.receive_json()["event"] == "turn_complete"
