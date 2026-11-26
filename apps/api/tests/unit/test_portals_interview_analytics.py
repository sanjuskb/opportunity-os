"""Unit tests for Role Portals (Company/University RBAC), Interview Simulator & Analytics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import jwt
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import get_db_session
from app.main import create_application

JWT_SECRET = "test-portals-secret-32-bytes-minimum"


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


def test_role_based_portal_enforcement_interview_and_analytics(monkeypatch) -> None:
    reset_local_rate_limits()
    monkeypatch.setattr(
        "app.api.v1.portals.GeminiClient",
        lambda: SimpleNamespace(configured=False),
    )
    cfg = Settings(
        ENVIRONMENT="development",
        REDIS_URL="",
        SUPABASE_JWT_SECRET=JWT_SECRET,
        SUPABASE_JWT_ISSUER="https://example.supabase.co/auth/v1",
    )
    app = create_application(cfg)
    user_id = uuid4()
    session_id = uuid4()
    profile_obj = SimpleNamespace(id=user_id, email="stu@iitb.ac.in", user_role="student")
    interview_obj: dict[str, object] = {}

    class _Scalars:
        def all(self):
            return []

    class _Res:
        def __init__(self, obj=None, count=0):
            self._obj = obj
            self._count = count

        def scalar_one_or_none(self):
            return self._obj

        def scalar(self):
            return self._count

        def scalars(self):
            return _Scalars()

        def all(self):
            return []

    class _FakeDb:
        async def execute(self, stmt):
            text_sql = str(stmt)
            if "FROM public.profiles" in text_sql:
                return _Res(profile_obj)
            if "FROM public.interview_sessions" in text_sql:
                return _Res(interview_obj.get("row"))
            return _Res(None, count=0)

        def add(self, obj):
            if getattr(obj, "id", None) is None:
                obj.id = session_id
            if obj.__class__.__name__ == "InterviewSession":
                interview_obj["row"] = obj

        async def commit(self):
            return None

        async def refresh(self, obj):
            return None

    async def _override_db():
        yield _FakeDb()

    verifier = SupabaseJWTVerifier(cfg)
    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    token = _make_token(user_id)

    with TestClient(app) as client:
        # 1. Student user MUST get 403 Forbidden on Company & University endpoints
        assert (
            client.get(
                "/api/v1/company/candidates",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 403
        )
        assert (
            client.get(
                "/api/v1/university/overview",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 403
        )

        # 2. Switch workspace role to 'company' -> allowed on company portal
        profile_obj.user_role = "company"
        assert (
            client.get(
                "/api/v1/company/applicants",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 200
        )

        # 3. Create & respond to interview session cleanly
        create_resp = client.post(
            "/api/v1/interview/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"targetRole": "Backend Engineering Intern", "language": "mr"},
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert len(created["questions"]) == 3

        respond_resp = client.post(
            f"/api/v1/interview/sessions/{created['id']}/respond",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "questionIndex": 0,
                "answerText": "We decompose microservices and add PostgreSQL indexing, Redis caching, and failure metrics.",
            },
        )
        assert respond_resp.status_code == 200
        assert respond_resp.json()["overallScore"] >= 45

        # 4. Analytics overview returns valid structure
        ana_resp = client.get(
            "/api/v1/analytics/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ana_resp.status_code == 200
        assert "totalOpportunities" in ana_resp.json()
