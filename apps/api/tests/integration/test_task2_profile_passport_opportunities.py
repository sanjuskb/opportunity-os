"""Live PostgreSQL 17 integration tests for Profile, Career Passport, and Opportunity APIs."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import DatabaseManager, check_db_health
from app.main import create_application

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
        pytest.skip("Live PostgreSQL instance unavailable for Task 2 API integration tests")


@pytest.mark.asyncio
async def test_profile_passport_and_opportunity_apis_live() -> None:
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
    opp_ids = [uuid.uuid4() for _ in range(3)]
    headers_a = {"Authorization": f"Bearer {_make_token(user_a)}"}
    headers_b = {"Authorization": f"Bearer {_make_token(user_b)}"}

    admin_db = DatabaseManager(Settings(DATABASE_URL=dsn))
    try:
        async with admin_db.session_factory() as s, s.begin():
            await s.execute(
                text("INSERT INTO auth.users (id, email) VALUES (:ua, :ea), (:ub, :eb)"),
                {
                    "ua": user_a,
                    "ea": f"task2-a-{user_a.hex[:6]}@example.com",
                    "ub": user_b,
                    "eb": f"task2-b-{user_b.hex[:6]}@example.com",
                },
            )
            base_ts = datetime.now(UTC)
            for idx, oid in enumerate(opp_ids):
                await s.execute(
                    text(
                        """
                        INSERT INTO public.opportunities (
                            id, title, organization, location, type, description,
                            source_url, source_provider, is_active, created_at
                        ) VALUES (
                            :id, :title, 'TestLab', 'Bengaluru', 'internship', 'FastAPI role',
                            'https://example.com', 'olostep', true, :ts
                        )
                        """
                    ),
                    {
                        "id": oid,
                        "title": f"Task2-Searchable-Intern-{idx}",
                        "ts": base_ts + timedelta(seconds=idx),
                    },
                )

        with TestClient(app) as client:
            # 1. Unauthenticated access rejected on private endpoints
            for method, path in (
                ("GET", "/api/v1/users/me"),
                ("PUT", "/api/v1/users/me"),
                ("GET", "/api/v1/users/me/student-profile"),
                ("GET", "/api/v1/career-passport"),
                ("POST", f"/api/v1/opportunities/{opp_ids[0]}/save"),
            ):
                assert client.request(method, path).status_code == 401

            # 2. Missing profile returns 404
            missing_headers = {"Authorization": f"Bearer {_make_token(uuid.uuid4())}"}
            assert client.get("/api/v1/users/me", headers=missing_headers).status_code == 404

            # 3. Profile retrieval & update (rejecting email tampering)
            me_resp = client.get("/api/v1/users/me", headers=headers_a)
            assert me_resp.status_code == 200
            assert me_resp.json()["userId"] == str(user_a)

            upd_resp = client.put(
                "/api/v1/users/me",
                headers=headers_a,
                json={"fullName": "Sanjeeth Updated", "preferredLanguage": "te"},
            )
            assert upd_resp.status_code == 200
            assert upd_resp.json()["fullName"] == "Sanjeeth Updated"
            assert upd_resp.json()["preferredLanguage"] == "te"

            # Attempt to tamper email -> 422
            assert (
                client.put(
                    "/api/v1/users/me",
                    headers=headers_a,
                    json={"email": "hacker@example.com"},
                ).status_code
                == 422
            )

            # 4. Student profile CRUD & validation
            assert (
                client.get("/api/v1/users/me/student-profile", headers=headers_a).status_code == 404
            )
            sp_resp = client.put(
                "/api/v1/users/me/student-profile",
                headers=headers_a,
                json={
                    "collegeName": "IIT Madras",
                    "degree": "B.Tech",
                    "branch": "CSE",
                    "graduationYear": 2027,
                    "cgpa": 9.1,
                    "state": "Tamil Nadu",
                },
            )
            assert sp_resp.status_code == 200
            assert sp_resp.json()["userId"] == str(user_a)
            assert sp_resp.json()["collegeName"] == "IIT Madras"

            # Invalid CGPA (> 10.0) -> 422
            assert (
                client.put(
                    "/api/v1/users/me/student-profile",
                    headers=headers_a,
                    json={
                        "collegeName": "IIT Madras",
                        "degree": "B.Tech",
                        "branch": "CSE",
                        "graduationYear": 2027,
                        "cgpa": 12.5,
                    },
                ).status_code
                == 422
            )

            # 5. Career Passport & cross-user isolation
            cp_add = client.post(
                "/api/v1/career-passport/items",
                headers=headers_a,
                json={"category": "projects", "data": {"title": "Opportunity OS"}},
            )
            assert cp_add.status_code == 200
            item_id = cp_add.json()["projects"][0]["id"]

            # User B cannot access or delete User A's Career Passport item
            assert client.get("/api/v1/career-passport", headers=headers_b).status_code == 404
            assert (
                client.delete(
                    f"/api/v1/career-passport/items/{item_id}", headers=headers_b
                ).status_code
                == 404
            )

            cp_del = client.delete(f"/api/v1/career-passport/items/{item_id}", headers=headers_a)
            assert cp_del.status_code == 200
            assert cp_del.json()["projects"] == []

            # 6. Public Opportunity pagination, filters, detail, discover & save
            p1 = client.get("/api/v1/opportunities?limit=2&type=internship&q=Task2-Searchable")
            assert p1.status_code == 200
            p1_data = p1.json()
            assert len(p1_data["items"]) == 2
            assert p1_data["hasMore"] is True

            p2 = client.get(
                f"/api/v1/opportunities?limit=2&type=internship&q=Task2-Searchable&cursor={p1_data['nextCursor']}"
            )
            assert p2.status_code == 200
            assert len(p2.json()["items"]) == 1
            assert p2.json()["hasMore"] is False

            detail = client.get(f"/api/v1/opportunities/{opp_ids[0]}")
            assert detail.status_code == 200
            assert detail.json()["id"] == str(opp_ids[0])
            assert client.get(f"/api/v1/opportunities/{uuid.uuid4()}").status_code == 404

            disc = client.post(
                "/api/v1/opportunities/discover",
                headers=headers_a,
                json={"query": "Task2-Searchable", "type": "internship", "limit": 5},
            )
            assert disc.status_code == 200
            assert len(disc.json()["items"]) == 3

            save_a = client.post(
                f"/api/v1/opportunities/{opp_ids[0]}/save",
                headers=headers_a,
                json={"saved": True, "notes": "Apply soon"},
            )
            assert save_a.status_code == 200
            assert save_a.json()["saved"] is True

            unsave_a = client.post(
                f"/api/v1/opportunities/{opp_ids[0]}/save",
                headers=headers_a,
                json={"saved": False},
            )
            assert unsave_a.status_code == 200
            assert unsave_a.json()["saved"] is False
    finally:
        # Clean up test users and test opportunities
        async with admin_db.session_factory() as s, s.begin():
            await s.execute(
                text("DELETE FROM public.opportunities WHERE id = ANY(:oids)"),
                {"oids": opp_ids},
            )
            await s.execute(
                text("DELETE FROM auth.users WHERE id = ANY(:uids)"),
                {"uids": [user_a, user_b]},
            )
        await admin_db.dispose()
