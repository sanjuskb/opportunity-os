"""Resume repository enforcing strict user ownership."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Resume


class ResumeRepository:
    """Data access for public.resumes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Resume]:
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(self, resume_id: UUID, user_id: UUID) -> Resume | None:
        stmt = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_for_user(
        self,
        user_id: UUID,
        *,
        title: str,
        master_content: dict[str, Any],
    ) -> Resume:
        resume = Resume(user_id=user_id, title=title, master_content=master_content)
        self._session.add(resume)
        await self._session.flush()
        await self._session.refresh(resume)
        return resume

    async def update_for_user(
        self,
        resume_id: UUID,
        user_id: UUID,
        *,
        title: str | None = None,
        master_content: dict[str, Any] | None = None,
    ) -> Resume | None:
        resume = await self.get_for_user(resume_id, user_id)
        if resume is None:
            return None
        if title is not None:
            resume.title = title
        if master_content is not None:
            resume.master_content = master_content
        await self._session.flush()
        await self._session.refresh(resume)
        return resume

    async def delete_for_user(self, resume_id: UUID, user_id: UUID) -> bool:
        stmt = delete(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]
