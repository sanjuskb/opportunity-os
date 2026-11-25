"""Domain service for application lifecycle tracking and state-machine enforcement."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import Application
from app.repositories.applications import ApplicationRepository
from app.repositories.opportunities import OpportunityRepository
from app.repositories.profiles import ProfileRepository
from app.schemas.common import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
)

# Client-allowed pre-approval state transitions.
# 'approved' can only be set by ApprovalService; 'submitted'/'accepted'/'rejected' only by backend workers.
_CLIENT_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "discovered": {"saved", "evaluating", "drafting"},
    "saved": {"evaluating", "drafting"},
    "evaluating": {"eligible", "ineligible", "drafting"},
    "eligible": {"drafting", "ready_for_review"},
    "drafting": {"ready_for_review", "saved"},
    "ready_for_review": {"drafting"},
}

_PRIVILEGED_TARGET_STATES = {"approved", "submitted", "rejected", "accepted"}


class ApplicationService:
    """Business logic for public.applications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ApplicationRepository(session)
        self._opp_repo = OpportunityRepository(session)
        self._profile_repo = ProfileRepository(session)

    async def list_applications(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ApplicationResponse]:
        rows = await self._repo.list_for_user(user_id, limit=limit, offset=offset)
        return [self._to_response(r) for r in rows]

    async def get_application(self, application_id: UUID, user_id: UUID) -> ApplicationResponse:
        record = await self._repo.get_for_user(application_id, user_id)
        if record is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Application Not Found",
                detail="Requested application does not exist.",
            )
        return self._to_response(record)

    async def create_application(
        self, user_id: UUID, payload: ApplicationCreateRequest
    ) -> ApplicationResponse:
        if await self._profile_repo.get_by_user_id(user_id) is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Profile Not Found",
                detail="User profile must exist before creating an application.",
            )
        if await self._opp_repo.get_by_id(payload.opportunity_id) is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Opportunity Not Found",
                detail="Target opportunity does not exist.",
            )

        try:
            created = await self._repo.create_draft(
                user_id, payload.opportunity_id, status=payload.status
            )
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ProblemDetailError(
                status_code=409,
                problem_type="urn:problem:conflict",
                title="Duplicate Application",
                detail="An application already exists for this opportunity.",
            ) from exc
        return self._to_response(created)

    async def update_status_by_client(
        self,
        application_id: UUID,
        user_id: UUID,
        payload: ApplicationStatusUpdateRequest,
    ) -> ApplicationResponse:
        target = payload.status
        if target in _PRIVILEGED_TARGET_STATES:
            raise ProblemDetailError(
                status_code=403,
                problem_type="urn:problem:forbidden",
                title="Approval Required",
                detail=f"Transitioning an application to '{target}' requires human approval or backend submission.",
            )

        record = await self._repo.get_for_user(application_id, user_id)
        if record is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Application Not Found",
                detail="Requested application does not exist.",
            )

        current_status = record.status or "drafting"
        if target == current_status:
            return self._to_response(record)

        allowed = _CLIENT_ALLOWED_TRANSITIONS.get(current_status, set())
        if target not in allowed:
            raise ProblemDetailError(
                status_code=422,
                problem_type="urn:problem:invalid_state_transition",
                title="Invalid Status Transition",
                detail=f"Cannot transition application from '{current_status}' to '{target}'.",
            )

        updated = await self._repo.update_status_for_user(
            application_id, user_id, status=target
        )
        assert updated is not None
        await self._session.commit()
        return self._to_response(updated)

    async def delete_draft(self, application_id: UUID, user_id: UUID) -> None:
        record = await self._repo.get_for_user(application_id, user_id)
        if record is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Application Not Found",
                detail="Requested application does not exist.",
            )

        deleted = await self._repo.delete_draft_for_user(application_id, user_id)
        if not deleted:
            raise ProblemDetailError(
                status_code=409,
                problem_type="urn:problem:conflict",
                title="Cannot Delete Active Application",
                detail="Only applications in 'drafting' or 'saved' status can be deleted.",
            )
        await self._session.commit()

    @staticmethod
    def _to_response(record: Application) -> ApplicationResponse:
        return ApplicationResponse(
            id=record.id,
            user_id=record.user_id,
            opportunity_id=record.opportunity_id,
            status=record.status or "drafting",
            applied_at=record.applied_at,
            submission_method=record.submission_method or "manual",
            created_at=record.created_at,
        )
