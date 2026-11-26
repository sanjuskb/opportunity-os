"""Pydantic schemas for deterministic eligibility requirements and traceable audit results."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

EligibilityOutcome = Literal["eligible", "ineligible", "needs_more_info", "unable_to_verify"]
RuleCheckOutcome = Literal["pass", "fail", "missing_student_info", "unable_to_verify"]


class RequirementEvidence(BaseModel):
    field: str
    is_explicit: bool = True
    source_snippet: str


class StructuredOpportunityRequirements(BaseModel):
    opportunity_id: str
    title: str
    eligible_degrees: list[str] = Field(default_factory=list)
    eligible_branches: list[str] = Field(default_factory=list)
    eligible_graduation_years: list[int] = Field(default_factory=list)
    eligible_academic_years: list[int] = Field(default_factory=list)  # e.g., [2, 3] for 2nd/3rd year
    min_cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    max_active_backlogs: int | None = Field(default=None, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_months: int | None = Field(default=None, ge=0)
    allowed_locations: list[str] = Field(default_factory=list)
    remote_allowed: bool | None = None
    required_citizenship: str | None = None  # Only populated when legally & explicitly specified
    deadline: date | None = None
    ambiguous_clauses: list[str] = Field(default_factory=list)
    evidence: list[RequirementEvidence] = Field(default_factory=list)


class StudentEligibilityInput(BaseModel):
    student_id: str
    degree: str | None = None
    branch: str | None = None
    graduation_year: int | None = None
    current_academic_year: int | None = Field(default=None, ge=1, le=6)
    cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    active_backlogs: int | None = Field(default=None, ge=0)
    skills: list[str] = Field(default_factory=list)
    experience_months: int | None = Field(default=None, ge=0)
    preferred_locations: list[str] = Field(default_factory=list)
    open_to_relocate: bool | None = None
    citizenship: str | None = None


class RuleAuditItem(BaseModel):
    requirement: str
    is_explicit_requirement: bool = True
    student_value: str | None
    comparison_result: RuleCheckOutcome
    evidence_source: str
    reason: str


class EligibilityDecision(BaseModel):
    opportunity_id: str
    status: EligibilityOutcome
    is_eligible: bool
    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    audit_trail: list[RuleAuditItem] = Field(default_factory=list)
    summary_reason: str
