from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base schema serializing snake_case internals to camelCase JSON wire format."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StrictCamelModel(CamelModel):
    """Strict input schema rejecting unexpected fields (e.g. client-supplied userId)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="0.1.0", description="API version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    environment: str


class ReadinessDependencies(CamelModel):
    database: Literal["healthy", "unavailable"]
    redis: Literal["healthy", "unavailable"]


class ReadinessResponse(CamelModel):
    status: Literal["ready", "degraded"]
    version: str = Field(default="0.1.0")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    environment: str
    dependencies: ReadinessDependencies


class ProfileResponse(CamelModel):
    user_id: UUID
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    preferred_language: str = "en"
    supabase_role: str


class ProfileUpdateRequest(StrictCamelModel):
    full_name: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)
    preferred_language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn"] | None = None


class EducationItemResponse(CamelModel):
    id: UUID
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int | None = None
    score: str | None = None


class StudentProfileResponse(CamelModel):
    id: UUID
    user_id: UUID
    college_name: str
    degree: str
    branch: str
    graduation_year: int
    cgpa: Decimal | None = None
    state: str | None = None
    bio: str | None = None
    education: list[EducationItemResponse] = []


class StudentProfileUpsertRequest(StrictCamelModel):
    college_name: str = Field(min_length=2, max_length=200)
    degree: str = Field(min_length=2, max_length=100)
    branch: str = Field(min_length=2, max_length=120)
    graduation_year: int = Field(ge=2020, le=2035)
    cgpa: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("10.00"))
    state: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)


class CareerPassportResponse(CamelModel):
    id: UUID
    student_id: UUID
    verified_achievements: list[dict[str, Any]] = []
    coursework: list[dict[str, Any]] = []
    certifications: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []
    last_updated: datetime | None = None


class CareerPassportItemCreateRequest(StrictCamelModel):
    category: Literal["verified_achievements", "coursework", "certifications", "projects"]
    data: dict[str, Any] = Field(min_length=1)


class OpportunityResponse(CamelModel):
    id: UUID
    title: str
    organization: str
    location: str
    type: str
    description: str
    stipend_or_salary: str | None = None
    deadline: datetime | None = None
    source_url: str
    source_provider: str
    retrieval_timestamp: datetime | None = None
    is_active: bool = True
    required_skills: list[str] = []
    eligible_batches: list[int] = []
    eligible_degrees: list[str] = []
    eligible_branches: list[str] = []
    min_cgpa: Decimal | None = None


class PaginatedOpportunitiesResponse(CamelModel):
    items: list[OpportunityResponse]
    next_cursor: str | None = None
    has_more: bool


class SaveOpportunityRequest(StrictCamelModel):
    saved: bool = True
    notes: str | None = Field(default=None, max_length=500)


class SaveOpportunityResponse(CamelModel):
    opportunity_id: UUID
    saved: bool
    notes: str | None = None


class EligibilityEvaluateRequest(CamelModel):
    """Eligibility evaluation request; student identity is derived strictly from JWT."""

    opportunity_id: UUID


class EligibilityCheckResponse(CamelModel):
    opportunity_id: str
    student_id: str
    is_eligible: bool
    score: float = Field(ge=0.0, le=100.0)
    reasons: list[str] = []
    missing_skills: list[str] = []


class OpportunityDiscoverRequest(StrictCamelModel):
    query: str = Field(min_length=2, max_length=200)
    type: str | None = Field(default=None, max_length=50)
    limit: int = Field(default=20, ge=1, le=50)


class ApplicationCreateRequest(StrictCamelModel):
    opportunity_id: UUID
    status: Literal["drafting", "saved"] = "drafting"


ApplicationStatusLiteral = Literal[
    "discovered",
    "saved",
    "evaluating",
    "eligible",
    "ineligible",
    "drafting",
    "ready_for_review",
    "approved",
    "submitted",
    "rejected",
    "accepted",
]


class ApplicationStatusUpdateRequest(StrictCamelModel):
    status: ApplicationStatusLiteral
    expected_status: ApplicationStatusLiteral


class ApplicationResponse(CamelModel):
    id: UUID
    user_id: UUID
    opportunity_id: UUID
    status: str
    applied_at: datetime | None = None
    submission_method: str
    created_at: datetime | None = None


class ApprovalRequestResponse(CamelModel):
    id: UUID
    session_id: UUID
    user_id: UUID
    opportunity_id: UUID
    action_type: str
    payload_summary: dict[str, Any]
    status: str
    user_decision_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime | None = None


class ApprovalDecisionRequest(StrictCamelModel):
    approved: bool
    rejection_reason: str | None = Field(default=None, max_length=1000)


class ApprovalDecisionResponse(CamelModel):
    approval_id: UUID
    user_id: UUID
    opportunity_id: UUID
    status: str
    user_decision_at: datetime | None = None


class NotificationResponse(CamelModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime | None = None


class VoiceTicketResponse(CamelModel):
    ticket: str
    expires_at: datetime
    ttl_seconds: int


class ResumeCreateRequest(StrictCamelModel):
    title: str = Field(min_length=1, max_length=255)
    master_content: dict[str, Any]

    @field_validator("title")
    @classmethod
    def _strip_non_empty_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be empty or whitespace")
        return stripped


class ResumeResponse(CamelModel):
    id: UUID
    user_id: UUID
    title: str
    master_content: dict[str, Any]
    created_at: datetime | None = None


class VoiceSessionCreateRequest(StrictCamelModel):
    detected_language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn"] = "en"
    audio_duration_seconds: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), le=Decimal("999999.99")
    )
    transcript: str | None = Field(default=None, max_length=20000)
    status: Literal["completed", "interrupted", "failed"] = "completed"


class VoiceSessionResponse(CamelModel):
    id: UUID
    user_id: UUID
    detected_language: str
    audio_duration_seconds: Decimal
    transcript: str | None = None
    status: str
    created_at: datetime | None = None
