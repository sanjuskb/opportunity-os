"""
Real Compiled LangGraph StateGraph & Typed Node Adapters for NexteRaS.

Implements the complete 7-stage Agentic Cognitive Loop:
  PERCEIVE -> REASON -> PLAN -> DELEGATE/VERIFY -> HUMAN_APPROVAL_GATE (M11) -> ACT (GATED) -> EVALUATE/ADAPT

Enforces mandatory human-in-the-loop halting (`interrupt()` / explicit pending state) before any
external action/submission can execute.
"""

from __future__ import annotations

from datetime import date
from typing import Any, TypedDict

from ml.src.eligibility.parser import parse_opportunity_requirements
from ml.src.eligibility.schemas import StructuredOpportunityRequirements, StudentEligibilityInput
from ml.src.integration.fastapi_adapter import NexteRaSMLService
from ml.src.multilingual.preprocessing import preprocess_multilingual_query
from ml.src.multilingual.service import MultilingualUnderstandingResult
from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences
from ml.src.verification.schemas import VerificationRequest


class CareerWorkflowState(TypedDict, total=False):
    # Input payload fields
    resume_text: str
    query_text: str
    student_overrides: dict[str, Any]
    preferences: dict[str, Any]
    raw_candidates: list[dict[str, Any]]
    synthesized_bullets: list[str]
    career_passport_premise: str
    reference_date: date | None

    # Agentic cognitive loop state
    stage_trace: list[str]
    extracted_profile: dict[str, Any]
    multilingual_metadata: dict[str, Any]
    retrieval_query: str
    student_profile_input: dict[str, Any]
    eligibility_decisions: dict[str, Any]
    semantic_scores: dict[str, float]
    semantic_model_used: str
    ranked_opportunities: list[dict[str, Any]]
    excluded_opportunities: list[dict[str, Any]]
    evidence_verifications: list[dict[str, Any]]
    auxiliary_evidence_passed: bool
    recommendation_summary: str

    # M11 Human-in-the-Loop Gate invariants
    requires_human_approval: bool
    human_approval_decision: str | None  # None | "approved" | "rejected"
    dispatched: bool
    dispatch_receipt: str | None
    adaptation_note: str


class NexteRaSLangGraphAdapter:
    """
    Exposes pure typed node functions callable inside LangGraph workflows
    (`EligibilityWorkflow`, `ResumeWorkflow`, `DiscoveryWorkflow`).
    NEVER bypasses M11 Human-in-the-Loop Approval Gates.
    """

    def __init__(self, ml_service: NexteRaSMLService) -> None:
        self.ml = ml_service

    def eligibility_hard_rule_node(self, state: dict[str, Any]) -> dict[str, Any]:
        student = StudentEligibilityInput.model_validate(state["student_profile"])
        reqs = StructuredOpportunityRequirements.model_validate(state["opportunity_requirements"])
        decision = self.ml.assess_eligibility(student, reqs, reference_date=state.get("reference_date"))
        return {
            **state,
            "eligibility_decision": decision.model_dump(),
            "hard_pass": decision.is_eligible,
            "missing_skills": decision.missing_required_skills,
        }

    def opportunity_ranking_node(self, state: dict[str, Any]) -> dict[str, Any]:
        prefs = StudentRankingPreferences.model_validate(state["preferences"])
        candidates = [CandidateOpportunity.model_validate(c) for c in state.get("candidates", [])]
        ranked = self.ml.rank_opportunities(candidates, prefs, reference_date=state.get("reference_date"))
        return {
            **state,
            "ranked_opportunities": [r.model_dump() for r in ranked.ranked],
            "excluded_opportunities": [e.model_dump() for e in ranked.excluded],
        }

    def resume_evidence_guardrail_node(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluates tailored bullet claims against verified Career Passport premise.
        Always preserves `requires_human_approval = True` even when all claims look supported.
        """
        premise = str(state["career_passport_premise"])
        claims: list[str] = list(state.get("synthesized_bullets", []))
        verifications = [
            self.ml.verify_claim_evidence(
                VerificationRequest(
                    claim_id=f"bullet-{idx + 1}",
                    premise_text=premise,
                    hypothesis_claim=bullet,
                )
            ).model_dump()
            for idx, bullet in enumerate(claims)
        ]
        all_supported = all(v["verdict"] == "supported" for v in verifications) if verifications else False
        return {
            **state,
            "evidence_verifications": verifications,
            "auxiliary_evidence_passed": all_supported,
            "requires_human_approval": True,  # Mandatory M11 gate invariant
        }


def build_nexteras_career_workflow(
    ml_service: NexteRaSMLService,
    *,
    checkpointer: Any | None = None,
    use_interrupt: bool = True,
) -> Any:
    """
    Build and compile an executable LangGraph `StateGraph` implementing NexteRaS's
    PERCEIVE -> REASON -> PLAN -> DELEGATE/VERIFY -> M11_APPROVAL_GATE -> ACT -> EVALUATE_ADAPT loop.
    """
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    def perceive_node(state: CareerWorkflowState) -> dict[str, Any]:
        ext = ml_service.extract_resume(state["resume_text"])
        raw_cands = list(state.get("raw_candidates", []))
        prep = preprocess_multilingual_query(state["query_text"])
        if prep.predicted_locale == "en":
            multi_meta = MultilingualUnderstandingResult(
                preprocessed=prep,
                model_id=ml_service.semantic_matcher.model_identifier,
                embedding_dimension=ml_service.semantic_matcher.embedding_dimension,
                top_similarity_score=None,
                fallback_triggered=False,
                fallback_query_text=None,
                warnings=[],
            )
            retrieval_q = prep.normalized_text
        else:
            doc_texts = [f"{c.get('title', '')} {c.get('description', '')}".strip() for c in raw_cands]
            _, multi_meta = ml_service.analyze_multilingual(state["query_text"], doc_texts)
            retrieval_q = multi_meta.fallback_query_text or multi_meta.preprocessed.normalized_text

        ov = state.get("student_overrides") or {}
        prefs_dict = state.get("preferences") or {}
        prof = ext.profile
        stu = StudentEligibilityInput(
            student_id=str(ov.get("student_id") or prefs_dict.get("student_id") or "student-lg"),
            degree=ov.get("degree") or prof.degree,
            branch=ov.get("branch") or prof.branch_or_specialization,
            graduation_year=ov.get("graduation_year") or prof.graduation_year,
            cgpa=ov.get("cgpa") if "cgpa" in ov else prof.cgpa,
            percentage=ov.get("percentage") if "percentage" in ov else prof.percentage,
            active_backlogs=ov.get("active_backlogs"),
            skills=list({*ext.normalized_skills, *ov.get("skills", [])}),
            experience_months=ov.get("experience_months"),
            preferred_locations=ov.get("preferred_locations", prefs_dict.get("preferred_locations", [])),
            open_to_relocate=ov.get("open_to_relocate"),
            citizenship=ov.get("citizenship"),
        )
        return {
            "stage_trace": [*state.get("stage_trace", []), "PERCEIVE"],
            "extracted_profile": ext.model_dump(mode="json"),
            "multilingual_metadata": multi_meta.model_dump(mode="json"),
            "retrieval_query": retrieval_q,
            "student_profile_input": stu.model_dump(),
        }

    def reason_node(state: CareerWorkflowState) -> dict[str, Any]:
        stu = StudentEligibilityInput.model_validate(state["student_profile_input"])
        ref_date = state.get("reference_date")
        decisions: dict[str, Any] = {}
        for c in state.get("raw_candidates", []):
            oid = str(c["opportunity_id"])
            if any(
                k in c and c[k]
                for k in ("eligible_degrees", "eligible_branches", "eligible_graduation_years", "required_skills", "allowed_locations")
            ) or c.get("min_cgpa") is not None:
                reqs = StructuredOpportunityRequirements.model_validate(c)
            else:
                reqs = parse_opportunity_requirements(
                    oid,
                    str(c.get("title", "")),
                    str(c.get("description", "")),
                    explicit_deadline=c.get("deadline"),
                )
            dec = ml_service.assess_eligibility(stu, reqs, reference_date=ref_date)
            decisions[oid] = dec.model_dump(mode="json")
        return {
            "stage_trace": [*state.get("stage_trace", []), "REASON"],
            "eligibility_decisions": decisions,
        }

    def plan_node(state: CareerWorkflowState) -> dict[str, Any]:
        raw_cands = list(state.get("raw_candidates", []))
        opp_docs = [
            {
                "doc_id": str(c["opportunity_id"]),
                "title": str(c.get("title", c["opportunity_id"])),
                "doc_text": f"{c.get('title', '')} at {c.get('organization', '')}. Skills: {', '.join(c.get('required_skills', []))}. {c.get('description', '')}",
            }
            for c in raw_cands
        ]
        matches, model_used = ml_service.match_semantic(
            state["retrieval_query"], opp_docs, top_k=max(1, len(opp_docs))
        )
        sim_map = {m.doc_id: m.score for m in matches}

        elig_map = state.get("eligibility_decisions", {})
        prefs = StudentRankingPreferences.model_validate(state["preferences"])
        cand_objs = [
            CandidateOpportunity(
                opportunity_id=str(c["opportunity_id"]),
                title=str(c["title"]),
                organization=str(c.get("organization", "Unknown")),
                opportunity_type=str(c.get("opportunity_type", "internship")),
                location=str(c.get("location", "")),
                is_remote=bool(c.get("is_remote", False)),
                source_url=c.get("source_url"),
                is_verified_source=bool(c.get("is_verified_source", False)),
                has_compensation=bool(c.get("has_compensation", False)),
                monthly_compensation_inr=c.get("monthly_compensation_inr"),
                deadline=c.get("deadline"),
                is_active=bool(c.get("is_active", True)),
                semantic_similarity=sim_map.get(str(c["opportunity_id"])),
                eligibility=elig_map[str(c["opportunity_id"])],
            )
            for c in raw_cands
        ]
        ranked_resp = ml_service.rank_opportunities(
            cand_objs, prefs, reference_date=state.get("reference_date")
        )
        top_msg = (
            ranked_resp.ranked[0].ranking_explanation
            if ranked_resp.ranked
            else "No eligible opportunities matched hard constraints."
        )
        return {
            "stage_trace": [*state.get("stage_trace", []), "PLAN"],
            "semantic_scores": sim_map,
            "semantic_model_used": model_used,
            "ranked_opportunities": [r.model_dump(mode="json") for r in ranked_resp.ranked],
            "excluded_opportunities": [e.model_dump(mode="json") for e in ranked_resp.excluded],
            "recommendation_summary": top_msg,
        }

    def delegate_verify_node(state: CareerWorkflowState) -> dict[str, Any]:
        premise = str(state.get("career_passport_premise") or state["resume_text"])
        claims = list(state.get("synthesized_bullets", []))
        verifs = [
            ml_service.verify_claim_evidence(
                VerificationRequest(
                    claim_id=f"bullet-{i + 1}",
                    premise_text=premise,
                    hypothesis_claim=claim,
                )
            ).model_dump()
            for i, claim in enumerate(claims)
        ]
        all_ok = all(v["verdict"] == "supported" for v in verifs) if verifs else True
        return {
            "stage_trace": [*state.get("stage_trace", []), "DELEGATE_VERIFY"],
            "evidence_verifications": verifs,
            "auxiliary_evidence_passed": all_ok,
            "requires_human_approval": True,
        }

    def m11_approval_gate_node(state: CareerWorkflowState) -> dict[str, Any]:
        decision = state.get("human_approval_decision")
        if use_interrupt and decision not in ("approved", "rejected"):
            response = interrupt(
                {
                    "gate": "M11_HUMAN_APPROVAL",
                    "top_recommendation": (state.get("ranked_opportunities") or [None])[0],
                    "auxiliary_evidence_passed": state.get("auxiliary_evidence_passed", False),
                    "requires_human_approval": True,
                }
            )
            if isinstance(response, dict) and response.get("approved") is True:
                decision = "approved"
            else:
                decision = "rejected"
        return {
            "stage_trace": [*state.get("stage_trace", []), "M11_APPROVAL_GATE"],
            "requires_human_approval": True,
            "human_approval_decision": decision or "pending",
        }

    def act_dispatch_node(state: CareerWorkflowState) -> dict[str, Any]:
        if state.get("human_approval_decision") == "approved":
            top_list = state.get("ranked_opportunities") or []
            top_id = top_list[0]["opportunity_id"] if top_list else "none"
            return {
                "stage_trace": [*state.get("stage_trace", []), "ACT"],
                "dispatched": True,
                "dispatch_receipt": f"DRY_RUN_APPROVED_FOR_{top_id}",
            }
        return {
            "stage_trace": [*state.get("stage_trace", []), "ACT_BLOCKED"],
            "dispatched": False,
            "dispatch_receipt": "HALTED_WITHOUT_HUMAN_APPROVAL",
        }

    def evaluate_adapt_node(state: CareerWorkflowState) -> dict[str, Any]:
        eligible_cnt = len(state.get("ranked_opportunities") or [])
        excluded_cnt = len(state.get("excluded_opportunities") or [])
        return {
            "stage_trace": [*state.get("stage_trace", []), "EVALUATE_ADAPT"],
            "adaptation_note": (
                f"Cycle finished cleanly: eligible_ranked={eligible_cnt}, excluded={excluded_cnt}, "
                f"dispatched={state.get('dispatched', False)}. Pending real interaction logs before LTR weights update."
            ),
        }

    graph = StateGraph(CareerWorkflowState)
    graph.add_node("perceive", perceive_node)
    graph.add_node("reason", reason_node)
    graph.add_node("plan", plan_node)
    graph.add_node("delegate_verify", delegate_verify_node)
    graph.add_node("m11_approval_gate", m11_approval_gate_node)
    graph.add_node("act_dispatch", act_dispatch_node)
    graph.add_node("evaluate_adapt", evaluate_adapt_node)

    graph.add_edge(START, "perceive")
    graph.add_edge("perceive", "reason")
    graph.add_edge("reason", "plan")
    graph.add_edge("plan", "delegate_verify")
    graph.add_edge("delegate_verify", "m11_approval_gate")
    graph.add_edge("m11_approval_gate", "act_dispatch")
    graph.add_edge("act_dispatch", "evaluate_adapt")
    graph.add_edge("evaluate_adapt", END)

    return graph.compile(checkpointer=checkpointer)
