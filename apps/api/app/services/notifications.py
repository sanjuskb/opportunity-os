"""Domain service for user notifications."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import Notification
from app.repositories.notifications import NotificationRepository
from app.schemas.common import NotificationResponse


class NotificationService:
    """Business logic for public.notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def list_notifications(
        self,
        user_id: UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NotificationResponse]:
        rows = await self._repo.list_for_user(
            user_id, unread_only=unread_only, limit=limit, offset=offset
        )
        return [self._to_response(r) for r in rows]

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> NotificationResponse:
        updated = await self._repo.mark_read_for_user(notification_id, user_id)
        if updated is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Notification Not Found",
                detail="Requested notification does not exist.",
            )
        await self._session.commit()
        return self._to_response(updated)

    @staticmethod
    def _to_response(record: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=record.id,
            user_id=record.user_id,
            title=record.title,
            message=record.message,
            type=record.type or "opportunity_match",
            is_read=bool(record.is_read) if record.is_read is not None else False,
            created_at=record.created_at,
        )
