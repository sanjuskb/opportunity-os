"""Live PostgreSQL 17 + pgvector integration tests for WS2 Discover, Live Eligibility, Education & Crons."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import DatabaseManager, check_db_health
from app.main import create_application
from app.models.entities import (
    Opportunity,
    OpportunityEligibility,
    OpportunityEmbedding,
    SavedOpportunity,
)
from app.tasks.embeddings import check_opportunity_deadlines

TEST_SECRET = "test-ws2-phase3-jwt-secret-key-at-least-32"
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
            "email": "student@nitk.edu.in",
        },
        TEST_SECRET,
        algorithm="HS256",
    )


def _hot_vec(idx: int) -> list[float]:
    v = [0.0] * 384
    v[idx] = 1.0
    return v


class _StubQueryAdapter:
    def embed_one(self, _text: str) -> tuple[list[float], str, str]:
        return _hot_vec(7), "sentence-transformers/all-MiniLM-L6-v2", "v1"


@pytest.mark.asyncio
async def test_live_pgvector_discover_eligibility_education_and_deadline_cron() -> None:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    probe = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(probe):
        await probe.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS2 discover/eligibility tests")
    await probe.dispose()

    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", DATABASE_URL=dsn, REDIS_URL=""))
    app.dependency_overrides[get_jwt_verifier] = lambda: SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    app.state.embedding_adapter = _StubQueryAdapter()

    uid = uuid4()
    opp_elig_id = uuid4()
    opp_inelig_id = uuid4()
    db = DatabaseManager(Settings(DATABASE_URL=dsn))

    async with db.session_factory() as session, session.begin():
        await session.execute(
            text(
                "INSERT INTO auth.users (id, email, aud, role, raw_app_meta_data, raw_user_meta_data) "
                "VALUES (:uid, :email, 'authenticated', 'authenticated', '{}'::jsonb, '{}'::jsonb) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"uid": str(uid), "email": f"{uid}@nitk.edu.in"},
        )
        session.add_all(
            [
                Opportunity(
                    id=opp_elig_id,
                    title="Live Vector Backend Intern",
                    organization="VectorLabs",
                    location="Bengaluru",
                    type="internship",
                    description="Python FastAPI backend engineering role.",
                    source_url="https://example.com/v-elig",
                    source_provider="manual",
                    deadline=datetime.now(UTC) + timedelta(hours=24),
                    is_active=True,
                    eligibility=OpportunityEligibility(
                        opportunity_id=opp_elig_id,
                        eligible_batches=[2027],
                        eligible_degrees=["B.Tech"],
                        eligible_branches=["CSE"],
                        min_cgpa=Decimal("7.50"),
                        required_skills=["Python", "FastAPI"],
                        max_active_backlogs=0,
                    ),
                ),
                Opportunity(
                    id=opp_inelig_id,
                    title="High CGPA Only Systems Role",
                    organization="StrictLabs",
                    location="Mumbai",
                    type="internship",
                    description="Backend role requiring 9.6 CGPA.",
                    source_url="https://example.com/v-inelig",
                    source_provider="manual",
                    deadline=datetime.now(UTC) + timedelta(days=5),
                    is_active=True,
                    eligibility=OpportunityEligibility(
                        opportunity_id=opp_inelig_id,
                        eligible_batches=[2027],
                        eligible_degrees=["B.Tech"],
                        min_cgpa=Decimal("9.60"),
                        required_skills=["Python"],
                    ),
                ),
            ]
        )
        await session.flush()
        session.add_all(
            [
                OpportunityEmbedding(
                    opportunity_id=opp_elig_id,
                    embedding_minilm_384=_hot_vec(7),
                    embedding_status="ready",
                    content_hash="h-elig",
                ),
                OpportunityEmbedding(
                    opportunity_id=opp_inelig_id,
                    embedding_minilm_384=_hot_vec(8),
                    embedding_status="ready",
                    content_hash="h-inelig",
                ),
                SavedOpportunity(user_id=uid, opportunity_id=opp_elig_id),
            ]
        )

    try:
        headers = {"Authorization": f"Bearer {_make_token(uid)}"}
        with TestClient(app) as client:
            # 1. Populate student profile & education record
            sp = client.put(
                "/api/v1/users/me/student-profile",
                headers=headers,
                json={
                    "collegeName": "NITK Surathkal",
                    "degree": "B.Tech",
                    "branch": "CSE",
                    "graduationYear": 2027,
                    "cgpa": 8.5,
                    "activeBacklogs": 0,
                    "skills": ["Python"],
                },
            )
            assert sp.status_code == 200

            edu_add = client.post(
                "/api/v1/users/me/education",
                headers=headers,
                json={
                    "institution": "NITK Surathkal",
                    "degree": "B.Tech",
                    "fieldOfStudy": "Computer Science",
                    "startYear": 2023,
                    "endYear": 2027,
                    "score": "8.5 CGPA",
                },
            )
            assert edu_add.status_code == 201
            edu_id = edu_add.json()["id"]
            edu_list = client.get("/api/v1/users/me/education", headers=headers)
            assert edu_list.status_code == 200
            assert any(item["id"] == edu_id for item in edu_list.json())

            # 2. Vector Discover executes pgvector search & ranks eligible opportunity first
            disc = client.post(
                "/api/v1/opportunities/discover",
                headers=headers,
                json={"query": "backend engineering internship", "limit": 10},
            )
            assert disc.status_code == 200
            items = disc.json()["items"]
            found = {i["id"]: i for i in items}
            assert str(opp_elig_id) in found
            assert found[str(opp_elig_id)]["isEligible"] is True
            assert (found[str(opp_elig_id)]["semanticScore"] or 0.0) > 0.99
            assert "FastAPI" in found[str(opp_elig_id)]["missingSkills"]

            # 3. Live Eligibility Evaluate checks DB student + opportunity rules cleanly
            ev_ok = client.post(
                "/api/v1/eligibility/evaluate",
                headers=headers,
                json={"opportunityId": str(opp_elig_id)},
            )
            assert ev_ok.status_code == 200
            assert ev_ok.json()["isEligible"] is True

            ev_bad = client.post(
                "/api/v1/eligibility/evaluate",
                headers=headers,
                json={"opportunityId": str(opp_inelig_id)},
            )
            assert ev_bad.status_code == 200
            assert ev_bad.json()["isEligible"] is False
            assert ev_bad.json()["deterministicChecks"]["cgpaMatched"] is False

            # Delete education cleanly
            assert (
                client.delete(f"/api/v1/users/me/education/{edu_id}", headers=headers).status_code
                == 204
            )

        # 4. ARQ deadline notification task creates idempotent alert cleanly
        cron_res1 = await check_opportunity_deadlines(
            {"session_factory": db.session_factory}, window_hours=72
        )
        assert cron_res1["created"] >= 1
        cron_res2 = await check_opportunity_deadlines(
            {"session_factory": db.session_factory}, window_hours=72
        )
        assert cron_res2["created"] == 0
    finally:
        async with db.session_factory() as conn_sess, conn_sess.begin():
            await conn_sess.execute(
                text("DELETE FROM public.opportunities WHERE id = ANY(:ids)"),
                {"ids": [opp_elig_id, opp_inelig_id]},
            )
            await conn_sess.execute(
                text("DELETE FROM auth.users WHERE id = :uid"),
                {"uid": uid},
            )
        await db.dispose()
