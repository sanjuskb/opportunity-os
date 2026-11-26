"""Live PostgreSQL 17 integration tests for Applications, Approvals, and Notifications."""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import DatabaseManager, check_db_health
from app.main import create_application
from app.schemas.common import ApprovalDecisionRequest
from app.services.approvals import ApprovalService

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
        pytest.skip("Live PostgreSQL instance unavailable for Task 3 integration tests")


@pytest.mark.asyncio
async def test_applications_approvals_notifications_and_concurrency_live() -> None:
    await _ensure_live_db()

    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    app = create_application(
        Settings(
            ENVIRONMENT="development",
            DATABASE_URL=dsn,
            REDIS_URL="",
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
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

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    opp_1 = uuid.uuid4()
    opp_2 = uuid.uuid4()
    session_id = uuid.uuid4()
    approval_1 = uuid.uuid4()
    approval_2 = uuid.uuid4()
    headers_a = {"Authorization": f"Bearer {_make_token(user_a)}"}
    headers_b = {"Authorization": f"Bearer {_make_token(user_b)}"}

    admin_db = DatabaseManager(Settings(DATABASE_URL=dsn))
    try:
        async with admin_db.session_factory() as s, s.begin():
            await s.execute(
                text("INSERT INTO auth.users (id, email) VALUES (:ua, :ea), (:ub, :eb)"),
                {
                    "ua": user_a,
                    "ea": f"task3-a-{user_a.hex[:6]}@example.com",
                    "ub": user_b,
                    "eb": f"task3-b-{user_b.hex[:6]}@example.com",
                },
            )
            for oid, title in ((opp_1, "Task3-Opp-1"), (opp_2, "Task3-Opp-2")):
                await s.execute(
                    text(
                        """
                        INSERT INTO public.opportunities (
                            id, title, organization, location, type, description,
                            source_url, source_provider, is_active
                        ) VALUES (
                            :id, :title, 'TestOrg', 'Remote', 'internship', 'Desc',
                            'https://example.com', 'olostep', true
                        )
                        """
                    ),
                    {"id": oid, "title": title},
                )
            await s.execute(
                text(
                    "INSERT INTO public.agent_sessions (id, user_id, agent_type) VALUES (:sid, :uid, 'application')"
                ),
                {"sid": session_id, "uid": user_a},
            )
            for aid, oid in ((approval_1, opp_1), (approval_2, opp_2)):
                await s.execute(
                    text(
                        """
                        INSERT INTO public.approval_requests (
                            id, session_id, user_id, opportunity_id, action_type, payload_summary
                        ) VALUES (:aid, :sid, :uid, :oid, 'form_submission', '{"field":"resume"}'::jsonb)
                        """
                    ),
                    {"aid": aid, "sid": session_id, "uid": user_a, "oid": oid},
                )

        with TestClient(app) as client:
            # 1. Unauthenticated requests rejected
            for method, path in (
                ("GET", "/api/v1/applications"),
                ("POST", "/api/v1/applications"),
                ("GET", "/api/v1/agents/approvals/pending"),
                ("GET", "/api/v1/notifications"),
            ):
                assert client.request(method, path).status_code == 401

            # 2. Application CRUD, duplicate rejection, and state machine
            create_resp = client.post(
                "/api/v1/applications",
                headers=headers_a,
                json={"opportunityId": str(opp_1), "status": "drafting"},
            )
            assert create_resp.status_code == 201
            app_1_id = create_resp.json()["id"]

            # Duplicate (user_a, opp_1) -> 409 Conflict
            dup_resp = client.post(
                "/api/v1/applications",
                headers=headers_a,
                json={"opportunityId": str(opp_1), "status": "drafting"},
            )
            assert dup_resp.status_code == 409

            # User B cannot read, transition, or delete User A's application
            assert client.get(f"/api/v1/applications/{app_1_id}", headers=headers_b).status_code == 404
            assert (
                client.patch(
                    f"/api/v1/applications/{app_1_id}/status",
                    headers=headers_b,
                    json={"status": "ready_for_review", "expectedStatus": "drafting"},
                ).status_code
                == 404
            )
            assert client.delete(f"/api/v1/applications/{app_1_id}", headers=headers_b).status_code == 404

            # Privileged status bypass attempt -> 403
            assert (
                client.patch(
                    f"/api/v1/applications/{app_1_id}/status",
                    headers=headers_a,
                    json={"status": "submitted", "expectedStatus": "drafting"},
                ).status_code
                == 403
            )
            assert (
                client.patch(
                    f"/api/v1/applications/{app_1_id}/status",
                    headers=headers_a,
                    json={"status": "approved", "expectedStatus": "drafting"},
                ).status_code
                == 403
            )

            # Invalid transition (drafting -> accepted/ineligible) -> 422
            assert (
                client.patch(
                    f"/api/v1/applications/{app_1_id}/status",
                    headers=headers_a,
                    json={"status": "ineligible", "expectedStatus": "drafting"},
                ).status_code
                == 422
            )

            # Valid transition: drafting -> ready_for_review
            ready_resp = client.patch(
                f"/api/v1/applications/{app_1_id}/status",
                headers=headers_a,
                json={"status": "ready_for_review", "expectedStatus": "drafting"},
            )
            assert ready_resp.status_code == 200
            assert ready_resp.json()["status"] == "ready_for_review"

            # Cannot delete non-draft application -> 409
            assert client.delete(f"/api/v1/applications/{app_1_id}", headers=headers_a).status_code == 409

            # 3. Approval pending list, ownership, decision, replay prevention & notifications
            pending_a = client.get("/api/v1/agents/approvals/pending", headers=headers_a)
            assert pending_a.status_code == 200
            assert len(pending_a.json()) == 2
            assert client.get("/api/v1/agents/approvals/pending", headers=headers_b).json() == []

            # User B cannot view or decide User A's approval
            assert (
                client.get(f"/api/v1/agents/approvals/{approval_1}", headers=headers_b).status_code
                == 404
            )
            assert (
                client.post(
                    f"/api/v1/agents/approvals/{approval_1}/decision",
                    headers=headers_b,
                    json={"approved": True},
                ).status_code
                == 404
            )

            # User A approves approval_1 -> transitions linked app_1 to 'approved' & creates 1 notification
            dec_1 = client.post(
                f"/api/v1/agents/approvals/{approval_1}/decision",
                headers=headers_a,
                json={"approved": True},
            )
            assert dec_1.status_code == 200
            assert dec_1.json()["status"] == "approved"

            app_1_after = client.get(f"/api/v1/applications/{app_1_id}", headers=headers_a)
            assert app_1_after.json()["status"] == "approved"

            # Replay attempt on approval_1 -> 409 Conflict
            replay_1 = client.post(
                f"/api/v1/agents/approvals/{approval_1}/decision",
                headers=headers_a,
                json={"approved": False},
            )
            assert replay_1.status_code == 409

            # Notifications: User A has 1 unread notification; User B cannot read or mark it read
            notifs_a = client.get("/api/v1/notifications?unread_only=true", headers=headers_a)
            assert notifs_a.status_code == 200
            assert len(notifs_a.json()) == 1
            notif_id = notifs_a.json()[0]["id"]

            assert client.get("/api/v1/notifications", headers=headers_b).json() == []
            assert (
                client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers_b).status_code
                == 404
            )
            mark_read = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers_a)
            assert mark_read.status_code == 200
            assert mark_read.json()["isRead"] is True

        # 4. Concurrent approval race on approval_2: exactly 1 succeeds, 1 gets 409 Conflict
        async def _race_decide(approved: bool) -> str:
            async with admin_db.session_factory() as s:
                try:
                    await ApprovalService(s).decide_approval(
                        approval_2, user_a, ApprovalDecisionRequest(approved=approved)
                    )
                    return "ok"
                except ProblemDetailError as exc:
                    return f"err:{exc.status_code}"

        results = await asyncio.gather(_race_decide(True), _race_decide(False))
        assert sorted(results) == ["err:409", "ok"]

        # Verify total notifications for user_a == 2 (no duplicate from concurrent race)
        async with admin_db.session_factory() as s:
            notif_count = await s.scalar(
                text("SELECT COUNT(*) FROM public.notifications WHERE user_id = :uid"),
                {"uid": user_a},
            )
            assert notif_count == 2
    finally:
        async with admin_db.session_factory() as s, s.begin():
            await s.execute(
                text("DELETE FROM public.opportunities WHERE id = ANY(:oids)"),
                {"oids": [opp_1, opp_2]},
            )
            await s.execute(
                text("DELETE FROM auth.users WHERE id = ANY(:uids)"),
                {"uids": [user_a, user_b]},
            )
        await admin_db.dispose()
