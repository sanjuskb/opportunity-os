"""Student profile & education repository with explicit user_id ownership predicates."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
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
        await self._session.flush()
        await self._session.refresh(existing)
        return existing

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
