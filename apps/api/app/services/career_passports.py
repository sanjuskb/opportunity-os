"""Domain service for Career Passport management."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import CareerPassport
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import CareerPassportItemCreateRequest, CareerPassportResponse

_CATEGORIES = ("verified_achievements", "coursework", "certifications", "projects")


class CareerPassportService:
    """Business logic for public.career_passports."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CareerPassportRepository(session)
        self._student_repo = StudentProfileRepository(session)

    async def get_passport(self, user_id: UUID) -> CareerPassportResponse:
        passport = await self._repo.get_by_user_id(user_id)
        if passport is None:
            student = await self._student_repo.get_by_user_id(user_id)
            if student is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Student Profile Not Found",
                    detail="Create a student profile before accessing Career Passport.",
                )
            passport = await self._repo.upsert_for_user(user_id)
            assert passport is not None
            await self._session.commit()
        return self._to_response(passport)

    async def add_item(
        self, user_id: UUID, payload: CareerPassportItemCreateRequest
    ) -> CareerPassportResponse:
        passport = await self._repo.get_by_user_id(user_id)
        if passport is None:
            student = await self._student_repo.get_by_user_id(user_id)
            if student is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Student Profile Not Found",
                    detail="Create a student profile before adding Career Passport items.",
                )
            passport = await self._repo.upsert_for_user(user_id)
            assert passport is not None

        item_entry: dict[str, Any] = {**payload.data, "id": str(uuid4())}
        current_items: list[Any] = list(getattr(passport, payload.category) or [])
        current_items.append(item_entry)

        updated = await self._repo.upsert_for_user(
            user_id, **{payload.category: current_items}
        )
        assert updated is not None
        await self._session.commit()
        return self._to_response(updated)

    async def delete_item(self, user_id: UUID, item_id: str) -> CareerPassportResponse:
        passport = await self._repo.get_by_user_id(user_id)
        if passport is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Career Passport Not Found",
                detail="Career Passport does not exist for this user.",
            )

        removed = False
        updates: dict[str, list[Any]] = {}
        for category in _CATEGORIES:
            items = list(getattr(passport, category) or [])
            filtered = [item for item in items if not (isinstance(item, dict) and item.get("id") == item_id)]
            if len(filtered) != len(items):
                removed = True
                updates[category] = filtered

        if not removed:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Career Passport Item Not Found",
                detail="Requested Career Passport item was not found.",
            )

        updated = await self._repo.upsert_for_user(user_id, **updates)
        assert updated is not None
        await self._session.commit()
        return self._to_response(updated)

    @staticmethod
    def _to_response(passport: CareerPassport) -> CareerPassportResponse:
        return CareerPassportResponse(
            id=passport.id,
            student_id=passport.student_id,
            verified_achievements=list(passport.verified_achievements or []),
            coursework=list(passport.coursework or []),
            certifications=list(passport.certifications or []),
            projects=list(passport.projects or []),
            last_updated=passport.last_updated,
        )
