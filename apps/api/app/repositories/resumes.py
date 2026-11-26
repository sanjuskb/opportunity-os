"""Resume repository enforcing strict user ownership across resumes, versions & customizations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Resume, ResumeCustomization, ResumeVersion


class ResumeRepository:
    """Data access for public.resumes, public.resume_versions, and public.resume_customizations."""

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
        resume_id: UUID | None = None,
        title: str,
        master_content: dict[str, Any],
        storage_bucket: str | None = None,
        storage_path: str | None = None,
        original_filename: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        file_sha256: str | None = None,
        raw_text: str | None = None,
        extraction_status: str = "pending",
        extraction_confidence: Decimal | None = None,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            title=title,
            master_content=master_content,
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            file_sha256=file_sha256,
            raw_text=raw_text,
            extraction_status=extraction_status,
            extraction_confidence=extraction_confidence,
        )
        if resume_id is not None:
            resume.id = resume_id
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
        extraction_status: str | None = None,
        extraction_confidence: Decimal | None = None,
    ) -> Resume | None:
        resume = await self.get_for_user(resume_id, user_id)
        if resume is None:
            return None
        if title is not None:
            resume.title = title
        if master_content is not None:
            resume.master_content = master_content
        if extraction_status is not None:
            resume.extraction_status = extraction_status
        if extraction_confidence is not None:
            resume.extraction_confidence = extraction_confidence
        await self._session.flush()
        await self._session.refresh(resume)
        return resume

    async def delete_for_user(self, resume_id: UUID, user_id: UUID) -> bool:
        stmt = delete(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]

    async def next_version_number(self, resume_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(ResumeVersion.version_number), 0)).where(
            ResumeVersion.resume_id == resume_id
        )
        max_ver = (await self._session.execute(stmt)).scalar_one()
        return int(max_ver) + 1

    async def create_version(
        self,
        resume_id: UUID,
        *,
        version_number: int,
        content: dict[str, Any],
        pdf_url: str | None = None,
    ) -> ResumeVersion:
        version = ResumeVersion(
            resume_id=resume_id,
            version_number=version_number,
            content=content,
            pdf_url=pdf_url,
        )
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def list_versions(self, resume_id: UUID) -> list[ResumeVersion]:
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def create_customization(
        self,
        resume_id: UUID,
        opportunity_id: UUID,
        *,
        tailored_content: dict[str, Any],
        alignment_score: Decimal,
    ) -> ResumeCustomization:
        custom = ResumeCustomization(
            resume_id=resume_id,
            opportunity_id=opportunity_id,
            tailored_content=tailored_content,
            alignment_score=alignment_score,
        )
        self._session.add(custom)
        await self._session.flush()
        await self._session.refresh(custom)
        return custom

    async def list_customizations(self, resume_id: UUID) -> list[ResumeCustomization]:
        stmt = (
            select(ResumeCustomization)
            .where(ResumeCustomization.resume_id == resume_id)
            .order_by(ResumeCustomization.created_at.desc())
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all())
