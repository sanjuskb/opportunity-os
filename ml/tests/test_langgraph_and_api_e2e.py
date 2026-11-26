"""
True End-to-End Integration Tests:
  1. Real FastAPI HTTP Application (`apps/api/app/main.py`) + Real `NexteRaSMLService`
     loaded with the fine-tuned `ml/artifacts/minilm-nexteras-v1` checkpoint (when present)
  2. Real Compiled LangGraph `StateGraph` with MemorySaver Checkpointer + M11 Interrupt/Resume
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"
for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import Settings  # noqa: E402
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier  # noqa: E402
from app.core.security_middleware import reset_local_rate_limits  # noqa: E402
from app.main import create_application  # noqa: E402
from ml.src.infrastructure.runtime import ResourceManagedModelCache  # noqa: E402
from ml.src.integration.fastapi_adapter import NexteRaSMLService  # noqa: E402
from ml.src.integration.langgraph_adapter import build_nexteras_career_workflow  # noqa: E402

_TEST_SECRET = "test-ml-e2e-secret-key-at-least-32-chars"
_TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _make_auth_headers() -> dict[str, str]:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": _TEST_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "role": "authenticated",
        },
        _TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_real_fastapi_end_to_end_with_trained_minilm() -> None:
    reset_local_rate_limits()
    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
    try:
        svc = NexteRaSMLService(cache=cache, use_pretrained_nli=False)
        app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
        app.dependency_overrides[get_jwt_verifier] = lambda: SupabaseJWTVerifier(
            Settings(
                SUPABASE_URL="https://demo-project.supabase.co",
                SUPABASE_JWT_SECRET=_TEST_SECRET,
                SUPABASE_JWT_AUDIENCE="authenticated",
            )
        )
        app.state.ml_service = svc
        client = TestClient(app)
        headers = _make_auth_headers()

        # Unauthenticated calls must fail cleanly with 401
        assert client.get("/api/v1/ml/health").status_code == 401

        health = client.get("/api/v1/ml/health", headers=headers)
        assert health.status_code == 200
        assert health.json()["ml_available"] is True

        req_payload: dict[str, Any] = {
            "resume_text": (
                "Ananya Iyer\nEducation\nNIT Surathkal | B.Tech CSE | Batch 2026 | CGPA: 8.6/10\n"
                "Technical Skills\nPython, FastAPI, PostgreSQL, Docker\n"
                "Projects\nHostel Slot Server - Built atomic SQL row-lock API routes in Python and FastAPI."
            ),
            "query_text": "Mujhe Python FastAPI backend API internship chahiye",
            "student_overrides": {
                "student_id": "e2e-stu-1",
                "active_backlogs": 0,
                "preferred_locations": ["Bengaluru"],
                "open_to_relocate": False,
            },
            "preferences": {
                "student_id": "e2e-stu-1",
                "preferred_types": ["internship"],
                "preferred_locations": ["Bangalore"],
                "remote_preferred": True,
                "min_compensation_inr": 25000,
            },
            "candidates": [
                {
                    "opportunity": {
                        "opportunity_id": "e2e-opp-best",
                        "title": "Transactional Backend Platform Intern",
                        "description": "HTTP microservices with PostgreSQL locks and async workers.",
                        "eligible_degrees": ["B.Tech"],
                        "eligible_branches": ["CSE"],
                        "eligible_graduation_years": [2026],
                        "min_cgpa": 7.5,
                        "max_active_backlogs": 0,
                        "allowed_locations": ["Bengaluru"],
                        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                        "deadline": "2026-12-30",
                    },
                    "organization": "PayGrid Fintech",
                    "location": "Bangalore",
                    "is_verified_source": True,
                    "has_compensation": True,
                    "monthly_compensation_inr": 50000,
                },
                {
                    "opportunity": {
                        "opportunity_id": "e2e-opp-inelig",
                        "title": "High-Stipend Backend Intern (CGPA 9.5 Only)",
                        "description": "Backend API role requiring 9.5 CGPA.",
                        "eligible_degrees": ["B.Tech"],
                        "min_cgpa": 9.5,
                        "required_skills": ["Python"],
                        "deadline": "2026-12-30",
                    },
                    "organization": "StrictCGPA Labs",
                    "location": "Remote",
                    "is_remote": True,
                    "is_verified_source": True,
                    "has_compensation": True,
                    "monthly_compensation_inr": 90000,
                },
            ],
            "career_passport_premise": "Built atomic SQL row-lock API routes in Python and FastAPI.",
            "synthesized_resume_claims": [
                "Engineered Python and FastAPI SQL row-lock API routes.",
                "Led a 10-year nuclear physics team at CERN.",
            ],
            "reference_date": date(2026, 11, 25).isoformat(),
        }

        resp = client.post("/api/v1/ml/recommend-pipeline", json=req_payload, headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        assert body["requires_human_approval"] is True
        assert body["approval_status"] == "pending"
        assert body["extracted_profile"]["profile"]["full_name"] == "Ananya Iyer"
        assert body["multilingual_metadata"]["preprocessed"]["predicted_locale"] == "hinglish"
        assert body["multilingual_metadata"]["preprocessed"]["original_text"] == req_payload["query_text"]

        # Hard eligibility gate ensures ineligible high-stipend job CANNOT outrank eligible job
        ranked_ids = [r["opportunity_id"] for r in body["ranking"]["ranked"]]
        excluded_ids = [e["opportunity_id"] for e in body["ranking"]["excluded"]]
        assert ranked_ids == ["e2e-opp-best"]
        assert "e2e-opp-inelig" in excluded_ids

        # Evidence verification advisory verdicts
        verdicts = [v["verdict"] for v in body["evidence_verifications"]]
        assert "insufficient_evidence" in verdicts or "contradicted" in verdicts
    finally:
        cache.clear()


def test_real_compiled_langgraph_stategraph_halts_and_resumes_at_m11() -> None:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.types import Command

    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
    try:
        svc = NexteRaSMLService(cache=cache, use_pretrained_nli=False)
        saver = MemorySaver()
        graph = build_nexteras_career_workflow(svc, checkpointer=saver, use_interrupt=True)

        initial_state = {
            "resume_text": (
                "Rohan Deshmukh\nEducation\nVTU | B.E. CSE | Batch 2026 | CGPA: 8.2/10\n"
                "Skills\nPython, FastAPI, PostgreSQL"
            ),
            "query_text": "Looking for Python FastAPI backend internship",
            "student_overrides": {"active_backlogs": 0, "preferred_locations": ["Remote"]},
            "preferences": {
                "student_id": "lg-stu-1",
                "preferred_types": ["internship"],
                "remote_preferred": True,
            },
            "raw_candidates": [
                {
                    "opportunity_id": "lg-opp-1",
                    "title": "Backend API Intern",
                    "organization": "CloudFlow",
                    "description": "FastAPI REST APIs with PostgreSQL.",
                    "eligible_degrees": ["B.Tech"],
                    "eligible_graduation_years": [2026],
                    "min_cgpa": 7.5,
                    "remote_allowed": True,
                    "required_skills": ["Python", "FastAPI"],
                    "deadline": date(2026, 12, 30),
                    "is_remote": True,
                    "is_verified_source": True,
                    "has_compensation": True,
                    "monthly_compensation_inr": 35000,
                }
            ],
            "synthesized_bullets": ["Developed FastAPI REST APIs using PostgreSQL and Python."],
            "career_passport_premise": "Developed FastAPI REST APIs with PostgreSQL and Python.",
            "reference_date": date(2026, 11, 25),
        }

        cfg = {"configurable": {"thread_id": "m11-approve-flow"}}
        halted = graph.invoke(initial_state, config=cfg)

        # Must halt BEFORE ACT via LangGraph interrupt()
        assert "__interrupt__" in halted
        assert halted.get("dispatched") is not True
        assert halted["stage_trace"] == ["PERCEIVE", "REASON", "PLAN", "DELEGATE_VERIFY"]

        # Resuming with explicit human approval executes ACT + EVALUATE_ADAPT
        resumed = graph.invoke(Command(resume={"approved": True}), config=cfg)
        assert resumed["requires_human_approval"] is True
        assert resumed["human_approval_decision"] == "approved"
        assert resumed["dispatched"] is True
        assert resumed["dispatch_receipt"] == "DRY_RUN_APPROVED_FOR_lg-opp-1"
        assert "ACT" in resumed["stage_trace"]
        assert "EVALUATE_ADAPT" in resumed["stage_trace"]

        # Rejecting at M11 blocks dispatch cleanly
        cfg_reject = {"configurable": {"thread_id": "m11-reject-flow"}}
        halted_rej = graph.invoke(initial_state, config=cfg_reject)
        assert "__interrupt__" in halted_rej
        rejected = graph.invoke(Command(resume={"approved": False}), config=cfg_reject)
        assert rejected["human_approval_decision"] == "rejected"
        assert rejected["dispatched"] is False
        assert "ACT_BLOCKED" in rejected["stage_trace"]
    finally:
        cache.clear()
