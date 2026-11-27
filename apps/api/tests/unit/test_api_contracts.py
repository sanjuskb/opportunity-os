"""Automated contract verification between @opportunity-os/api-client and FastAPI routes."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security_middleware import reset_local_rate_limits
from app.main import create_application

REPO_ROOT = Path(__file__).resolve().parents[4]
API_CLIENT_SRC = REPO_ROOT / "packages" / "api-client" / "src" / "index.ts"

# Canonical (HTTP method, FastAPI path) pairs expected from packages/api-client
SDK_ENDPOINTS = [
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/users/me"),
    ("PUT", "/api/v1/users/me"),
    ("GET", "/api/v1/users/me/student-profile"),
    ("PUT", "/api/v1/users/me/student-profile"),
    ("GET", "/api/v1/users/me/education"),
    ("POST", "/api/v1/users/me/education"),
    ("DELETE", "/api/v1/users/me/education/{education_id}"),
    ("GET", "/api/v1/career-passport"),
    ("POST", "/api/v1/career-passport/items"),
    ("DELETE", "/api/v1/career-passport/items/{item_id}"),
    ("GET", "/api/v1/opportunities"),
    ("GET", "/api/v1/opportunities/{opportunity_id}"),
    ("POST", "/api/v1/opportunities/discover"),
    ("GET", "/api/v1/opportunities/saved"),
    ("POST", "/api/v1/opportunities/{opportunity_id}/save"),
    ("POST", "/api/v1/eligibility/evaluate"),
    ("GET", "/api/v1/applications"),
    ("POST", "/api/v1/applications"),
    ("GET", "/api/v1/applications/{application_id}"),
    ("PATCH", "/api/v1/applications/{application_id}/status"),
    ("DELETE", "/api/v1/applications/{application_id}"),
    ("GET", "/api/v1/agents/approvals/pending"),
    ("GET", "/api/v1/agents/approvals/{approval_id}"),
    ("POST", "/api/v1/agents/approvals/{approval_id}/decision"),
    ("GET", "/api/v1/notifications"),
    ("PATCH", "/api/v1/notifications/{notification_id}/read"),
    ("GET", "/api/v1/resumes"),
    ("POST", "/api/v1/resumes"),
    ("POST", "/api/v1/resumes/upload"),
    ("GET", "/api/v1/resumes/{resume_id}"),
    ("GET", "/api/v1/resumes/{resume_id}/download-url"),
    ("GET", "/api/v1/resumes/{resume_id}/versions"),
    ("POST", "/api/v1/resumes/{resume_id}/analyze"),
    ("POST", "/api/v1/resumes/{resume_id}/tailor"),
    ("GET", "/api/v1/resumes/{resume_id}/pdf"),
    ("DELETE", "/api/v1/resumes/{resume_id}"),
    ("POST", "/api/v1/research/discover"),
    ("POST", "/api/v1/companies/enrich"),
    ("GET", "/api/v1/companies"),
    ("GET", "/api/v1/companies/{org_id}"),
    ("GET", "/api/v1/watchtower/monitors"),
    ("POST", "/api/v1/watchtower/monitors"),
    ("DELETE", "/api/v1/watchtower/monitors/{monitor_id}"),
    ("POST", "/api/v1/voice/tickets"),
    ("GET", "/api/v1/voice/sessions"),
    ("POST", "/api/v1/voice/sessions"),
    ("POST", "/api/v1/ai/chat"),
    ("GET", "/api/v1/conversations"),
    ("GET", "/api/v1/conversations/{conversation_id}"),
    ("POST", "/api/v1/applications/{application_id}/prepare-automation"),
    ("POST", "/api/v1/applications/{application_id}/execute-approved"),
    ("GET", "/api/v1/browser-logs"),
    ("GET", "/api/v1/agents/sessions"),
    ("GET", "/api/v1/agents/sessions/{session_id}/events"),
    ("POST", "/api/v1/jobs"),
    ("GET", "/api/v1/jobs/{job_id}"),
    ("POST", "/api/v1/interview/sessions"),
    ("GET", "/api/v1/interview/sessions"),
    ("POST", "/api/v1/interview/sessions/{session_id}/respond"),
    ("GET", "/api/v1/analytics/overview"),
    ("POST", "/api/v1/analytics/events"),
    ("POST", "/api/v1/company/opportunities"),
    ("GET", "/api/v1/company/candidates"),
    ("GET", "/api/v1/company/applicants"),
    ("PATCH", "/api/v1/company/applications/{application_id}/advance"),
    ("GET", "/api/v1/university/overview"),
    ("GET", "/api/v1/university/students"),
    ("POST", "/api/v1/university/students/{student_profile_id}/verify"),
    ("GET", "/api/v1/ml/health"),
    ("POST", "/api/v1/ml/extract-resume"),
    ("POST", "/api/v1/ml/multilingual/understand"),
    ("POST", "/api/v1/ml/semantic-match"),
    ("POST", "/api/v1/ml/eligibility/evaluate"),
    ("POST", "/api/v1/ml/rank-opportunities"),
    ("POST", "/api/v1/ml/verify-evidence"),
    ("POST", "/api/v1/ml/recommend-pipeline"),
]


def test_sdk_endpoints_match_fastapi_router_without_legacy_404_paths() -> None:
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    openapi_paths = app.openapi().get("paths", {})
    registered: set[tuple[str, str]] = {
        (method.upper(), path)
        for path, ops in openapi_paths.items()
        for method in ops
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }

    for expected in SDK_ENDPOINTS:
        assert expected in registered, f"Missing FastAPI contract route: {expected}"

    sdk_text = API_CLIENT_SRC.read_text(encoding="utf-8")
    # Ensure the 4 historical mismatched routes never reappear
    assert "'/users/me/profile'" not in sdk_text
    assert "`/eligibility/evaluate/$" not in sdk_text
    assert "`/agents/approval/$" not in sdk_text
    assert not re.search(r"request[^(]*\(`/opportunities/discover\?", sdk_text)


def test_ml_endpoints_require_auth_and_security_headers_are_present() -> None:
    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    client = TestClient(app)

    for method, path in [
        ("GET", "/api/v1/ml/health"),
        ("POST", "/api/v1/ml/extract-resume"),
        ("POST", "/api/v1/ml/multilingual/understand"),
        ("POST", "/api/v1/ml/semantic-match"),
        ("POST", "/api/v1/ml/eligibility/evaluate"),
        ("POST", "/api/v1/ml/rank-opportunities"),
        ("POST", "/api/v1/ml/verify-evidence"),
        ("POST", "/api/v1/ml/recommend-pipeline"),
    ]:
        res = client.request(method, path, json={} if method == "POST" else None)
        assert res.status_code == 401, f"Expected 401 on {method} {path}, got {res.status_code}"
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"


def test_rate_limiter_enforces_429_rfc7807() -> None:
    from fastapi import Depends

    from app.api.v1.ml import ml_router  # noqa: F401
    from app.core.security_middleware import rate_limit

    reset_local_rate_limits()
    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))

    @app.get("/_test/limited", dependencies=[Depends(rate_limit("test_scope", limit=2))])
    async def _limited() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/_test/limited").status_code == 200
    assert client.get("/_test/limited").status_code == 200
    blocked = client.get("/_test/limited")
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") is not None
    assert blocked.headers.get("content-type", "").startswith("application/problem+json")
    assert blocked.json()["status"] == 429
