from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="0.1.0", description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    environment: str


class OpportunityResponse(BaseModel):
    id: str
    title: str
    organization: str
    location: str
    type: str
    description: str
    stipend_or_salary: str | None = None
    deadline: str | None = None
    source_url: str
    source_provider: str
    retrieval_timestamp: str
    required_skills: list[str] = []
    eligible_batches: list[int] = []
    eligible_degrees: list[str] = []
    min_cgpa: float | None = None


class EligibilityCheckRequest(BaseModel):
    student_id: str
    opportunity_id: str


class EligibilityCheckResponse(BaseModel):
    opportunity_id: str
    is_eligible: bool
    score: float = Field(ge=0.0, le=100.0)
    reasons: list[str] = []
    missing_skills: list[str] = []
