"""Approval request repository enforcing user ownership and pending-state transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ApprovalRequest


class ApprovalRepository:
    """Data access for public.approval_requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_pending_for_user(self, user_id: UUID) -> list[ApprovalRequest]:
        stmt = (
            select(ApprovalRequest)
            .where(
                ApprovalRequest.user_id == user_id,
                ApprovalRequest.status == "pending",
            )
            .order_by(ApprovalRequest.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, approval_id: UUID, user_id: UUID) -> ApprovalRequest | None:
        stmt = select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def decide_for_user(
        self,
        approval_id: UUID,
        user_id: UUID,
        *,
        approved: bool,
        rejection_reason: str | None = None,
    ) -> ApprovalRequest | None:
        """Atomically transition a pending approval owned by user_id."""
        new_status = "approved" if approved else "rejected"
        stmt = (
            update(ApprovalRequest)
            .where(
                ApprovalRequest.id == approval_id,
                ApprovalRequest.user_id == user_id,
                ApprovalRequest.status == "pending",
            )
            .values(
                status=new_status,
                user_decision_at=datetime.now(UTC),
                rejection_reason=None if approved else rejection_reason,
            )
            .returning(ApprovalRequest)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
