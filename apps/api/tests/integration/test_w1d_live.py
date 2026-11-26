"""Live PostgreSQL 17 integration tests for W1-D: Voice Sessions, Saved Opportunities, Concurrency."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import DatabaseManager, check_db_health
from app.main import create_application
from app.schemas.common import ApplicationStatusUpdateRequest
from app.services.applications import ApplicationService

TEST_SECRET = "test-super-secret-supabase-jwt-key-32-chars"
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
            "email": "student@iitb.ac.in",
        },
        TEST_SECRET,
        algorithm="HS256",
    )


async def _ensure_live_db() -> None:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    ok = await check_db_health(db)
    await db.dispose()
    if not ok:
        pytest.skip("Live PostgreSQL instance unavailable for W1-D integration tests")


@pytest.mark.asyncio
async def test_w1d_voice_saved_opportunities_and_concurrency_live() -> None:
    await _ensure_live_db()

    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    app = create_application(
        Settings(
            ENVIRONMENT="development",
            DATABASE_URL=dsn,
            REDIS_URL="",
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier

    user_a = uuid4()
    user_b = uuid4()
    opp_active = uuid4()
    opp_inactive = uuid4()
    db = DatabaseManager(Settings(DATABASE_URL=dsn))

    async with db.engine.begin() as conn:
        for uid, email in [(user_a, f"{user_a}@iitb.ac.in"), (user_b, f"{user_b}@iitb.ac.in")]:
            await conn.execute(
                text(
                    "INSERT INTO auth.users (id, email, aud, role, raw_app_meta_data, raw_user_meta_data) "
                    "VALUES (:id, :email, 'authenticated', 'authenticated', '{}'::jsonb, '{}'::jsonb) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": str(uid), "email": email},
            )
            await conn.execute(
                text(
                    "INSERT INTO public.profiles (id, email, full_name) "
                    "VALUES (:id, :email, 'Test Student') ON CONFLICT (id) DO NOTHING"
                ),
                {"id": str(uid), "email": email},
            )
        await conn.execute(
            text(
                "INSERT INTO public.opportunities "
                "(id, title, organization, location, type, description, source_url, source_provider, is_active) "
                "VALUES (:id, 'Active Opp', 'Org', 'Remote', 'internship', 'Desc', "
                "'https://example.com/a', 'manual', true)"
            ),
            {"id": str(opp_active)},
        )
        await conn.execute(
            text(
                "INSERT INTO public.opportunities "
                "(id, title, organization, location, type, description, source_url, source_provider, is_active) "
                "VALUES (:id, 'Inactive Opp', 'Org', 'Remote', 'internship', 'Desc', "
                "'https://example.com/b', 'manual', false)"
            ),
            {"id": str(opp_inactive)},
        )

    try:
        with TestClient(app) as client:
            token_a = _make_token(user_a)
            token_b = _make_token(user_b)

            # 1. Voice session persistence
            vs_resp = client.post(
                "/api/v1/voice/sessions",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"detectedLanguage": "hi", "audioDurationSeconds": "5.25"},
            )
            assert vs_resp.status_code == 201
            assert vs_resp.json()["userId"] == str(user_a)

            # 2. Saved opportunities isolation & inactive exclusion
            assert (
                client.post(
                    f"/api/v1/opportunities/{opp_active}/save",
                    headers={"Authorization": f"Bearer {token_a}"},
                    json={"saved": True},
                ).status_code
                == 200
            )
            assert (
                client.post(
                    f"/api/v1/opportunities/{opp_inactive}/save",
                    headers={"Authorization": f"Bearer {token_a}"},
                    json={"saved": True},
                ).status_code
                == 200
            )
            saved_a = client.get(
                "/api/v1/opportunities/saved",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert saved_a.status_code == 200
            assert [o["id"] for o in saved_a.json()] == [str(opp_active)]

            saved_b = client.get(
                "/api/v1/opportunities/saved",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert saved_b.status_code == 200
            assert saved_b.json() == []

            # 3. Concurrent application status transitions in real PostgreSQL
            app_resp = client.post(
                "/api/v1/applications",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"opportunityId": str(opp_active), "status": "drafting"},
            )
            assert app_resp.status_code == 201
            app_id = UUID(app_resp.json()["id"])

            async with db.session_factory() as s1, db.session_factory() as s2:
                results = await asyncio.gather(
                    ApplicationService(s1).update_status_by_client(
                        app_id,
                        user_a,
                        ApplicationStatusUpdateRequest(
                            status="ready_for_review", expected_status="drafting"
                        ),
                    ),
                    ApplicationService(s2).update_status_by_client(
                        app_id,
                        user_a,
                        ApplicationStatusUpdateRequest(
                            status="saved", expected_status="drafting"
                        ),
                    ),
                    return_exceptions=True,
                )
            assert sum(1 for r in results if not isinstance(r, Exception)) == 1
            assert (
                sum(
                    1
                    for r in results
                    if isinstance(r, ProblemDetailError) and r.status_code == 409
                )
                == 1
            )

            # 4. Approval transaction integrity in real PostgreSQL
            from app.schemas.common import ApprovalDecisionRequest
            from app.services.approvals import ApprovalService

            agent_session_id = uuid4()
            approval_id = uuid4()
            async with db.engine.begin() as conn:
                await conn.execute(
                    text(
                        "INSERT INTO public.agent_sessions (id, user_id, agent_type) "
                        "VALUES (:id, :uid, 'application_submission')"
                    ),
                    {"id": str(agent_session_id), "uid": str(user_a)},
                )
                await conn.execute(
                    text(
                        "INSERT INTO public.approval_requests "
                        "(id, session_id, user_id, opportunity_id, action_type, payload_summary, status) "
                        "VALUES (:id, :sid, :uid, :oid, 'submit_application', '{}'::jsonb, 'pending')"
                    ),
                    {
                        "id": str(approval_id),
                        "sid": str(agent_session_id),
                        "uid": str(user_a),
                        "oid": str(opp_active),
                    },
                )
                await conn.execute(
                    text("UPDATE public.applications SET status = 'ready_for_review' WHERE id = :id"),
                    {"id": str(app_id)},
                )

            async with db.session_factory() as s_app:
                decision_resp = await ApprovalService(s_app).decide_approval(
                    approval_id, user_a, ApprovalDecisionRequest(approved=True)
                )
                assert decision_resp.status == "approved"
    finally:
        async with db.engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.users WHERE id IN (:a, :b)"),
                {"a": str(user_a), "b": str(user_b)},
            )
            await conn.execute(
                text("DELETE FROM public.opportunities WHERE id IN (:a, :b)"),
                {"a": str(opp_active), "b": str(opp_inactive)},
            )
        await db.dispose()
