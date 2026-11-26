"""Typed API & LangGraph compatibility contracts aligning with apps/api/app/schemas/common.py."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProblemDetailsDTO(BaseModel):
    """RFC 7807 error payload aligning with CROSS_TEAM_CONTRACT_REGISTER.md."""

    type: str = "urn:problem:ml_inference_error"
    title: str
    status: int = 500
    detail: str
    instance: str | None = None


class EligibilityCheckAPIResponse(BaseModel):
    """Aligns directly with apps/api/app/schemas/common.py::EligibilityCheckResponse + @opportunity-os/shared-types."""

    opportunity_id: str
    status: str  # eligible | ineligible | needs_more_info | unable_to_verify
    is_eligible: bool
    score: float = Field(ge=0.0, le=100.0)
    deterministic_checks: dict[str, bool] = Field(default_factory=dict)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    model_version: str = "deterministic-rule-engine-v1"


class HealthReadinessPayload(BaseModel):
    status: str
    readiness: str
    device: str
    cuda_available: bool
    loaded_models: list[str]
    registry_count: int
    details: dict[str, Any] = Field(default_factory=dict)
