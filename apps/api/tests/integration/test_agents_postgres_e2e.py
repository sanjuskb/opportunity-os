"""Live PostgreSQL 17 + AsyncPostgresSaver + Chromium Playwright E2E tests for WS8 agents."""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.agents.orchestrator import _FALLBACK_MEMORY_SAVERS
from app.core.config import Settings, settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import DatabaseManager, check_db_health
from app.main import create_application
from app.models.entities import (
    Application,
    ApprovalRequest,
    InterviewSession,
    Opportunity,
    OpportunityEligibility,
    Profile,
    Resume,
    StudentProfile,
)

TEST_SECRET = f"ws8-e2e-{uuid4().hex}-{uuid4().hex}"
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


def _start_portal_server() -> tuple[HTTPServer, str]:
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/captcha"):
                html = (
                    "<html><body><div class='g-recaptcha'></div>"
                    "<form><input name='full_name' /><button type='submit'>Go</button></form></body></html>"
                )
            elif self.path.startswith("/submitted"):
                html = "<html><body><h1>Confirmed Submission</h1></body></html>"
            else:
                html = (
                    "<html><body><form action='/submitted' method='get'>"
                    "<input name='full_name' /><input name='email' type='email' />"
                    "<input name='college' /><input name='cgpa' />"
                    "<textarea name='summary'></textarea>"
                    "<button type='submit'>Submit Application</button></form></body></html>"
                )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


@pytest.mark.asyncio
async def test_autonomous_langgraph_postgres_saver_and_playwright_resume_e2e() -> None:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    probe = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(probe):
        await probe.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS8 AsyncPostgresSaver E2E test")
    await probe.dispose()

    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch(headless=True)
            await b.close()
    except Exception as exc:
        pytest.skip(f"Playwright Chromium unavailable: {exc}")

    server, base_url = _start_portal_server()
    reset_local_rate_limits()
    uid = uuid4()
    opp_id = uuid4()

    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    try:
        async with db.session_factory() as sess:
            await sess.execute(
                text("INSERT INTO auth.users (id, email) VALUES (:uid, :email)"),
                {"uid": str(uid), "email": f"ws8-e2e-{uid.hex[:8]}@iitb.ac.in"},
            )
            prof = await sess.get(Profile, uid)
            if prof is not None:
                prof.full_name = "Rohan Deshmukh"
            sess.add(
                StudentProfile(
                    user_id=uid,
                    college_name="IIT Bombay",
                    degree="B.Tech",
                    branch="CSE",
                    graduation_year=2026,
                    cgpa=8.85,
                    skills=["Python", "FastAPI", "PostgreSQL"],
                )
            )
            sess.add(
                Resume(
                    user_id=uid,
                    title="WS8 Master Resume",
                    master_content={
                        "summary": "Built production FastAPI & ML backends.",
                        "skills": ["Python", "FastAPI", "PostgreSQL"],
                    },
                )
            )
            sess.add(
                Opportunity(
                    id=opp_id,
                    title="WS8 Autonomous Backend Intern",
                    organization="NexteRaS AI",
                    location="Bengaluru",
                    type="internship",
                    description="Backend engineering intern role",
                    source_url=f"{base_url}/apply",
                    source_provider="direct_portal",
                    is_active=True,
                )
            )
            await sess.flush()
            sess.add(
                OpportunityEligibility(
                    opportunity_id=opp_id,
                    eligible_batches=[2026],
                    eligible_degrees=["B.Tech"],
                    required_skills=["Python", "FastAPI"],
                )
            )
            await sess.commit()

        cfg = Settings(
            ENVIRONMENT="development",
            DATABASE_URL=dsn,
            REDIS_URL="",
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            GEMINI_API_KEY="",
        )
        app = create_application(cfg)
        app.dependency_overrides[get_jwt_verifier] = lambda: SupabaseJWTVerifier(cfg)
        headers = {"Authorization": f"Bearer {_make_token(uid)}"}

        with TestClient(app) as client:
            # 1. Run full autonomous LangGraph workflow -> halts cleanly at M11 with PostgresSaver
            run_res = client.post(
                "/api/v1/agents/runs",
                headers=headers,
                json={
                    "query": "WS8 Autonomous Backend Intern",
                    "workflowType": "full_pipeline",
                    "language": "mr",
                    "targetOpportunityId": str(opp_id),
                    "portalUrl": f"{base_url}/apply",
                    "enableWebResearch": False,
                    "runPlaywright": True,
                },
            )
            assert run_res.status_code == 200
            body = run_res.json()
            assert body["checkpointerBackend"] == "postgres"
            assert body["status"] == "awaiting_human_approval"
            assert body["approvalRequestId"] is not None
            assert body["screenshotPath"] and Path(body["screenshotPath"]).exists()

            # Prove zero reliance on in-memory fallback savers across HTTP requests
            _FALLBACK_MEMORY_SAVERS.clear()

            # 2. Decide approval with executeSubmission=True -> resumes LangGraph M11 -> M09 -> Playwright submit!
            dec_res = client.post(
                f"/api/v1/agents/approvals/{body['approvalRequestId']}/decision",
                headers=headers,
                json={"approved": True, "executeSubmission": True},
            )
            assert dec_res.status_code == 200
            dec = dec_res.json()
            assert dec["status"] == "approved"
            assert dec["workflowResumed"] is True
            assert dec["submissionStatus"] == "submitted"

        async with db.session_factory() as sess:
            app_row = (
                await sess.execute(select(Application).where(Application.user_id == uid))
            ).scalar_one()
            assert app_row.status == "submitted"
            iv_row = (
                await sess.execute(select(InterviewSession).where(InterviewSession.user_id == uid))
            ).scalar_one()
            assert iv_row.language == "mr"
            apr_row = await sess.get(ApprovalRequest, UUID(body["approvalRequestId"]))
            assert apr_row is not None and apr_row.status == "approved"
    finally:
        async with db.session_factory() as sess:
            opp_obj = await sess.get(Opportunity, opp_id)
            if opp_obj is not None:
                await sess.delete(opp_obj)
            await sess.execute(
                text("DELETE FROM auth.users WHERE id = CAST(:uid AS uuid)"),
                {"uid": str(uid)},
            )
            await sess.commit()
        await db.dispose()
        server.shutdown()
