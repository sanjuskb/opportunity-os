"""Pydantic schemas for separated eligibility filtering, semantic relevance, and explainable ranking."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from ml.src.eligibility.schemas import EligibilityDecision


class StudentRankingPreferences(BaseModel):
    student_id: str
    preferred_types: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preferred: bool = False
    min_compensation_inr: int | None = Field(default=None, ge=0)
    career_interests: list[str] = Field(default_factory=list)


class CandidateOpportunity(BaseModel):
    opportunity_id: str
    title: str
    organization: str
    opportunity_type: str = "internship"
    location: str = ""
    is_remote: bool = False
    source_url: str | None = None
    is_verified_source: bool = False
    has_compensation: bool = False
    monthly_compensation_inr: int | None = Field(default=None, ge=0)
    deadline: date | None = None
    is_active: bool = True
    semantic_similarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    interest_overlap_score: float | None = Field(default=None, ge=0.0, le=1.0)
    eligibility: EligibilityDecision


class ScoreContribution(BaseModel):
    factor: str
    weight: float
    raw_score: float = Field(ge=0.0, le=1.0)
    weighted_points: float
    explanation: str


class RankedOpportunity(BaseModel):
    rank: int = Field(ge=1)
    opportunity_id: str
    title: str
    organization: str
    final_score: float = Field(ge=0.0, le=100.0)
    eligibility_status: str
    contributions: list[ScoreContribution]
    ranking_explanation: str


class ExcludedCandidate(BaseModel):
    opportunity_id: str
    title: str
    reason: str
    category: Literal["expired", "inactive", "duplicate", "ineligible", "needs_more_info", "unable_to_verify"]


class RankingResponse(BaseModel):
    ranked: list[RankedOpportunity]
    excluded: list[ExcludedCandidate]
    total_input: int
    duplicates_removed: int
    expired_removed: int
