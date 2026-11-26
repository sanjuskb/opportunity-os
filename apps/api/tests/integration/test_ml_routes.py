"""FastAPI ML & Eligibility HTTP route tests (runs cleanly in both slim API CI and full-stack ML env)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

import app.api.v1.ml as ml_routes
from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.main import create_application

TEST_SECRET = "test-ml-routes-jwt-secret-key-at-least-32-chars"
TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _auth_headers() -> dict[str, str]:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
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
    return {"Authorization": f"Bearer {token}"}


def _configure_test_auth(app: Any) -> None:
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    app.dependency_overrides[get_jwt_verifier] = lambda: verifier


class _StubResult:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return self._payload


class _StubMatcher:
    model_identifier = "stub-minilm"
    using_finetuned_checkpoint = False


class _StubMLService:
    semantic_matcher = _StubMatcher()

    def health_and_readiness(self) -> _StubResult:
        return _StubResult(
            {
                "status": "healthy",
                "readiness": "ready_lazy",
                "device": "cpu",
                "cuda_available": False,
                "loaded_models": [],
                "registry_count": 6,
                "details": {"semantic_model_active": "stub-minilm"},
            }
        )

    def extract_resume(self, resume_text: str) -> _StubResult:
        return _StubResult(
            {
                "profile": {"full_name": "Kiran Rao", "graduation_year": 2026},
                "normalized_skills": ["Python", "FastAPI"],
                "extraction_mode": "deterministic_rules",
                "validation_status": "valid",
                "confidence": 0.9,
                "warnings": [],
            }
        )


def test_ml_routes_reject_unauthenticated_requests() -> None:
    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    client = TestClient(app)

    assert client.get("/api/v1/ml/health").status_code == 401
    assert (
        client.post("/api/v1/ml/extract-resume", json={"resume_text": "B.Tech CSE"}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/ml/eligibility/evaluate",
            json={"student": {"student_id": "s1"}, "opportunity": {"opportunity_id": "o1"}},
        ).status_code
        == 401
    )


def test_ml_health_reports_slim_api_mode_when_ml_absent(monkeypatch: Any) -> None:
    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    _configure_test_auth(app)
    monkeypatch.setattr(ml_routes, "is_ml_subsystem_available", lambda: False)
    client = TestClient(app)
    headers = _auth_headers()

    health = client.get("/api/v1/ml/health", headers=headers)
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "degraded_api_only"
    assert body["ml_available"] is False

    # Protected route returns RFC 7807 503 Problem Details cleanly when ML runtime is absent
    def _unavail() -> Any:
        raise ml_routes.MLSubsystemUnavailableError("Slim API container")

    monkeypatch.setattr(ml_routes, "get_ml_service", _unavail)
    resp = client.post(
        "/api/v1/ml/extract-resume",
        json={"resume_text": "B.Tech CSE Python"},
        headers=headers,
    )
    assert resp.status_code == 503
    assert resp.json()["detail"]["status"] == 503


def test_ml_routes_work_with_injected_service() -> None:
    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    _configure_test_auth(app)
    app.state.ml_service = _StubMLService()
    client = TestClient(app)
    headers = _auth_headers()

    h = client.get("/api/v1/ml/health", headers=headers)
    assert h.status_code == 200
    assert h.json()["ml_available"] is True

    ex = client.post(
        "/api/v1/ml/extract-resume",
        json={"resume_text": "Kiran Rao B.Tech CSE 2026 Python FastAPI"},
        headers=headers,
    )
    assert ex.status_code == 200
    assert "Python" in ex.json()["normalized_skills"]


def test_real_ml_endpoints_if_installed_in_environment() -> None:
    if not ml_routes.is_ml_subsystem_available():
        return
    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    _configure_test_auth(app)
    client = TestClient(app)
    headers = _auth_headers()

    res = client.post(
        "/api/v1/ml/eligibility/evaluate",
        headers=headers,
        json={
            "student": {
                "student_id": "s-api-1",
                "degree": "B.E.",
                "branch": "CSE",
                "graduation_year": 2026,
                "cgpa": 8.4,
                "preferred_locations": ["Bengaluru"],
                "skills": ["Python", "FastAPI"],
            },
            "opportunity": {
                "opportunity_id": "opp-api-1",
                "title": "Backend Intern",
                "eligible_degrees": ["B.Tech"],
                "eligible_branches": ["Computer Science & Engineering"],
                "eligible_graduation_years": [2026],
                "min_cgpa": 7.5,
                "allowed_locations": ["Bangalore"],
                "required_skills": ["Python"],
                "deadline": "2026-12-30",
            },
            "semantic_similarity": 0.85,
            "reference_date": date(2026, 11, 25).isoformat(),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["is_eligible"] is True
    assert payload["score"] > 0
