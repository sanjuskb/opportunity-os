"""Live PostgreSQL 17 integration tests for W1-C Resume CRUD & ownership isolation."""

from __future__ import annotations

import io
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import jwt
import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import Settings, settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import DatabaseManager, check_db_health
from app.integrations.supabase_storage import ResumeStorageClient
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


@pytest.mark.asyncio
async def test_resume_upload_tailor_pdf_and_storage_rls_live(tmp_path: Path) -> None:
    await _ensure_live_db()
    reset_local_rate_limits()

    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    cfg = Settings(
        ENVIRONMENT="development",
        DATABASE_URL=dsn,
        REDIS_URL="",
        SUPABASE_URL="",
        SUPABASE_SERVICE_ROLE_KEY="",
        LOCAL_RESUME_STORAGE_DIR=str(tmp_path),
    )
    app = create_application(cfg)
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.state.resume_storage = ResumeStorageClient(cfg)

    user_a = uuid4()
    user_b = uuid4()
    opp_id = uuid4()
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
                "INSERT INTO public.opportunities (id, title, organization, location, type, description, source_url, source_provider) "
                "VALUES (:oid, 'Backend API Intern', 'NexteRaS Org', 'Bengaluru', 'internship', "
                "'Python and PostgreSQL backend systems.', 'https://example.com/ws3', 'manual')"
            ),
            {"oid": str(opp_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO public.opportunity_eligibility (opportunity_id, required_skills, eligible_degrees, min_cgpa) "
                "VALUES (:oid, ARRAY['Python', 'PostgreSQL', 'Docker'], ARRAY['B.Tech'], 7.5)"
            ),
            {"oid": str(opp_id)},
        )

    try:
        # 1. Verify storage.objects RLS enforces strict auth.uid() isolation in live Postgres
        async with db.engine.begin() as conn:
            await conn.execute(text("SET LOCAL ROLE authenticated"))
            await conn.execute(
                text("SELECT set_config('request.jwt.claim.sub', :uid, true)"),
                {"uid": str(user_a)},
            )
            await conn.execute(
                text(
                    "INSERT INTO storage.objects (bucket_id, name, owner) "
                    "VALUES ('resumes', :path, CAST(:uid AS uuid))"
                ),
                {"path": f"{user_a}/r1/cv.pdf", "uid": str(user_a)},
            )
            await conn.execute(
                text("SELECT set_config('request.jwt.claim.sub', :uid, true)"),
                {"uid": str(user_b)},
            )
            other_count = (
                await conn.execute(
                    text("SELECT COUNT(*) FROM storage.objects WHERE bucket_id = 'resumes'")
                )
            ).scalar_one()
            assert other_count == 0
            await conn.execute(text("RESET ROLE"))

        # 2. HTTP Upload DOCX -> Analyze -> Grounded Tailor -> Export ATS PDF
        docx = Document()
        docx.add_paragraph("Riya Verma")
        docx.add_paragraph("IIIT Hyderabad | B.Tech CSE | Batch 2027 | CGPA: 8.7/10")
        docx.add_paragraph("Technical Skills: Python, PostgreSQL, FastAPI")
        docx.add_paragraph(
            "Projects: Built Campus Attendance API using FastAPI and PostgreSQL for 100 students."
        )
        buf = io.BytesIO()
        docx.save(buf)

        with TestClient(app) as client:
            headers_a = {"Authorization": f"Bearer {_make_token(user_a)}"}
            headers_b = {"Authorization": f"Bearer {_make_token(user_b)}"}

            up = client.post(
                "/api/v1/resumes/upload",
                headers=headers_a,
                files={
                    "file": (
                        "riya_cv.docx",
                        buf.getvalue(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                data={"title": "Riya Master CV", "sync_to_profile": "true"},
            )
            assert up.status_code == 201, up.text
            resume = up.json()
            rid = resume["id"]
            assert resume["storageBucket"] == "resumes"
            assert (
                resume["mimeType"]
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            # Spoofed PDF must be rejected with 422
            bad_up = client.post(
                "/api/v1/resumes/upload",
                headers=headers_a,
                files={"file": ("bad.pdf", b"not a pdf", "application/pdf")},
            )
            assert bad_up.status_code == 422

            # Analyze against target opportunity detects Docker gap
            an = client.post(
                f"/api/v1/resumes/{rid}/analyze",
                headers=headers_a,
                json={"opportunityId": str(opp_id)},
            )
            assert an.status_code == 200
            assert "Docker" in an.json()["missingSkills"]

            # Tailor must verify grounded claim and reject fabricated numeric claim
            tl = client.post(
                f"/api/v1/resumes/{rid}/tailor",
                headers=headers_a,
                json={
                    "opportunityId": str(opp_id),
                    "candidateClaims": [
                        "Built Campus Attendance API using FastAPI and PostgreSQL for 100 students.",
                        "Managed 50000 GPU cluster at SpaceX for 9 years.",
                    ],
                },
            )
            assert tl.status_code == 200, tl.text
            tl_body = tl.json()
            assert tl_body["versionNumber"] == 2
            assert len(tl_body["verifiedClaims"]) >= 1
            assert len(tl_body["rejectedClaims"]) >= 1

            # Export valid %PDF- bytes & verify cross-user B cannot read A's PDF
            pdf_resp = client.get(f"/api/v1/resumes/{rid}/pdf", headers=headers_a)
            assert pdf_resp.status_code == 200
            assert pdf_resp.headers["content-type"].startswith("application/pdf")
            assert pdf_resp.content.startswith(b"%PDF-")
            doc = pymupdf.open(stream=pdf_resp.content, filetype="pdf")
            extracted = "\n".join(p.get_text("text") for p in doc)
            doc.close()
            assert "TAILORED" in extracted.upper() or "RIYA" in extracted.upper()

            assert client.get(f"/api/v1/resumes/{rid}/pdf", headers=headers_b).status_code == 404
    finally:
        async with db.engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM public.opportunities WHERE id = :oid"),
                {"oid": str(opp_id)},
            )
            await conn.execute(
                text("DELETE FROM auth.users WHERE id IN (:a, :b)"),
                {"a": str(user_a), "b": str(user_b)},
            )
        await db.dispose()
