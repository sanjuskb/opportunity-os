"""Integration tests for FastAPI adapter, LangGraph nodes, and API fallback safety."""

from __future__ import annotations

from datetime import date

import numpy as np

from apps.api.app.ml.adapter import get_ml_service, is_ml_subsystem_available
from ml.src.eligibility.parser import parse_opportunity_requirements
from ml.src.eligibility.schemas import StudentEligibilityInput
from ml.src.integration.fastapi_adapter import NexteRaSMLService
from ml.src.integration.langgraph_adapter import NexteRaSLangGraphAdapter


class _MockSemanticEncoder:
    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False):
        return np.tile(np.array([0.5, 0.5, 0.5, 0.5], dtype=float), (len(texts), 1))


class _FailingSemanticEncoder:
    def encode(self, *args, **kwargs):
        raise RuntimeError("Simulated missing checkpoint")


def test_unified_service_and_langgraph_human_gate() -> None:
    svc = NexteRaSMLService(
        semantic_encoder_override=_MockSemanticEncoder(),
        multilingual_encoder_override=_MockSemanticEncoder(),
        use_pretrained_nli=False,
    )
    hr = svc.health_and_readiness()
    assert hr.status == "healthy"
    assert hr.cuda_available is False
    assert hr.registry_count >= 6

    extracted = svc.extract_resume("Kiran Rao\nB.Tech CSE Batch 2026 CGPA: 8.5\nSkills: Python, FastAPI, PostgreSQL")
    assert extracted.profile.graduation_year == 2026

    reqs = parse_opportunity_requirements(
        "opp-api-1",
        "Backend Intern",
        "Open to B.Tech batch 2026, minimum CGPA 8.0. Required: Python, FastAPI.",
        explicit_deadline=date(2026, 12, 31),
    )
    lg = NexteRaSLangGraphAdapter(svc)
    stu = StudentEligibilityInput(
        student_id="st-1",
        degree=extracted.profile.degree,
        branch=extracted.profile.branch_or_specialization,
        graduation_year=extracted.profile.graduation_year,
        cgpa=extracted.profile.cgpa,
        skills=extracted.normalized_skills,
    )
    elig_state = lg.eligibility_hard_rule_node(
        {
            "student_profile": stu.model_dump(),
            "opportunity_requirements": reqs.model_dump(),
            "reference_date": date(2026, 11, 25),
        }
    )
    assert elig_state["hard_pass"] is True

    api_resp = svc.evaluate_eligibility_for_api(stu, reqs, semantic_similarity=0.88, reference_date=date(2026, 11, 25))
    assert api_resp.is_eligible is True
    assert api_resp.score > 0.0

    # Verify M11 Human-in-the-Loop Gate is NEVER bypassed
    guard_state = lg.resume_evidence_guardrail_node(
        {
            "career_passport_premise": "Built FastAPI REST APIs with PostgreSQL.",
            "synthesized_bullets": ["Developed FastAPI REST APIs using PostgreSQL."],
        }
    )
    assert guard_state["requires_human_approval"] is True


def test_apps_api_ml_adapter_and_unavailable_fallback() -> None:
    assert is_ml_subsystem_available() is True
    bridge_svc = get_ml_service(semantic_encoder_override=_MockSemanticEncoder(), use_pretrained_nli=False)
    assert bridge_svc.health_and_readiness().status == "healthy"

    broken_svc = NexteRaSMLService(semantic_encoder_override=_FailingSemanticEncoder(), use_pretrained_nli=False)
    # When internal cache raises MLInferenceError on model init, match_semantic degrades gracefully
    from ml.src.infrastructure.runtime import MLInferenceError

    def _failing_loader(*args, **kwargs):
        raise MLInferenceError("MODEL_LOAD_FAILED", "Offline test")

    broken_svc.semantic_matcher._encoder_override = None
    broken_svc.semantic_matcher._get_model = _failing_loader  # type: ignore[method-assign]
    matches, model_used = broken_svc.match_semantic("Python", [{"doc_id": "1", "doc_text": "Python"}])
    assert matches == []
    assert model_used == "fallback_unavailable"
