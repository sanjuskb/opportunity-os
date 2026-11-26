"""Live PostgreSQL 17 integration tests for W1-C Resume CRUD & ownership isolation."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

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
        pytest.skip("Live PostgreSQL instance unavailable for Resume integration tests")


@pytest.mark.asyncio
async def test_resume_crud_and_ownership_isolation_live() -> None:
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

    try:
        with TestClient(app) as client:
            token_a = _make_token(user_a)
            token_b = _make_token(user_b)

            create_resp = client.post(
                "/api/v1/resumes",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"title": "Live Test Resume", "masterContent": {"skills": ["Python"]}},
            )
            assert create_resp.status_code == 201
            resume_id = create_resp.json()["id"]

            list_a = client.get("/api/v1/resumes", headers={"Authorization": f"Bearer {token_a}"})
            assert list_a.status_code == 200
            assert any(item["id"] == resume_id for item in list_a.json())

            list_b = client.get("/api/v1/resumes", headers={"Authorization": f"Bearer {token_b}"})
            assert list_b.status_code == 200
            assert all(item["id"] != resume_id for item in list_b.json())

            assert (
                client.get(
                    f"/api/v1/resumes/{resume_id}",
                    headers={"Authorization": f"Bearer {token_b}"},
                ).status_code
                == 404
            )
            assert (
                client.delete(
                    f"/api/v1/resumes/{resume_id}",
                    headers={"Authorization": f"Bearer {token_b}"},
                ).status_code
                == 404
            )

            del_a = client.delete(
                f"/api/v1/resumes/{resume_id}",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert del_a.status_code == 204
            assert (
                client.get(
                    f"/api/v1/resumes/{resume_id}",
                    headers={"Authorization": f"Bearer {token_a}"},
                ).status_code
                == 404
            )
    finally:
        async with db.engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.users WHERE id IN (:a, :b)"),
                {"a": str(user_a), "b": str(user_b)},
            )
        await db.dispose()
