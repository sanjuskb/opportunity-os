"""Interview Simulator, Market Analytics, Company Portal & University Portal APIs."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy import desc, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.core.security import AuthenticatedUser, require_supabase_role
from app.core.security_middleware import rate_limit
from app.db.session import get_db_session
from app.integrations.gemini import GeminiClient
from app.integrations.olostep import validate_public_http_url
from app.models.entities import (
    AnalyticsEvent,
    Application,
    CareerPassport,
    InterviewSession,
    Notification,
    Opportunity,
    OpportunityEligibility,
    Profile,
    StudentProfile,
    UniversityVerification,
)
from app.repositories.profiles import ProfileRepository
from app.schemas.common import CamelModel, StrictCamelModel
from app.services.interview import evaluate_interview_answer, generate_interview_questions

portals_router = APIRouter(tags=["Portals, Interview & Analytics"])

_AuthenticatedUser = Annotated[AuthenticatedUser, Depends(require_supabase_role("authenticated"))]
_DbSession = Annotated[AsyncSession, Depends(get_db_session)]

logger = logging.getLogger("opportunity_os.portals")


async def _require_workspace_role(
    session: AsyncSession, user_id: UUID, allowed: tuple[str, ...]
) -> Profile:
    profile = await ProfileRepository(session).get_by_user_id(user_id)
    if profile is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Profile Not Found",
            detail="User profile must exist before accessing portal resources.",
        )
    role = profile.user_role or "student"
    if role not in allowed:
        raise ProblemDetailError(
            status_code=403,
            problem_type="urn:problem:forbidden",
            title="Role Access Restricted",
            detail=f"Current workspace role '{role}' cannot access this portal endpoint (requires {', '.join(allowed)}).",
        )
    return profile


# ---------------------------------------------------------------------------
# Interview Simulator
# ---------------------------------------------------------------------------


class InterviewSessionCreateRequest(StrictCamelModel):
    target_role: str = Field(min_length=2, max_length=200)
    language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu"] = "en"


class InterviewRespondRequest(StrictCamelModel):
    question_index: int = Field(ge=0, le=20)
    answer_text: str = Field(min_length=3, max_length=8000)


class InterviewSessionResponse(CamelModel):
    id: UUID
    user_id: UUID
    target_role: str
    language: str
    questions: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    feedback: list[dict[str, Any]] = []
    overall_score: float | None = None
    status: str
    created_at: datetime | None = None


def _to_interview_response(row: InterviewSession) -> InterviewSessionResponse:
    return InterviewSessionResponse(
        id=row.id,
        user_id=row.user_id,
        target_role=row.target_role,
        language=row.language or "en",
        questions=list(row.questions or []),
        responses=list(row.responses or []),
        feedback=list(row.feedback or []),
        overall_score=float(row.overall_score) if row.overall_score is not None else None,
        status=row.status or "in_progress",
        created_at=row.created_at,
    )


@portals_router.post(
    "/interview/sessions",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("interview", limit=20, window_seconds=60))],
)
async def create_interview_session(
    payload: InterviewSessionCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> InterviewSessionResponse:
    """Create a grounded technical mock interview session tailored to the student's target role."""
    profile = await ProfileRepository(session).get_by_user_id(current_user.user_id)
    if profile is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Profile Not Found",
            detail="User profile must exist before starting an interview session.",
        )

    questions = await generate_interview_questions(
        payload.target_role, payload.language, gemini_client=GeminiClient()
    )
    row = InterviewSession(
        user_id=current_user.user_id,
        target_role=payload.target_role,
        language=payload.language,
        questions=questions,
        responses=[],
        feedback=[],
        status="in_progress",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_interview_response(row)


@portals_router.get(
    "/interview/sessions",
    response_model=list[InterviewSessionResponse],
)
async def list_interview_sessions(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=15, ge=1, le=50),
) -> list[InterviewSessionResponse]:
    """List mock interview sessions owned by the authenticated student."""
    rows = list(
        (
            await session.execute(
                select(InterviewSession)
                .where(InterviewSession.user_id == current_user.user_id)
                .order_by(desc(InterviewSession.created_at))
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [_to_interview_response(r) for r in rows]


@portals_router.post(
    "/interview/sessions/{session_id}/respond",
    response_model=InterviewSessionResponse,
    dependencies=[Depends(rate_limit("interview", limit=30, window_seconds=60))],
)
async def submit_interview_response(
    session_id: UUID,
    payload: InterviewRespondRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> InterviewSessionResponse:
    """Submit a student answer for an interview question and receive Gemini/rubric feedback."""
    row = (
        await session.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == current_user.user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Interview Session Not Found",
            detail="Interview session does not exist for this user.",
        )
    questions = list(row.questions or [])
    if payload.question_index >= len(questions):
        raise ProblemDetailError(
            status_code=422,
            problem_type="urn:problem:validation_failed",
            title="Invalid Question Index",
            detail="Question index exceeds session question count.",
        )

    q_obj = questions[payload.question_index]
    eval_res = await evaluate_interview_answer(
        target_role=row.target_role,
        question=str(q_obj.get("question", "")),
        ideal_points=[str(x) for x in q_obj.get("idealPoints", [])],
        answer=payload.answer_text,
        language=row.language or "en",
        gemini_client=GeminiClient(),
    )

    responses = [
        r for r in (row.responses or []) if r.get("questionIndex") != payload.question_index
    ]
    responses.append(
        {
            "questionIndex": payload.question_index,
            "answerText": payload.answer_text,
            "submittedAt": datetime.now(UTC).isoformat(),
        }
    )
    feedback = [f for f in (row.feedback or []) if f.get("questionIndex") != payload.question_index]
    feedback.append(
        {
            "questionIndex": payload.question_index,
            "score": eval_res["score"],
            "summary": eval_res["summary"],
            "strengths": eval_res["strengths"],
            "improvements": eval_res["improvements"],
        }
    )
    scores = [float(f["score"]) for f in feedback if isinstance(f.get("score"), (int, float))]
    row.responses = responses
    row.feedback = feedback
    row.overall_score = Decimal(str(round(sum(scores) / len(scores), 2))) if scores else None
    row.status = "completed" if len(responses) >= len(questions) else "in_progress"
    await session.commit()
    await session.refresh(row)
    return _to_interview_response(row)


# ---------------------------------------------------------------------------
# Analytics & Telemetry
# ---------------------------------------------------------------------------


class AnalyticsEventCreateRequest(StrictCamelModel):
    event_name: str = Field(min_length=2, max_length=100)
    event_metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsOverviewResponse(CamelModel):
    total_opportunities: int
    total_applications: int
    applications_by_status: dict[str, int]
    top_skills: list[dict[str, Any]]
    top_locations: list[dict[str, Any]]
    recent_events_count: int


@portals_router.get(
    "/analytics/overview",
    response_model=AnalyticsOverviewResponse,
)
async def get_analytics_overview(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AnalyticsOverviewResponse:
    """Compute real database metrics for opportunities, applications, skills & locations."""
    opps = list(
        (await session.execute(select(Opportunity).where(Opportunity.is_active.is_(True))))
        .scalars()
        .all()
    )
    eligs = list((await session.execute(select(OpportunityEligibility))).scalars().all())
    apps = list(
        (
            await session.execute(
                select(Application).where(Application.user_id == current_user.user_id)
            )
        )
        .scalars()
        .all()
    )
    ev_count = int(
        (
            await session.execute(
                select(func.count(AnalyticsEvent.id)).where(
                    AnalyticsEvent.user_id == current_user.user_id
                )
            )
        ).scalar()
        or 0
    )

    skill_counts: Counter[str] = Counter()
    for el in eligs:
        for sk in el.required_skills or []:
            if isinstance(sk, str) and sk.strip():
                skill_counts[sk.strip()] += 1

    loc_counts: Counter[str] = Counter()
    for opp in opps:
        if opp.location:
            loc_counts[opp.location.split("/")[0].strip()] += 1

    app_status_counts: Counter[str] = Counter()
    for app in apps:
        app_status_counts[app.status or "drafting"] += 1

    return AnalyticsOverviewResponse(
        total_opportunities=len(opps),
        total_applications=len(apps),
        applications_by_status=dict(app_status_counts),
        top_skills=[{"skill": k, "count": v} for k, v in skill_counts.most_common(6)],
        top_locations=[{"location": k, "count": v} for k, v in loc_counts.most_common(6)],
        recent_events_count=ev_count,
    )


@portals_router.post(
    "/analytics/events",
    status_code=status.HTTP_201_CREATED,
)
async def record_analytics_event(
    payload: AnalyticsEventCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> dict[str, Any]:
    """Record a user-attributed telemetry event in public.analytics_events."""
    row = AnalyticsEvent(
        user_id=current_user.user_id,
        event_name=payload.event_name,
        event_metadata=payload.event_metadata,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": str(row.id), "eventName": row.event_name, "recorded": True}


# ---------------------------------------------------------------------------
# Company Recruiter Portal
# ---------------------------------------------------------------------------


class CompanyOpportunityCreateRequest(StrictCamelModel):
    title: str = Field(min_length=3, max_length=255)
    organization: str = Field(min_length=2, max_length=255)
    location: str = Field(min_length=2, max_length=200)
    type: Literal[
        "internship",
        "full_time",
        "scholarship",
        "hackathon",
        "fellowship",
        "government_scheme",
    ] = "internship"
    stipend_or_salary: str | None = Field(default=None, max_length=200)
    deadline: datetime | None = None
    description: str = Field(min_length=10, max_length=8000)
    source_url: str = Field(min_length=8, max_length=1000)
    required_skills: list[str] = Field(default_factory=list, max_length=30)
    eligible_batches: list[int] = Field(default_factory=list, max_length=10)
    eligible_degrees: list[str] = Field(default_factory=list, max_length=15)
    min_cgpa: float | None = Field(default=None, ge=0.0, le=10.0)


class RecruiterCandidateSummary(CamelModel):
    student_profile_id: UUID
    full_name: str
    college_name: str
    degree: str
    branch: str
    graduation_year: int
    cgpa: float | None = None
    skills: list[str] = []
    is_verified: bool = False


class CompanyApplicantItem(CamelModel):
    application_id: UUID
    opportunity_id: UUID
    opportunity_title: str
    candidate_name: str
    college_name: str
    cgpa: float | None = None
    status: str
    created_at: datetime | None = None


class AdvanceApplicationRequest(StrictCamelModel):
    status: Literal["evaluating", "eligible", "accepted", "rejected"] = "eligible"


@portals_router.post(
    "/company/opportunities",
    status_code=status.HTTP_201_CREATED,
)
async def create_company_opportunity(
    payload: CompanyOpportunityCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> dict[str, Any]:
    """Publish a verified opportunity directly from an authenticated Company workspace."""
    await _require_workspace_role(session, current_user.user_id, ("company",))
    try:
        safe_url = validate_public_http_url(payload.source_url)
    except ValueError as exc:
        raise ProblemDetailError(
            status_code=422,
            problem_type="urn:problem:validation_failed",
            title="Invalid Portal URL",
            detail=str(exc),
        ) from exc

    opp = Opportunity(
        title=payload.title,
        organization=payload.organization,
        location=payload.location,
        type=payload.type,
        description=payload.description,
        stipend_or_salary=payload.stipend_or_salary,
        deadline=payload.deadline,
        source_url=safe_url,
        source_provider="direct_portal",
        is_active=True,
    )
    session.add(opp)
    await session.flush()
    await session.refresh(opp)

    elig = OpportunityEligibility(
        opportunity_id=opp.id,
        required_skills=payload.required_skills,
        eligible_batches=payload.eligible_batches,
        eligible_degrees=payload.eligible_degrees,
        min_cgpa=Decimal(str(payload.min_cgpa)) if payload.min_cgpa is not None else None,
    )
    session.add(elig)
    await session.commit()
    return {
        "id": str(opp.id),
        "title": opp.title,
        "organization": opp.organization,
        "location": opp.location,
        "type": opp.type,
        "sourceUrl": opp.source_url,
    }


@portals_router.get(
    "/company/candidates",
    response_model=list[RecruiterCandidateSummary],
)
async def list_company_candidates(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[RecruiterCandidateSummary]:
    """List verified student talent profiles for Company recruiter discovery."""
    await _require_workspace_role(session, current_user.user_id, ("company", "university"))
    stmt = (
        select(StudentProfile, Profile, CareerPassport, UniversityVerification)
        .join(Profile, StudentProfile.user_id == Profile.id)
        .outerjoin(CareerPassport, CareerPassport.student_id == StudentProfile.id)
        .outerjoin(
            UniversityVerification,
            UniversityVerification.student_profile_id == StudentProfile.id,
        )
        .order_by(desc(StudentProfile.cgpa))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    results: list[RecruiterCandidateSummary] = []
    q_low = q.strip().lower() if q else ""
    for sp, prof, cp, ver in rows:
        skills = [str(s) for s in (sp.skills or [])]
        if cp and isinstance(cp.projects, list):
            for proj in cp.projects:
                if isinstance(proj, dict):
                    for t in proj.get("technologies", []):
                        if isinstance(t, str) and t not in skills:
                            skills.append(t)
        full_name = prof.full_name or "Verified Student"
        if (
            q_low
            and q_low not in full_name.lower()
            and q_low not in sp.college_name.lower()
            and q_low not in sp.branch.lower()
            and not any(q_low in sk.lower() for sk in skills)
        ):
            continue
        results.append(
            RecruiterCandidateSummary(
                student_profile_id=sp.id,
                full_name=full_name,
                college_name=sp.college_name,
                degree=sp.degree,
                branch=sp.branch,
                graduation_year=sp.graduation_year,
                cgpa=float(sp.cgpa) if sp.cgpa is not None else None,
                skills=skills,
                is_verified=(ver is not None and ver.status == "verified"),
            )
        )
    return results


@portals_router.get(
    "/company/applicants",
    response_model=list[CompanyApplicantItem],
)
async def list_company_applicants(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=30, ge=1, le=100),
) -> list[CompanyApplicantItem]:
    """List submitted/active student applications for recruiter review."""
    await _require_workspace_role(session, current_user.user_id, ("company",))
    stmt = (
        select(Application, Opportunity, Profile, StudentProfile)
        .join(Opportunity, Application.opportunity_id == Opportunity.id)
        .join(Profile, Application.user_id == Profile.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == Profile.id)
        .order_by(desc(Application.created_at))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        CompanyApplicantItem(
            application_id=app.id,
            opportunity_id=opp.id,
            opportunity_title=opp.title,
            candidate_name=prof.full_name or "Student Applicant",
            college_name=sp.college_name if sp else "Partner Institute",
            cgpa=float(sp.cgpa) if sp and sp.cgpa is not None else None,
            status=app.status or "drafting",
            created_at=app.created_at,
        )
        for app, opp, prof, sp in rows
    ]


@portals_router.patch(
    "/company/applications/{application_id}/advance",
    response_model=CompanyApplicantItem,
)
async def advance_company_application(
    application_id: UUID,
    payload: AdvanceApplicationRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> CompanyApplicantItem:
    """Advance an application status from the Company recruiter pipeline and notify candidate."""
    await _require_workspace_role(session, current_user.user_id, ("company",))
    app = await session.get(Application, application_id)
    if app is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Application Not Found",
            detail="Target application does not exist.",
        )
    await session.execute(
        update(Application).where(Application.id == application_id).values(status=payload.status)
    )
    session.add(
        Notification(
            user_id=app.user_id,
            title="Recruiter Status Update",
            message=f"Your application status was updated to '{payload.status}'.",
            type="application_status",
        )
    )
    await session.commit()
    opp = await session.get(Opportunity, app.opportunity_id)
    prof = await session.get(Profile, app.user_id)
    sp = (
        await session.execute(select(StudentProfile).where(StudentProfile.user_id == app.user_id))
    ).scalar_one_or_none()
    return CompanyApplicantItem(
        application_id=app.id,
        opportunity_id=app.opportunity_id,
        opportunity_title=opp.title if opp else "Role",
        candidate_name=prof.full_name if prof and prof.full_name else "Student Applicant",
        college_name=sp.college_name if sp else "Partner Institute",
        cgpa=float(sp.cgpa) if sp and sp.cgpa is not None else None,
        status=payload.status,
        created_at=app.created_at,
    )


# ---------------------------------------------------------------------------
# University Placement Portal
# ---------------------------------------------------------------------------


class UniversityOverviewResponse(CamelModel):
    total_students: int
    verified_students: int
    active_applications: int
    department_breakdown: list[dict[str, Any]]


class VerifyStudentRequest(StrictCamelModel):
    credential_type: str = Field(default="academic_transcript", max_length=100)
    notes: str | None = Field(default=None, max_length=500)


@portals_router.get(
    "/university/overview",
    response_model=UniversityOverviewResponse,
)
async def get_university_overview(
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> UniversityOverviewResponse:
    """Return placement cohort metrics and branch breakdown for the University portal."""
    await _require_workspace_role(session, current_user.user_id, ("university",))
    students = list((await session.execute(select(StudentProfile))).scalars().all())
    verified_cnt = int(
        (
            await session.execute(
                select(func.count(UniversityVerification.id)).where(
                    UniversityVerification.status == "verified"
                )
            )
        ).scalar()
        or 0
    )
    apps_cnt = int((await session.execute(select(func.count(Application.id)))).scalar() or 0)
    branch_counts: Counter[str] = Counter()
    for sp in students:
        branch_counts[sp.branch] += 1

    return UniversityOverviewResponse(
        total_students=len(students),
        verified_students=verified_cnt,
        active_applications=apps_cnt,
        department_breakdown=[
            {"department": branch, "students": count}
            for branch, count in branch_counts.most_common(10)
        ],
    )


@portals_router.get(
    "/university/students",
    response_model=list[RecruiterCandidateSummary],
)
async def list_university_students(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[RecruiterCandidateSummary]:
    """List student cohort directory and verification status for University officers."""
    await _require_workspace_role(session, current_user.user_id, ("university",))
    return await list_company_candidates(
        current_user=current_user, session=session, q=q, limit=limit
    )


@portals_router.post(
    "/university/students/{student_profile_id}/verify",
)
async def verify_university_student(
    student_profile_id: UUID,
    payload: VerifyStudentRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> dict[str, Any]:
    """Mark a student's academic transcript/CGPA verified via institutional review."""
    await _require_workspace_role(session, current_user.user_id, ("university",))
    sp = await session.get(StudentProfile, student_profile_id)
    if sp is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Student Profile Not Found",
            detail="Student profile does not exist.",
        )

    stmt = (
        pg_insert(UniversityVerification)
        .values(
            student_profile_id=student_profile_id,
            verified_by_user_id=current_user.user_id,
            status="verified",
            credential_type=payload.credential_type,
            notes=payload.notes,
        )
        .on_conflict_do_update(
            index_elements=["student_profile_id"],
            set_={
                "verified_by_user_id": current_user.user_id,
                "status": "verified",
                "credential_type": payload.credential_type,
                "notes": payload.notes,
                "verified_at": func.now(),
            },
        )
        .returning(UniversityVerification)
    )
    record = (await session.execute(stmt)).scalar_one()
    session.add(
        Notification(
            user_id=sp.user_id,
            title="Credential Institutionally Verified",
            message=f"Your {payload.credential_type.replace('_', ' ')} was verified by your placement cell.",
            type="verification",
        )
    )
    await session.commit()
    return {
        "id": str(record.id),
        "studentProfileId": str(student_profile_id),
        "status": record.status,
        "credentialType": record.credential_type,
    }
