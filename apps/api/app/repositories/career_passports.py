"""Career Passport repository enforcing user ownership via StudentProfile."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import CareerPassport, StudentProfile


class CareerPassportRepository:
    """Data access for public.career_passports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> CareerPassport | None:
        stmt = (
            select(CareerPassport)
            .join(StudentProfile, CareerPassport.student_id == StudentProfile.id)
            .where(StudentProfile.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_for_user(
        self,
        user_id: UUID,
        *,
        verified_achievements: list[Any] | None = None,
        coursework: list[Any] | None = None,
        certifications: list[Any] | None = None,
        projects: list[Any] | None = None,
    ) -> CareerPassport | None:
        student_stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        student = (await self._session.execute(student_stmt)).scalar_one_or_none()
        if student is None:
            return None

        passport = await self.get_by_user_id(user_id)
        if passport is None:
            passport = CareerPassport(
                student_id=student.id,
                verified_achievements=verified_achievements or [],
                coursework=coursework or [],
                certifications=certifications or [],
                projects=projects or [],
            )
            self._session.add(passport)
        else:
            if verified_achievements is not None:
                passport.verified_achievements = verified_achievements
            if coursework is not None:
                passport.coursework = coursework
            if certifications is not None:
                passport.certifications = certifications
            if projects is not None:
                passport.projects = projects
            passport.last_updated = datetime.now(UTC)

        await self._session.flush()
        await self._session.refresh(passport)
        return passport
