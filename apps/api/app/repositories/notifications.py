"""Notification repository enforcing explicit user ownership."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Notification


class NotificationRepository:
    """Data access for public.notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = (
            stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(max(1, min(limit, 100)))
            .offset(max(0, offset))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_for_user(
        self,
        user_id: UUID,
        *,
        title: str,
        message: str,
        notif_type: str = "opportunity_match",
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            is_read=False,
        )
        self._session.add(notif)
        await self._session.flush()
        await self._session.refresh(notif)
        return notif

    async def mark_read_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
            .returning(Notification)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
