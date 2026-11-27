"""Unit tests for WS8 autonomous 9-agent LangGraph orchestrator, M11 resume, SSE & screenshots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.core.security_middleware import reset_local_rate_limits
from app.db.session import get_db_session
from app.main import create_application
from app.schemas.common import (
    EligibilityCheckResponse,
    OpportunityResponse,
    PaginatedOpportunitiesResponse,
)

JWT_SECRET = f"ws8-unit-{uuid4().hex}-{uuid4().hex}"


def _token(user_id: UUID) -> str:
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


def test_autonomous_langgraph_interrupt_resume_sse_and_screenshot_guardrails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reset_local_rate_limits()
    uid = uuid4()
    other_uid = uuid4()
    opp_id = uuid4()
    app_row_id = uuid4()
    resume_id = uuid4()

    shot_dir = tmp_path / "shots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    valid_shot = shot_dir / "pre_submit_sample.png"
    valid_shot.write_bytes(b"\x89PNG\r\n\x1a\nfake-png-bytes")
    outside_shot = tmp_path / "escape.png"
    outside_shot.write_bytes(b"\x89PNG\r\n\x1a\noutside")

    monkeypatch.setattr(
        "app.automation.playwright_runner.settings.PLAYWRIGHT_SCREENSHOT_DIR", str(shot_dir)
    )

    # In-memory store simulating PostgreSQL rows cleanly for offline unit testing
    store: dict[str, Any] = {
        "sessions": {},
        "events": [],
        "approvals": {},
        "applications": {},
        "analytics": [],
        "interviews": [],
        "logs": {},
    }

    class _Scalars:
        def __init__(self, items):
            self._items = items

        def all(self):
            return list(self._items)

    class _Res:
        def __init__(self, items):
            self._items = items

        def scalar_one_or_none(self):
            return self._items[0] if self._items else None

        def scalars(self):
            return _Scalars(self._items)

    class _FakeDb:
        def add(self, obj):
            cls_name = obj.__class__.__name__
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None and hasattr(obj, "created_at"):
                obj.created_at = datetime.now(UTC)
            if cls_name == "AgentSession":
                store["sessions"][obj.id] = obj
            elif cls_name == "AgentEvent":
                store["events"].append(obj)
            elif cls_name == "ApprovalRequest":
                store["approvals"][obj.id] = obj
            elif cls_name == "Application":
                store["applications"][obj.id] = obj
            elif cls_name == "AnalyticsEvent":
                store["analytics"].append(obj)
            elif cls_name == "InterviewSession":
                store["interviews"].append(obj)

        async def flush(self):
            return None

        async def refresh(self, obj):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

        async def get(self, model, pk):
            name = model.__name__
            if name == "AgentSession":
                return store["sessions"].get(pk)
            if name == "ApprovalRequest":
                return store["approvals"].get(pk)
            if name == "Application":
                return store["applications"].get(pk)
            return None

        async def execute(self, stmt):
            sql = str(stmt)
            if "FROM public.agent_sessions" in sql:
                # Filter by params when querying single session vs user list
                vals = list(store["sessions"].values())
                compiled_params = stmt.compile().params
                if "id_1" in compiled_params:
                    vals = [
                        s
                        for s in vals
                        if str(s.id) == str(compiled_params["id_1"])
                        and str(s.user_id) == str(compiled_params["user_id_1"])
                    ]
                elif "user_id_1" in compiled_params:
                    vals = [s for s in vals if str(s.user_id) == str(compiled_params["user_id_1"])]
                return _Res(vals)
            if "FROM public.agent_events" in sql:
                sid_param = stmt.compile().params.get("session_id_1")
                evs = [
                    e
                    for e in store["events"]
                    if not sid_param or str(e.session_id) == str(sid_param)
                ]
                return _Res(evs)
            if "FROM public.browser_execution_logs" in sql:
                compiled_params = stmt.compile().params
                log_id = compiled_params.get("id_1")
                req_uid = compiled_params.get("user_id_1")
                log_obj = store["logs"].get(log_id)
                if log_obj is not None and str(log_obj.owner_id) == str(req_uid):
                    return _Res([log_obj])
                return _Res([])
            return _Res([])

    # Add two BrowserExecutionLog fixtures (valid path & path-traversal path)
    valid_log_id = uuid4()
    bad_log_id = uuid4()
    store["logs"][valid_log_id] = SimpleNamespace(
        id=valid_log_id, owner_id=uid, screenshot_url=str(valid_shot)
    )
    store["logs"][bad_log_id] = SimpleNamespace(
        id=bad_log_id, owner_id=uid, screenshot_url=str(outside_shot)
    )

    # Patch repositories/services used inside build_autonomous_career_graph for pure unit run
    monkeypatch.setattr(
        "app.agents.orchestrator.ProfileRepository.get_by_user_id",
        _async_val(SimpleNamespace(full_name="Ananya Iyer", email="ananya@nitk.edu.in")),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.StudentProfileRepository.get_by_user_id",
        _async_val(
            SimpleNamespace(
                college_name="NITK",
                degree="B.Tech",
                branch="CSE",
                graduation_year=2026,
                cgpa=8.9,
                skills=["Python", "FastAPI"],
            )
        ),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.CareerPassportRepository.get_by_user_id",
        _async_val(SimpleNamespace(projects=[{"title": "Distributed Lock API"}])),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.ResumeRepository.list_for_user",
        _async_val([SimpleNamespace(id=resume_id)]),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.OpportunityService.discover",
        _async_val(
            PaginatedOpportunitiesResponse(
                items=[
                    OpportunityResponse(
                        id=opp_id,
                        title="AI Platform Intern",
                        organization="NexteRaS Labs",
                        location="Bengaluru",
                        type="internship",
                        description="Python FastAPI role",
                        source_url="https://example.com/apply",
                        source_provider="olostep",
                        is_active=True,
                        required_skills=["Python"],
                        match_score=92.0,
                    )
                ],
                next_cursor=None,
                has_more=False,
            )
        ),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.IntelligenceService.enrich_company",
        _async_val(
            SimpleNamespace(name="NexteRaS Labs", is_verified=True, headcount_range="51-200")
        ),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.EligibilityService.evaluate",
        _async_val(
            EligibilityCheckResponse(
                opportunity_id=str(opp_id),
                student_id=str(uid),
                is_eligible=True,
                status="eligible",
                score=94.0,
                reasons=["Eligible"],
                missing_skills=["Kubernetes"],
            )
        ),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.ResumeService.tailor_resume",
        _async_val(
            SimpleNamespace(verified_claims=[{"claim": "Built FastAPI"}], rejected_claims=[])
        ),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.ApplicationRepository.get_by_user_and_opportunity",
        _async_val(SimpleNamespace(id=app_row_id, status="drafting")),
    )
    monkeypatch.setattr(
        "app.agents.orchestrator.ApplicationRepository.transition_status_for_user",
        _async_val(SimpleNamespace(id=app_row_id, status="ready_for_review")),
    )

    fake_db = _FakeDb()

    async def _override_db():
        yield fake_db

    cfg = Settings(
        ENVIRONMENT="development",
        REDIS_URL="",
        SUPABASE_JWT_SECRET=JWT_SECRET,
        SUPABASE_JWT_ISSUER="https://example.supabase.co/auth/v1",
        GEMINI_API_KEY="",
    )
    app = create_application(cfg)
    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_jwt_verifier] = lambda: SupabaseJWTVerifier(cfg)

    headers = {"Authorization": f"Bearer {_token(uid)}"}
    other_headers = {"Authorization": f"Bearer {_token(other_uid)}"}

    with TestClient(app) as client:
        # 1. Launch autonomous LangGraph workflow -> halts cleanly at M11 interrupt()
        run_resp = client.post(
            "/api/v1/agents/runs",
            headers=headers,
            json={"query": "AI Platform Intern", "workflowType": "full_pipeline", "language": "hi"},
        )
        assert run_resp.status_code == 200
        run_body = run_resp.json()
        assert run_body["status"] == "awaiting_human_approval"
        assert run_body["currentStage"] == "awaiting_human_approval"
        assert run_body["approvalRequestId"] is not None
        assert run_body["tailoredResumeId"] == str(resume_id)
        assert run_body["skillGaps"] == ["Kubernetes"]
        assert len(run_body["events"]) >= 6

        session_id = UUID(run_body["sessionId"])
        approval_id = UUID(run_body["approvalRequestId"])

        # 2. Cross-user access blocked with 404
        assert (
            client.get(f"/api/v1/agents/sessions/{session_id}", headers=other_headers).status_code
            == 404
        )

        # 3. SSE telemetry stream emits agent_event + stream_end
        sse_resp = client.get(
            f"/api/v1/agents/sessions/{session_id}/stream?once=true",
            headers=headers,
        )
        assert sse_resp.status_code == 200
        assert "event: agent_event" in sse_resp.text
        assert "event: stream_end" in sse_resp.text

        # 4. Operator command query logs event and returns grounded reply
        cmd_resp = client.post(
            f"/api/v1/agents/sessions/{session_id}/command",
            headers=headers,
            json={"action": "query", "command": "What stage is active?", "language": "hi"},
        )
        assert cmd_resp.status_code == 200
        assert "awaiting_human_approval" in cmd_resp.json()["reply"]

        # 5. Screenshot ownership & traversal guardrails
        assert (
            client.get(
                f"/api/v1/browser-logs/{valid_log_id}/screenshot", headers=other_headers
            ).status_code
            == 404
        )
        assert (
            client.get(f"/api/v1/browser-logs/{bad_log_id}/screenshot", headers=headers).status_code
            == 403
        )
        png_resp = client.get(f"/api/v1/browser-logs/{valid_log_id}/screenshot", headers=headers)
        assert png_resp.status_code == 200
        assert png_resp.headers["content-type"] == "image/png"
        assert png_resp.content.startswith(b"\x89PNG")

        # 6. Human approval decision resumes suspended LangGraph M11 -> M09 cleanly
        decided_resp = SimpleNamespace(
            id=approval_id,
            session_id=session_id,
            user_id=uid,
            opportunity_id=opp_id,
            action_type="submit_application",
            payload_summary={"langgraph_thread_id": str(session_id)},
            status="approved",
            user_decision_at=datetime.now(UTC),
            rejection_reason=None,
            created_at=datetime.now(UTC),
        )
        monkeypatch.setattr(
            "app.services.approvals.ApprovalService.decide_approval",
            _async_val(
                SimpleNamespace(
                    approval_id=approval_id,
                    user_id=uid,
                    opportunity_id=opp_id,
                    status="approved",
                    user_decision_at=datetime.now(UTC),
                    model_copy=lambda update: {
                        "approval_id": approval_id,
                        "user_id": uid,
                        "opportunity_id": opp_id,
                        "status": "approved",
                        "user_decision_at": datetime.now(UTC),
                        **update,
                    },
                )
            ),
        )
        monkeypatch.setattr(
            "app.agents.orchestrator.ApprovalRepository.get_for_user",
            _async_val(decided_resp),
        )

        dec_res = client.post(
            f"/api/v1/agents/approvals/{approval_id}/decision",
            headers=headers,
            json={"approved": True, "executeSubmission": False},
        )
        assert dec_res.status_code == 200
        dec_json = dec_res.json()
        assert dec_json["workflowResumed"] is True
        assert dec_json["resumedStage"] == "approved_ready_for_dispatch"
        assert len(store["interviews"]) == 1
        assert store["sessions"][session_id].is_active is False


def _async_val(value):
    async def _fn(*args, **kwargs):
        return value

    return _fn
