"""Live Postgres integration tests for WS4/WS5 Research Deduplication, Company Cache & Watchtower."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import DatabaseManager, check_db_health
from app.integrations.crustdata import CrustdataClient
from app.integrations.olostep import OlostepClient
from app.main import create_application

TEST_SECRET = "test-ws4-ws5-jwt-secret-key-at-least-32-chars"
TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _make_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "role": "authenticated",
        },
        TEST_SECRET,
        algorithm="HS256",
    )


@pytest.mark.asyncio
async def test_research_dedup_provenance_company_cache_and_watchtower_live() -> None:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    probe = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(probe):
        await probe.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS4/WS5 integration tests")
    await probe.dispose()

    reset_local_rate_limits()
    olostep_calls = 0
    crust_calls = 0

    def _olostep_transport(request: httpx.Request) -> httpx.Response:
        nonlocal olostep_calls
        olostep_calls += 1
        if request.url.path.endswith("/searches"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "links": [
                            {
                                "title": "Backend Intern at CloudScale",
                                "url": "https://cloudscale.example.com/jobs/backend-intern",
                                "snippet": "Python FastAPI role in Bengaluru",
                            }
                        ]
                    }
                },
            )
        return httpx.Response(200, json={"id": "mon-remote-1"})

    def _crustdata_transport(request: httpx.Request) -> httpx.Response:
        nonlocal crust_calls
        crust_calls += 1
        return httpx.Response(
            200,
            json=[
                {
                    "company_name": "CloudScale AI",
                    "company_website_domain": "cloudscale.example.com",
                    "industry": "Developer Tools",
                    "headcount_range": "201-500",
                    "funding_stage": "Series B",
                }
            ],
        )

    app = create_application(Settings(ENVIRONMENT="development", DATABASE_URL=dsn, REDIS_URL=""))
    app.dependency_overrides[get_jwt_verifier] = lambda: SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    app.state.olostep_client = OlostepClient(
        Settings(OLOSTEP_API_KEY="olo_test_live_db_123456"),
        transport=httpx.MockTransport(_olostep_transport),
    )
    app.state.crustdata_client = CrustdataClient(
        Settings(CRUSTDATA_API_KEY="crust_test_live_db_123456"),
        transport=httpx.MockTransport(_crustdata_transport),
    )

    uid = uuid4()
    other_uid = uuid4()
    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    async with db.session_factory() as sess, sess.begin():
        for u in (uid, other_uid):
            await sess.execute(
                text(
                    "INSERT INTO auth.users (id, email, aud, role, raw_app_meta_data, raw_user_meta_data) "
                    "VALUES (:id, :email, 'authenticated', 'authenticated', '{}'::jsonb, '{}'::jsonb) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": str(u), "email": f"{u}@iitb.ac.in"},
            )

    try:
        headers = {"Authorization": f"Bearer {_make_token(uid)}"}
        other_headers = {"Authorization": f"Bearer {_make_token(other_uid)}"}
        with TestClient(app) as client:
            # 1. Research discover persists novel opportunity + provenance
            r1 = client.post(
                "/api/v1/research/discover",
                headers=headers,
                json={"query": "backend intern bengaluru", "enrichCompanies": True},
            )
            assert r1.status_code == 200, r1.text
            assert r1.json()["discoveredCount"] == 1
            assert r1.json()["deduplicatedCount"] == 0
            assert "cloudscale.example.com" in r1.json()["sourcesRecorded"]

            # 2. Repeat discovery deduplicates cleanly (0 duplicate inserts)
            r2 = client.post(
                "/api/v1/research/discover",
                headers=headers,
                json={"query": "backend intern bengaluru"},
            )
            assert r2.status_code == 200
            assert r2.json()["discoveredCount"] == 0
            assert r2.json()["deduplicatedCount"] == 1

            # 3. SSRF block rejects private metadata URL cleanly
            bad_url = client.post(
                "/api/v1/research/discover",
                headers=headers,
                json={
                    "query": "ssrf probe",
                    "targetUrl": "http://169.254.169.254/latest/meta-data/",
                },
            )
            assert bad_url.status_code == 422

            # 4. Company enrich hits DB 24h cache on second request (no extra Crustdata API hit)
            c1 = client.post(
                "/api/v1/companies/enrich",
                headers=headers,
                json={"domain": "cloudscale.example.com"},
            )
            assert c1.status_code == 200
            calls_after_first = crust_calls
            c2 = client.post(
                "/api/v1/companies/enrich",
                headers=headers,
                json={"domain": "cloudscale.example.com"},
            )
            assert c2.status_code == 200
            assert c2.json()["id"] == c1.json()["id"]
            assert crust_calls == calls_after_first

            # 5. Watchtower monitor creation & cross-user ownership isolation
            m1 = client.post(
                "/api/v1/watchtower/monitors",
                headers=headers,
                json={
                    "targetOrganization": "CloudScale AI",
                    "targetUrl": "https://cloudscale.example.com/careers",
                    "frequency": "daily",
                },
            )
            assert m1.status_code == 201
            mid = m1.json()["id"]
            assert m1.json()["criteria"]["olostepMonitorId"] == "mon-remote-1"
            assert (
                client.delete(
                    f"/api/v1/watchtower/monitors/{mid}", headers=other_headers
                ).status_code
                == 404
            )
            assert (
                client.delete(f"/api/v1/watchtower/monitors/{mid}", headers=headers).status_code
                == 204
            )
    finally:
        async with db.session_factory() as sess, sess.begin():
            await sess.execute(
                text(
                    "DELETE FROM public.opportunities WHERE source_url LIKE 'https://cloudscale.example.com/%'"
                )
            )
            await sess.execute(
                text("DELETE FROM public.organizations WHERE domain = 'cloudscale.example.com'")
            )
            await sess.execute(
                text(
                    "DELETE FROM public.opportunity_sources WHERE domain = 'cloudscale.example.com'"
                )
            )
            await sess.execute(
                text("DELETE FROM auth.users WHERE id IN (:a, :b)"),
                {"a": uid, "b": other_uid},
            )
        await db.dispose()


@pytest.mark.asyncio
async def test_gemini_live_rest_smoke_when_configured() -> None:
    if not settings.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not set")
    import httpx

    from app.integrations.gemini import GeminiClient

    try:
        text_reply = await GeminiClient().generate_text(
            "Reply with the single word: READY",
            temperature=0.0,
        )
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.skip(f"External Gemini endpoint unreachable in offline run: {type(exc).__name__}")
    assert "READY" in text_reply.upper()
