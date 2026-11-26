import asyncio
import logging
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ml import eligibility_router, ml_router
from app.api.v1.voice import voice_router
from app.core.config import settings
from app.core.security import AuthenticatedUser, require_supabase_role
from app.db.session import DatabaseManager, check_db_health, get_db_session
from app.schemas.common import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalRequestResponse,
    CareerPassportItemCreateRequest,
    CareerPassportResponse,
    EligibilityCheckResponse,
    EligibilityEvaluateRequest,
    HealthResponse,
    NotificationResponse,
    OpportunityDiscoverRequest,
    OpportunityResponse,
    PaginatedOpportunitiesResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ReadinessDependencies,
    ReadinessResponse,
    ResumeCreateRequest,
    ResumeResponse,
    SaveOpportunityRequest,
    SaveOpportunityResponse,
    StudentProfileResponse,
    StudentProfileUpsertRequest,
)
from app.services import (
    ApplicationService,
    ApprovalService,
    CareerPassportService,
    NotificationService,
    OpportunityService,
    ProfileService,
    ResumeService,
    StudentProfileService,
)

_logger = logging.getLogger("opportunity_os.health")

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(voice_router)
v1_router.include_router(ml_router)
v1_router.include_router(eligibility_router)

_AuthenticatedUser = Annotated[AuthenticatedUser, Depends(require_supabase_role("authenticated"))]
_DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _check_redis_health(redis_client: Any | None, timeout_seconds: float = 2.0) -> bool:
    if redis_client is None:
        return False
    try:
        return bool(await asyncio.wait_for(redis_client.ping(), timeout=timeout_seconds))
    except (RedisError, OSError, TimeoutError):
        _logger.warning("Redis readiness check failed.")
        return False


@v1_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Liveness check confirming the FastAPI process is running."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


@v1_router.get("/health/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_check(request: Request, response: Response) -> ReadinessResponse:
    """Readiness check verifying live PostgreSQL and Redis connectivity."""
    db_manager: DatabaseManager | None = getattr(request.app.state, "db", None)
    redis_client: Any | None = getattr(request.app.state, "redis_client", None)

    db_ok = await check_db_health(db_manager) if db_manager is not None else False
    redis_ok = await _check_redis_health(redis_client)

    all_healthy = db_ok and redis_ok
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if all_healthy else "degraded",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
        dependencies=ReadinessDependencies(
            database="healthy" if db_ok else "unavailable",
            redis="healthy" if redis_ok else "unavailable",
        ),
    )


# ---------------------------------------------------------------------------
# User & Student Profile APIs
# ---------------------------------------------------------------------------


@v1_router.get("/users/me", response_model=ProfileResponse, tags=["Users"])
async def get_me(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ProfileResponse:
    """Fetch the authenticated user's profile derived strictly from JWT sub."""
    return await ProfileService(session).get_profile(current_user)


@v1_router.put("/users/me", response_model=ProfileResponse, tags=["Users"])
async def update_me(
    payload: ProfileUpdateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ProfileResponse:
    """Update editable profile fields (email cannot be modified here)."""
    return await ProfileService(session).update_profile(current_user, payload)


@v1_router.get(
    "/users/me/student-profile",
    response_model=StudentProfileResponse,
    tags=["Users"],
)
async def get_my_student_profile(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> StudentProfileResponse:
    """Fetch the authenticated student's academic profile and education records."""
    return await StudentProfileService(session).get_student_profile(current_user.user_id)


@v1_router.put(
    "/users/me/student-profile",
    response_model=StudentProfileResponse,
    tags=["Users"],
)
async def upsert_my_student_profile(
    payload: StudentProfileUpsertRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> StudentProfileResponse:
    """Create or update the authenticated student's academic profile."""
    return await StudentProfileService(session).upsert_student_profile(
        current_user.user_id, payload
    )


# ---------------------------------------------------------------------------
# Career Passport APIs
# ---------------------------------------------------------------------------


@v1_router.get("/career-passport", response_model=CareerPassportResponse, tags=["Career Passport"])
async def get_career_passport(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> CareerPassportResponse:
    """Fetch the authenticated student's Career Passport."""
    return await CareerPassportService(session).get_passport(current_user.user_id)


@v1_router.post(
    "/career-passport/items",
    response_model=CareerPassportResponse,
    tags=["Career Passport"],
)
async def add_career_passport_item(
    payload: CareerPassportItemCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> CareerPassportResponse:
    """Add a verified achievement, coursework, certification, or project item."""
    return await CareerPassportService(session).add_item(current_user.user_id, payload)


@v1_router.delete(
    "/career-passport/items/{item_id}",
    response_model=CareerPassportResponse,
    tags=["Career Passport"],
)
async def delete_career_passport_item(
    item_id: str,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> CareerPassportResponse:
    """Remove an item from the authenticated student's Career Passport."""
    return await CareerPassportService(session).delete_item(current_user.user_id, item_id)


# ---------------------------------------------------------------------------
# Opportunity Discovery & Bookmark APIs
# ---------------------------------------------------------------------------


@v1_router.get(
    "/opportunities",
    response_model=PaginatedOpportunitiesResponse,
    tags=["Opportunities"],
)
async def list_opportunities(
    session: _DbSession,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = Query(default=None, alias="type"),  # noqa: A002
    q: str | None = Query(default=None, min_length=1, max_length=200),
    active_only: bool = Query(default=True),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
) -> PaginatedOpportunitiesResponse:
    """Return cursor-paginated, filterable opportunities from PostgreSQL."""
    return await OpportunityService(session).list_opportunities(
        cursor=cursor,
        limit=limit,
        opp_type=type,
        search_query=q,
        active_only=active_only,
        sort_order=sort_order,
    )


@v1_router.get(
    "/opportunities/saved",
    response_model=list[OpportunityResponse],
    tags=["Opportunities"],
)
async def list_saved_opportunities(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    active_only: bool = Query(default=True),
) -> list[OpportunityResponse]:
    """List opportunities saved by the authenticated user."""
    return await OpportunityService(session).list_saved_opportunities(
        current_user.user_id, limit=limit, offset=offset, active_only=active_only
    )


@v1_router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityResponse,
    tags=["Opportunities"],
)
async def get_opportunity_detail(
    opportunity_id: UUID,
    session: _DbSession,
) -> OpportunityResponse:
    """Fetch a single opportunity with eligibility criteria."""
    return await OpportunityService(session).get_opportunity(opportunity_id)


@v1_router.post(
    "/opportunities/discover",
    response_model=PaginatedOpportunitiesResponse,
    tags=["Opportunities"],
)
async def discover_opportunities(
    payload: OpportunityDiscoverRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> PaginatedOpportunitiesResponse:
    """Authenticated search over vetted database opportunities."""
    _ = current_user.user_id
    return await OpportunityService(session).list_opportunities(
        limit=payload.limit,
        opp_type=payload.type,
        search_query=payload.query,
        active_only=True,
    )


@v1_router.post(
    "/opportunities/{opportunity_id}/save",
    response_model=SaveOpportunityResponse,
    tags=["Opportunities"],
)
async def save_opportunity(
    opportunity_id: UUID,
    payload: SaveOpportunityRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> SaveOpportunityResponse:
    """Bookmark or unbookmark an opportunity for the authenticated user."""
    return await OpportunityService(session).toggle_save(
        current_user.user_id, opportunity_id, payload
    )


# ---------------------------------------------------------------------------
# Applications, Approvals & Notifications APIs
# ---------------------------------------------------------------------------


@v1_router.get("/applications", response_model=list[ApplicationResponse], tags=["Applications"])
async def list_applications(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ApplicationResponse]:
    """List applications owned by the authenticated user."""
    return await ApplicationService(session).list_applications(
        current_user.user_id, limit=limit, offset=offset
    )


@v1_router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Applications"],
)
async def create_application(
    payload: ApplicationCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ApplicationResponse:
    """Create a draft/saved application for the authenticated user."""
    return await ApplicationService(session).create_application(current_user.user_id, payload)


@v1_router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    tags=["Applications"],
)
async def get_application(
    application_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ApplicationResponse:
    """Fetch a single application owned by the authenticated user."""
    return await ApplicationService(session).get_application(application_id, current_user.user_id)


@v1_router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
    tags=["Applications"],
)
async def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ApplicationResponse:
    """Transition an application through allowed pre-approval draft statuses."""
    return await ApplicationService(session).update_status_by_client(
        application_id, current_user.user_id, payload
    )


@v1_router.delete(
    "/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Applications"],
)
async def delete_application(
    application_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> None:
    """Delete a draft/saved application owned by the authenticated user."""
    await ApplicationService(session).delete_draft(application_id, current_user.user_id)


@v1_router.get(
    "/agents/approvals/pending",
    response_model=list[ApprovalRequestResponse],
    tags=["Agents"],
)
async def list_pending_approvals(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> list[ApprovalRequestResponse]:
    """List pending human-in-the-loop approval requests for the authenticated user."""
    return await ApprovalService(session).list_pending(current_user.user_id)


@v1_router.get(
    "/agents/approvals/{approval_id}",
    response_model=ApprovalRequestResponse,
    tags=["Agents"],
)
async def get_approval_detail(
    approval_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ApprovalRequestResponse:
    """Fetch a single approval request owned by the authenticated user."""
    return await ApprovalService(session).get_approval(approval_id, current_user.user_id)


@v1_router.post(
    "/agents/approvals/{approval_id}/decision",
    response_model=ApprovalDecisionResponse,
    tags=["Agents"],
)
async def decide_approval(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ApprovalDecisionResponse:
    """Atomically approve or reject a pending approval request owned by current_user."""
    return await ApprovalService(session).decide_approval(
        approval_id, current_user.user_id, payload
    )


@v1_router.get(
    "/notifications",
    response_model=list[NotificationResponse],
    tags=["Notifications"],
)
async def list_notifications(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationResponse]:
    """List notifications for the authenticated user."""
    return await NotificationService(session).list_notifications(
        current_user.user_id, unread_only=unread_only, limit=limit, offset=offset
    )


@v1_router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> NotificationResponse:
    """Mark a notification owned by the authenticated user as read."""
    return await NotificationService(session).mark_read(notification_id, current_user.user_id)


# ---------------------------------------------------------------------------
# Eligibility Endpoint (Pending ML Integration)
# ---------------------------------------------------------------------------


@v1_router.post(
    "/eligibility/evaluate",
    response_model=EligibilityCheckResponse,
    tags=["Eligibility"],
)
async def evaluate_eligibility(
    payload: EligibilityEvaluateRequest,
    current_user: _AuthenticatedUser,
) -> EligibilityCheckResponse:
    """Evaluate eligibility for the authenticated student (identity from JWT sub only)."""
    return EligibilityCheckResponse(
        opportunity_id=str(payload.opportunity_id),
        student_id=str(current_user.user_id),
        is_eligible=False,
        score=0.0,
        reasons=["Profile evaluation pending ML integration."],
        missing_skills=[],
    )


# ---------------------------------------------------------------------------
# Resumes (Basic CRUD)
# ---------------------------------------------------------------------------


@v1_router.get("/resumes", response_model=list[ResumeResponse], tags=["Resumes"])
async def list_resumes(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ResumeResponse]:
    """List resumes owned by the authenticated user."""
    return await ResumeService(session).list_resumes(
        current_user.user_id, limit=limit, offset=offset
    )


@v1_router.post(
    "/resumes",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resumes"],
)
async def create_resume(
    payload: ResumeCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ResumeResponse:
    """Create a resume record owned by the authenticated user."""
    return await ResumeService(session).create_resume(current_user.user_id, payload)


@v1_router.get(
    "/resumes/{resume_id}",
    response_model=ResumeResponse,
    tags=["Resumes"],
)
async def get_resume(
    resume_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> ResumeResponse:
    """Fetch a single resume owned by the authenticated user."""
    return await ResumeService(session).get_resume(resume_id, current_user.user_id)


@v1_router.delete(
    "/resumes/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Resumes"],
)
async def delete_resume(
    resume_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> None:
    """Delete a resume owned by the authenticated user."""
    await ResumeService(session).delete_resume(resume_id, current_user.user_id)
