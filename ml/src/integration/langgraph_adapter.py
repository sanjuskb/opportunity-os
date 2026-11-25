"""Typed LangGraph node compatibility adapters enforcing human approval safety invariants."""

from __future__ import annotations

from typing import Any

from ml.src.eligibility.schemas import StructuredOpportunityRequirements, StudentEligibilityInput
from ml.src.integration.fastapi_adapter import NexteRaSMLService
from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences
from ml.src.verification.schemas import VerificationRequest


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
                    claim_id=f"bullet-{idx+1}",
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
