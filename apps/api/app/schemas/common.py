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
    user_role: str = "student"
    supabase_role: str


class ProfileUpdateRequest(StrictCamelModel):
    full_name: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)
    preferred_language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu"] | None = None
    user_role: Literal["student", "company", "university"] | None = None


class EducationCreateRequest(StrictCamelModel):
    institution: str = Field(min_length=2, max_length=200)
    degree: str = Field(min_length=1, max_length=100)
    field_of_study: str = Field(min_length=1, max_length=150)
    start_year: int = Field(ge=1990, le=2035)
    end_year: int | None = Field(default=None, ge=1990, le=2038)
    score: str | None = Field(default=None, max_length=40)


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
    current_academic_year: int | None = None
    active_backlogs: int = 0
    experience_months: int = 0
    citizenship: str | None = None
    skills: list[str] = []
    preferred_locations: list[str] = []
    open_to_relocate: bool = True
    education: list[EducationItemResponse] = []


class StudentProfileUpsertRequest(StrictCamelModel):
    college_name: str = Field(min_length=2, max_length=200)
    degree: str = Field(min_length=2, max_length=100)
    branch: str = Field(min_length=2, max_length=120)
    graduation_year: int = Field(ge=2020, le=2035)
    cgpa: Decimal | None = Field(default=None, ge=Decimal("0.00"), le=Decimal("10.00"))
    state: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    current_academic_year: int | None = Field(default=None, ge=1, le=6)
    active_backlogs: int | None = Field(default=None, ge=0, le=50)
    experience_months: int | None = Field(default=None, ge=0, le=240)
    citizenship: str | None = Field(default=None, max_length=80)
    skills: list[str] | None = Field(default=None, max_length=100)
    preferred_locations: list[str] | None = Field(default=None, max_length=50)
    open_to_relocate: bool | None = None


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
    eligible_academic_years: list[int] = []
    min_cgpa: Decimal | None = None
    max_active_backlogs: int | None = None
    min_experience_months: int | None = None
    allowed_locations: list[str] = []
    remote_allowed: bool = True
    required_citizenship: str | None = None
    preferred_skills: list[str] = []
    match_score: float | None = None
    semantic_score: float | None = None
    is_eligible: bool | None = None
    match_reasons: list[str] = []
    matched_skills: list[str] = []
    missing_skills: list[str] = []


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


class DeterministicChecksSummary(CamelModel):
    batch_matched: bool = True
    degree_matched: bool = True
    cgpa_matched: bool = True
    backlogs_matched: bool = True
    location_matched: bool = True
    deadline_active: bool = True


class SkillOverlapSummary(CamelModel):
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    preferred_matched: list[str] = []


class EligibilityCheckResponse(CamelModel):
    opportunity_id: str
    student_id: str
    is_eligible: bool
    status: Literal["eligible", "ineligible", "needs_more_info"] = "needs_more_info"
    score: float = Field(ge=0.0, le=100.0)
    reasons: list[str] = []
    missing_skills: list[str] = []
    explanation: str = ""
    semantic_similarity: float | None = None
    deterministic_checks: DeterministicChecksSummary = Field(
        default_factory=DeterministicChecksSummary
    )
    skill_overlap: SkillOverlapSummary = Field(default_factory=SkillOverlapSummary)


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
    execute_submission: bool = False


class ApprovalDecisionResponse(CamelModel):
    approval_id: UUID
    user_id: UUID
    opportunity_id: UUID
    status: str
    user_decision_at: datetime | None = None
    workflow_resumed: bool = False
    resumed_stage: str | None = None
    submission_status: str | None = None


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
    storage_bucket: str | None = None
    storage_path: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    file_size_bytes: int | None = None
    file_sha256: str | None = None
    extraction_status: str | None = None
    extraction_confidence: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResumeVersionResponse(CamelModel):
    id: UUID
    resume_id: UUID
    version_number: int
    content: dict[str, Any]
    pdf_url: str | None = None
    created_at: datetime | None = None


class ResumeDownloadUrlResponse(CamelModel):
    resume_id: UUID
    storage_bucket: str | None = None
    storage_path: str | None = None
    signed_url: str | None = None
    fallback_pdf_endpoint: str


class ResumeAnalyzeRequest(StrictCamelModel):
    opportunity_id: UUID | None = None


class ResumeAnalyzeResponse(CamelModel):
    resume_id: UUID
    opportunity_id: UUID | None = None
    completeness_score: float = Field(ge=0.0, le=100.0)
    extracted_skills: list[str] = []
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []


class ResumeTailorRequest(StrictCamelModel):
    opportunity_id: UUID
    custom_focus: str | None = Field(default=None, max_length=500)
    candidate_claims: list[str] = Field(default_factory=list, max_length=20)


class ResumeCustomizationResponse(CamelModel):
    id: UUID
    resume_id: UUID
    opportunity_id: UUID
    version_number: int
    alignment_score: float = Field(ge=0.0, le=100.0)
    tailored_content: dict[str, Any]
    verified_claims: list[dict[str, Any]] = []
    rejected_claims: list[dict[str, Any]] = []
    created_at: datetime | None = None


class ResearchDiscoverRequest(StrictCamelModel):
    query: str = Field(min_length=2, max_length=200)
    target_url: str | None = Field(default=None, max_length=1000)
    limit: int = Field(default=10, ge=1, le=25)
    enrich_companies: bool = False


class ResearchDiscoverResponse(CamelModel):
    query: str
    discovered_count: int
    deduplicated_count: int
    opportunities: list[OpportunityResponse] = []
    sources_recorded: list[str] = []
    usage_stats: dict[str, int] = {}


class CompanyEnrichRequest(StrictCamelModel):
    domain: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    force_refresh: bool = False


class OrganizationResponse(CamelModel):
    id: UUID
    name: str
    domain: str | None = None
    industry: str | None = None
    headcount_range: str | None = None
    funding_stage: str | None = None
    description: str | None = None
    hiring_velocity_score: float | None = None
    is_verified: bool = False
    last_enriched_at: datetime | None = None


class MonitorCreateRequest(StrictCamelModel):
    target_organization: str = Field(min_length=2, max_length=255)
    target_url: str | None = Field(default=None, max_length=1000)
    frequency: Literal["hourly", "daily", "weekly"] = "daily"
    criteria: dict[str, Any] = Field(default_factory=dict)


class MonitorResponse(CamelModel):
    id: UUID
    user_id: UUID
    target_organization: str
    criteria: dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime | None = None


class VoiceSessionCreateRequest(StrictCamelModel):
    detected_language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu"] = "en"
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


class AiChatRequest(StrictCamelModel):
    message: str = Field(min_length=1, max_length=4000)
    language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu", "hinglish"] = "en"
    conversation_id: UUID | None = None


class AiChatResponse(CamelModel):
    conversation_id: UUID
    language: str
    reply: str
    provider: str
    model: str
    tool_calls: list[dict[str, Any]] = []


class ConversationSummaryResponse(CamelModel):
    id: UUID
    title: str
    created_at: datetime | None = None


class ConversationMessageResponse(CamelModel):
    id: UUID
    role: str
    content: str
    language: str
    created_at: datetime | None = None


class ConversationDetailResponse(CamelModel):
    id: UUID
    title: str
    created_at: datetime | None = None
    messages: list[ConversationMessageResponse] = []
