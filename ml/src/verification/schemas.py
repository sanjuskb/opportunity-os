"""Schemas for auxiliary Natural Language Inference evidence verification (never sole approval authority)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VerdictLabel = Literal["supported", "contradicted", "insufficient_evidence"]


class VerificationRequest(BaseModel):
    claim_id: str = "claim-1"
    premise_text: str = Field(min_length=3, description="Verified source evidence text (e.g., Career Passport / JD)")
    hypothesis_claim: str = Field(min_length=3, description="Claim or tailored bullet point to verify")


class VerificationResult(BaseModel):
    claim_id: str
    verdict: VerdictLabel
    entailment_score: float = Field(ge=0.0, le=1.0)
    contradiction_score: float = Field(ge=0.0, le=1.0)
    neutral_score: float = Field(ge=0.0, le=1.0)
    evidence_snippet: str
    model_used: str
    is_advisory_only: bool = True
    never_auto_approves_actions: bool = True
    reason: str
    limitations: str = (
        "NLI score is an auxiliary consistency signal only — not a guarantee of factual truth and never replaces deterministic checks or human sign-off."
    )
