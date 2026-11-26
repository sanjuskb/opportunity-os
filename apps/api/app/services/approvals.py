"""Domain service for human-in-the-loop approval workflows."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import ApprovalRequest
from app.repositories.applications import ApplicationRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.notifications import NotificationRepository
from app.schemas.common import (
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalRequestResponse,
)


class ApprovalService:
    """Business logic for public.approval_requests and transactional state coordination."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ApprovalRepository(session)
        self._app_repo = ApplicationRepository(session)
        self._notif_repo = NotificationRepository(session)

    async def list_pending(self, user_id: UUID) -> list[ApprovalRequestResponse]:
        rows = await self._repo.list_pending_for_user(user_id)
        return [self._to_response(r) for r in rows]

    async def get_approval(self, approval_id: UUID, user_id: UUID) -> ApprovalRequestResponse:
        record = await self._repo.get_for_user(approval_id, user_id)
        if record is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Approval Request Not Found",
                detail="Requested approval does not exist.",
            )
        return self._to_response(record)

    async def decide_approval(
        self,
        approval_id: UUID,
        user_id: UUID,
        payload: ApprovalDecisionRequest,
    ) -> ApprovalDecisionResponse:
        """Atomically approve or reject a pending request owned by user_id.

        Updates the linked application status (approved/drafting) and creates a single
        in-DB notification within the same transaction. Never executes external actions.
        """
        existing = await self._repo.get_for_user(approval_id, user_id)
        if existing is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Approval Request Not Found",
                detail="Requested approval does not exist.",
            )
        if existing.status != "pending":
            raise ProblemDetailError(
                status_code=409,
                problem_type="urn:problem:conflict",
                title="Approval Already Resolved",
                detail=f"Approval request is already '{existing.status}' and cannot be re-decided.",
            )

        decided = await self._repo.decide_for_user(
            approval_id,
            user_id,
            approved=payload.approved,
            rejection_reason=payload.rejection_reason,
        )
        if decided is None:
            await self._session.rollback()
            raise ProblemDetailError(
                status_code=409,
                problem_type="urn:problem:conflict",
                title="Approval Already Resolved",
                detail="Approval request was resolved concurrently.",
            )

        # Coordinate linked application status within the same DB transaction
        linked_app = await self._app_repo.get_by_user_and_opportunity(
            user_id, decided.opportunity_id
        )
        if linked_app is not None and linked_app.status in (
            "ready_for_review",
            "drafting",
            "eligible",
        ):
            next_app_status = "approved" if payload.approved else "drafting"
            updated_app = await self._app_repo.transition_status_for_user(
                linked_app.id,
                user_id,
                expected_status=linked_app.status,
                new_status=next_app_status,
            )
            if updated_app is None:
                await self._session.rollback()
                raise ProblemDetailError(
                    status_code=409,
                    problem_type="urn:problem:conflict",
                    title="Concurrent Application Update",
                    detail=(
                        "Linked application status changed concurrently; "
                        "approval decision rolled back."
                    ),
                )

        # Because atomic decide_for_user succeeds at most once per approval_id,
        # this notification cannot be duplicated on retries or concurrent races.
        decision_label = "approved" if payload.approved else "rejected"
        await self._notif_repo.create_for_user(
            user_id,
            title=f"Action {decision_label.capitalize()}",
            message=f"Your {decided.action_type} request has been {decision_label}.",
            notif_type="approval_required",
        )

        await self._session.commit()
        return ApprovalDecisionResponse(
            approval_id=decided.id,
            user_id=decided.user_id,
            opportunity_id=decided.opportunity_id,
            status=decided.status or decision_label,
            user_decision_at=decided.user_decision_at,
        )

    @staticmethod
    def _to_response(record: ApprovalRequest) -> ApprovalRequestResponse:
        return ApprovalRequestResponse(
            id=record.id,
            session_id=record.session_id,
            user_id=record.user_id,
            opportunity_id=record.opportunity_id,
            action_type=record.action_type,
            payload_summary=dict(record.payload_summary or {}),
            status=record.status or "pending",
            user_decision_at=record.user_decision_at,
            rejection_reason=record.rejection_reason,
            created_at=record.created_at,
        )
