"""Student profile & education repository with explicit user_id ownership predicates."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Education, StudentProfile


class StudentProfileRepository:
    """Data access for public.student_profiles and public.education."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> StudentProfile | None:
        stmt = (
            select(StudentProfile)
            .where(StudentProfile.user_id == user_id)
            .options(
                selectinload(StudentProfile.education_records),
                selectinload(StudentProfile.career_passport),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_for_user(
        self,
        user_id: UUID,
        *,
        college_name: str,
        degree: str,
        branch: str,
        graduation_year: int,
        cgpa: Decimal | None = None,
        state: str | None = None,
        bio: str | None = None,
        current_academic_year: int | None = None,
        active_backlogs: int | None = None,
        experience_months: int | None = None,
        citizenship: str | None = None,
        skills: list[str] | None = None,
        preferred_locations: list[str] | None = None,
        open_to_relocate: bool | None = None,
    ) -> StudentProfile:
        existing = await self.get_by_user_id(user_id)
        if existing is None:
            existing = StudentProfile(
                user_id=user_id,
                college_name=college_name,
                degree=degree,
                branch=branch,
                graduation_year=graduation_year,
                cgpa=cgpa,
                state=state,
                bio=bio,
                current_academic_year=current_academic_year,
                active_backlogs=active_backlogs if active_backlogs is not None else 0,
                experience_months=experience_months if experience_months is not None else 0,
                citizenship=citizenship,
                skills=skills or [],
                preferred_locations=preferred_locations or [],
                open_to_relocate=True if open_to_relocate is None else open_to_relocate,
            )
            self._session.add(existing)
        else:
            existing.college_name = college_name
            existing.degree = degree
            existing.branch = branch
            existing.graduation_year = graduation_year
            existing.cgpa = cgpa
            existing.state = state
            existing.bio = bio
            if current_academic_year is not None:
                existing.current_academic_year = current_academic_year
            if active_backlogs is not None:
                existing.active_backlogs = active_backlogs
            if experience_months is not None:
                existing.experience_months = experience_months
            if citizenship is not None:
                existing.citizenship = citizenship
            if skills is not None:
                existing.skills = skills
            if preferred_locations is not None:
                existing.preferred_locations = preferred_locations
            if open_to_relocate is not None:
                existing.open_to_relocate = open_to_relocate
        await self._session.flush()
        await self._session.refresh(existing)
        return existing

    async def list_education_for_user(self, user_id: UUID) -> list[Education]:
        student = await self.get_by_user_id(user_id)
        if student is None:
            return []
        stmt = (
            select(Education)
            .where(Education.student_id == student.id)
            .order_by(Education.start_year.desc(), Education.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add_education_for_user(
        self,
        user_id: UUID,
        *,
        institution: str,
        degree: str,
        field_of_study: str,
        start_year: int,
        end_year: int | None = None,
        score: str | None = None,
    ) -> Education | None:
        student = await self.get_by_user_id(user_id)
        if student is None:
            return None
        record = Education(
            student_id=student.id,
            institution=institution,
            degree=degree,
            field_of_study=field_of_study,
            start_year=start_year,
            end_year=end_year,
            score=score,
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def delete_education_for_user(self, user_id: UUID, education_id: UUID) -> bool:
        student = await self.get_by_user_id(user_id)
        if student is None:
            return False
        stmt = delete(Education).where(
            Education.id == education_id,
            Education.student_id == student.id,
        )
        res = await self._session.execute(stmt)
        return (res.rowcount or 0) > 0  # type: ignore[attr-defined]
