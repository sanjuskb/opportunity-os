"""Pydantic request/response schemas for NexteRaS ML FastAPI endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class MLHealthResponse(BaseModel):
    status: str
    readiness: str
    device: str
    cuda_available: bool
    loaded_models: list[str]
    registry_count: int
    ml_available: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class ResumeExtractRequest(BaseModel):
    resume_text: str = Field(min_length=5, max_length=100_000)


class MultilingualUnderstandRequest(BaseModel):
    query_text: str = Field(min_length=2, max_length=10_000)
    document_texts: list[str] = Field(default_factory=list)


class SemanticMatchCandidateInput(BaseModel):
    doc_id: str = Field(min_length=1)
    title: str | None = None
    doc_text: str = Field(min_length=2)


class SemanticMatchRequest(BaseModel):
    student_query: str = Field(min_length=2, max_length=20_000)
    opportunities: list[SemanticMatchCandidateInput] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)


class EligibilityStudentInputDTO(BaseModel):
    student_id: str
    degree: str | None = None
    branch: str | None = None
    graduation_year: int | None = None
    current_academic_year: int | None = None
    cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    active_backlogs: int | None = Field(default=None, ge=0)
    skills: list[str] = Field(default_factory=list)
    experience_months: int | None = Field(default=None, ge=0)
    preferred_locations: list[str] = Field(default_factory=list)
    open_to_relocate: bool | None = None
    citizenship: str | None = None


class EligibilityOpportunityInputDTO(BaseModel):
    opportunity_id: str
    title: str
    description: str = ""
    eligible_degrees: list[str] = Field(default_factory=list)
    eligible_branches: list[str] = Field(default_factory=list)
    eligible_graduation_years: list[int] = Field(default_factory=list)
    eligible_academic_years: list[int] = Field(default_factory=list)
    min_cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    max_active_backlogs: int | None = Field(default=None, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_months: int | None = Field(default=None, ge=0)
    allowed_locations: list[str] = Field(default_factory=list)
    remote_allowed: bool | None = None
    required_citizenship: str | None = None
    deadline: date | None = None
    ambiguous_clauses: list[str] = Field(default_factory=list)


class EvaluateEligibilityRequest(BaseModel):
    student: EligibilityStudentInputDTO
    opportunity: EligibilityOpportunityInputDTO
    semantic_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    reference_date: date | None = None


class RankCandidateItemDTO(BaseModel):
    opportunity: EligibilityOpportunityInputDTO
    organization: str
    opportunity_type: str = "internship"
    location: str = ""
    is_remote: bool = False
    source_url: str | None = None
    is_verified_source: bool = False
    has_compensation: bool = False
    monthly_compensation_inr: int | None = Field(default=None, ge=0)
    is_active: bool = True


class RankStudentPrefsDTO(BaseModel):
    student_id: str
    preferred_types: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preferred: bool = False
    min_compensation_inr: int | None = Field(default=None, ge=0)
    career_interests: list[str] = Field(default_factory=list)


class RankOpportunitiesRequest(BaseModel):
    student: EligibilityStudentInputDTO
    preferences: RankStudentPrefsDTO
    student_query_text: str = Field(min_length=2)
    candidates: list[RankCandidateItemDTO] = Field(default_factory=list)
    reference_date: date | None = None


class VerifyEvidenceRequestDTO(BaseModel):
    claim_id: str = "claim-1"
    premise_text: str = Field(min_length=3, max_length=10_000)
    hypothesis_claim: str = Field(min_length=3, max_length=5_000)


class PipelineRecommendRequest(BaseModel):
    resume_text: str = Field(min_length=10, max_length=100_000)
    query_text: str = Field(min_length=2, max_length=10_000)
    student_overrides: dict[str, Any] = Field(default_factory=dict)
    preferences: RankStudentPrefsDTO
    candidates: list[RankCandidateItemDTO] = Field(default_factory=list)
    synthesized_resume_claims: list[str] = Field(default_factory=list)
    career_passport_premise: str = ""
    reference_date: date | None = None
