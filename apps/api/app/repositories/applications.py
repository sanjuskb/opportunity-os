"""Application repository enforcing strict user ownership and uniqueness."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Application


class ApplicationRepository:
    """Data access for public.applications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Application]:
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc(), Application.id.desc())
            .limit(max(1, min(limit, 100)))
            .offset(max(0, offset))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, application_id: UUID, user_id: UUID) -> Application | None:
        stmt = select(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_opportunity(
        self, user_id: UUID, opportunity_id: UUID
    ) -> Application | None:
        stmt = select(Application).where(
            Application.user_id == user_id,
            Application.opportunity_id == opportunity_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_draft(
        self,
        user_id: UUID,
        opportunity_id: UUID,
        *,
        status: str = "drafting",
    ) -> Application:
        app_record = Application(
            user_id=user_id,
            opportunity_id=opportunity_id,
            status=status,
            submission_method="manual",
        )
        self._session.add(app_record)
        await self._session.flush()
        await self._session.refresh(app_record)
        return app_record

    async def update_status_for_user(
        self,
        application_id: UUID,
        user_id: UUID,
        *,
        status: str,
        submission_method: str | None = None,
        applied_at: datetime | None = None,
    ) -> Application | None:
        record = await self.get_for_user(application_id, user_id)
        if record is None:
            return None
        record.status = status
        if submission_method is not None:
            record.submission_method = submission_method
        if applied_at is not None:
            record.applied_at = applied_at
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def transition_status_for_user(
        self,
        application_id: UUID,
        user_id: UUID,
        *,
        expected_status: str,
        new_status: str,
        submission_method: str | None = None,
        applied_at: datetime | None = None,
    ) -> Application | None:
        """Atomically transition status only if current status matches expected_status."""
        values: dict[str, object] = {"status": new_status}
        if submission_method is not None:
            values["submission_method"] = submission_method
        if applied_at is not None:
            values["applied_at"] = applied_at

        stmt = (
            update(Application)
            .where(
                Application.id == application_id,
                Application.user_id == user_id,
                Application.status == expected_status,
            )
            .values(**values)
            .returning(Application)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_draft_for_user(self, application_id: UUID, user_id: UUID) -> bool:
        stmt = delete(Application).where(
            Application.id == application_id,
            Application.user_id == user_id,
            Application.status.in_(("drafting", "saved")),
        )
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]
