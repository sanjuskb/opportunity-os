"""Unit and live-browser sandbox tests for WS7 ARQ jobs, WS9 Playwright runner, and agent contracts."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.agents.contracts import AgentStateEnvelope, build_postgres_checkpoint_config
from app.automation.playwright_runner import (
    execute_approved_submission,
    prepare_application_automation,
)
from app.core.errors import ProblemDetailError
from app.db.session import DatabaseManager, check_db_health
from app.models.entities import (
    Application,
    ApprovalRequest,
    Opportunity,
    Profile,
    Resume,
    StudentProfile,
)
from app.tasks.jobs import aggregate_analytics_metrics


def _start_sandbox_portal_server() -> tuple[HTTPServer, str]:
    submitted_payloads: list[str] = []

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/captcha-portal"):
                html = (
                    "<html><body><h1>Security Gate</h1>"
                    "<p>Please verify you are human before continuing.</p>"
                    "<div class='g-recaptcha'></div>"
                    "<form><input name='full_name' /><button type='submit'>Apply</button></form>"
                    "</body></html>"
                )
            elif self.path.startswith("/submitted"):
                html = "<html><body><h1>Application Confirmed</h1></body></html>"
            else:
                html = (
                    "<html><body><h1>Intern Portal</h1>"
                    "<form action='/submitted' method='get'>"
                    "<input name='full_name' /><input name='email' type='email' />"
                    "<input name='college' /><input name='cgpa' />"
                    "<textarea name='summary'></textarea>"
                    "<button type='submit'>Submit Application</button>"
                    "</form></body></html>"
                )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _ = submitted_payloads
    return server, f"http://127.0.0.1:{port}"


def test_agent_checkpoint_contract_and_envelope() -> None:
    cfg = build_postgres_checkpoint_config()
    assert cfg.conn_uri.startswith("postgresql://")
    assert "submit_application" in cfg.interrupt_before_nodes
    env = AgentStateEnvelope(
        session_id=uuid4(),
        user_id=uuid4(),
        agent_type="application_orchestrator",
        current_stage="awaiting_human_approval",
    )
    assert env.current_stage == "awaiting_human_approval"


@pytest.mark.asyncio
async def test_playwright_sandbox_prepare_halt_captcha_and_approved_submit_live() -> None:
    db = DatabaseManager()
    if not await check_db_health(db):
        await db.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS7/WS9 automation integration test")

    from playwright.async_api import async_playwright

    # Skip gracefully only if browser binary isn't installed in this host image
    try:
        async with async_playwright() as pw:
            b = await pw.chromium.launch(headless=True)
            await b.close()
    except Exception as exc:
        await db.dispose()
        pytest.skip(f"Playwright Chromium unavailable: {exc}")

    server, base_url = _start_sandbox_portal_server()
    user_id = uuid4()
    opp_id = uuid4()
    app_id = uuid4()

    try:
        async with db.session_factory() as session:
            await session.execute(
                text("INSERT INTO auth.users (id, email) VALUES (:uid, :email)"),
                {"uid": str(user_id), "email": f"playwright-{user_id.hex[:8]}@iitb.ac.in"},
            )
            prof = await session.get(Profile, user_id)
            if prof is not None:
                prof.full_name = "Aarav Sharma"
            session.add(
                StudentProfile(
                    user_id=user_id,
                    college_name="IIT Bombay",
                    degree="B.Tech",
                    branch="CSE",
                    graduation_year=2027,
                    cgpa=9.12,
                )
            )
            session.add(
                Resume(
                    user_id=user_id,
                    title="Master SWE Resume",
                    master_content={"summary": "FastAPI & PyTorch builder.", "skills": ["Python"]},
                )
            )
            session.add(
                Opportunity(
                    id=opp_id,
                    title="Sandbox Internship",
                    organization="Sandbox Corp",
                    location="Bangalore",
                    description="Playwright sandbox test role.",
                    type="internship",
                    source_url=f"{base_url}/apply",
                    source_provider="direct_portal",
                    is_active=True,
                )
            )
            await session.flush()
            session.add(
                Application(
                    id=app_id,
                    user_id=user_id,
                    opportunity_id=opp_id,
                    status="drafting",
                )
            )
            await session.commit()

        # 1. Prepare automation: fills form, captures screenshot, STOPS at awaiting_approval
        async with db.session_factory() as session:
            prep = await prepare_application_automation(
                session,
                user_id=user_id,
                application_id=app_id,
                portal_url=f"{base_url}/apply",
            )
            assert prep.status == "awaiting_approval"
            assert prep.approval_request_id is not None
            assert prep.screenshot_path and Path(prep.screenshot_path).exists()
            assert prep.filled_fields.get("input[name='full_name']") == "Aarav Sharma"

        # 2. Executing before explicit approval MUST fail 403
        async with db.session_factory() as session:
            with pytest.raises(ProblemDetailError) as exc_unapproved:
                await execute_approved_submission(
                    session,
                    user_id=user_id,
                    application_id=app_id,
                    approval_id=prep.approval_request_id,
                )
            assert exc_unapproved.value.status_code == 403

        # 3. Approve request and execute submission
        async with db.session_factory() as session:
            approval = await session.get(ApprovalRequest, prep.approval_request_id)
            assert approval is not None
            approval.status = "approved"
            await session.commit()

            submitted = await execute_approved_submission(
                session,
                user_id=user_id,
                application_id=app_id,
                approval_id=prep.approval_request_id,
            )
            assert submitted.status == "submitted"
            assert submitted.screenshot_path and Path(submitted.screenshot_path).exists()

        # 4. CAPTCHA portal must NEVER bypass -> halts cleanly as requires_manual_completion
        async with db.session_factory() as session:
            halted = await prepare_application_automation(
                session,
                user_id=user_id,
                application_id=app_id,
                portal_url=f"{base_url}/captcha-portal",
            )
            assert halted.status == "requires_manual_completion"
            assert halted.approval_request_id is None

        # 5. ARQ domain analytics aggregator executes cleanly against live DB
        agg = await aggregate_analytics_metrics({"session_factory": db.session_factory})
        assert agg["status"] == "aggregated"
        assert agg["total_users"] >= 1
    finally:
        async with db.session_factory() as session:
            opp_obj = await session.get(Opportunity, opp_id)
            if opp_obj is not None:
                await session.delete(opp_obj)
            await session.execute(
                text("DELETE FROM auth.users WHERE id = CAST(:uid AS uuid)"),
                {"uid": str(user_id)},
            )
            await session.commit()
        await db.dispose()
        server.shutdown()
