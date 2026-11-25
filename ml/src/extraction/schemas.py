"""Pydantic schemas for structured resume & profile extraction with evidence tracking."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    field: str
    value: str
    source_snippet: str = Field(description="Exact substring or line from source resume supporting this field")


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    branch: str | None = None
    graduation_year: int | None = Field(default=None, ge=1990, le=2035)
    cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    percentage: float | None = Field(default=None, ge=0.0, le=100.0)


class ProjectOrExperienceEntry(BaseModel):
    title: str
    organization_or_context: str | None = None
    summary: str | None = None
    technologies: list[str] = Field(default_factory=list)
    evidence_snippet: str


class ExtractedResumeProfile(BaseModel):
    full_name: str | None = None
    education: list[EducationEntry] = Field(default_factory=list)
    degree: str | None = None
    branch_or_specialization: str | None = None
    graduation_year: int | None = Field(default=None, ge=1990, le=2035)
    cgpa: float | None = Field(default=None, ge=0.0, le=10.0)
    percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    projects: list[ProjectOrExperienceEntry] = Field(default_factory=list)
    experience: list[ProjectOrExperienceEntry] = Field(default_factory=list)
    internships: list[ProjectOrExperienceEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    relevant_interests: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    profile: ExtractedResumeProfile
    normalized_skills: list[str]
    extraction_mode: Literal["deterministic_rules", "hybrid_llm_validated"]
    validation_status: Literal["valid", "recovered_partial_json", "fallback_after_llm_error"]
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
