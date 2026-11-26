"""Domain services for user profiles and student academic profiles."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.core.security import AuthenticatedUser
from app.models.entities import Profile, StudentProfile
from app.repositories.profiles import ProfileRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    EducationItemResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    StudentProfileResponse,
    StudentProfileUpsertRequest,
)


class ProfileService:
    """Business logic for public.profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProfileRepository(session)

    async def get_profile(self, current_user: AuthenticatedUser) -> ProfileResponse:
        profile = await self._repo.get_by_user_id(current_user.user_id)
        if profile is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Profile Not Found",
                detail="Authenticated user profile does not exist.",
            )
        return self._to_response(profile, current_user.supabase_role)

    async def update_profile(
        self, current_user: AuthenticatedUser, payload: ProfileUpdateRequest
    ) -> ProfileResponse:
        profile = await self._repo.update_by_user_id(
            current_user.user_id,
            full_name=payload.full_name,
            avatar_url=payload.avatar_url,
            preferred_language=payload.preferred_language,
        )
        if profile is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Profile Not Found",
                detail="Authenticated user profile does not exist.",
            )
        await self._session.commit()
        return self._to_response(profile, current_user.supabase_role)

    @staticmethod
    def _to_response(profile: Profile, supabase_role: str) -> ProfileResponse:
        return ProfileResponse(
            user_id=profile.id,
            email=profile.email,
            full_name=profile.full_name,
            avatar_url=profile.avatar_url,
            preferred_language=profile.preferred_language or "en",
            supabase_role=supabase_role,
        )


class StudentProfileService:
    """Business logic for public.student_profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = StudentProfileRepository(session)
        self._profile_repo = ProfileRepository(session)

    async def get_student_profile(self, user_id: UUID) -> StudentProfileResponse:
        student = await self._repo.get_by_user_id(user_id)
        if student is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Student Profile Not Found",
                detail="Student academic profile has not been created yet.",
            )
        return self._to_response(student)

    async def upsert_student_profile(
        self, user_id: UUID, payload: StudentProfileUpsertRequest
    ) -> StudentProfileResponse:
        parent_profile = await self._profile_repo.get_by_user_id(user_id)
        if parent_profile is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Profile Not Found",
                detail="Base user profile must exist before creating a student profile.",
            )
        await self._repo.upsert_for_user(
            user_id,
            college_name=payload.college_name,
            degree=payload.degree,
            branch=payload.branch,
            graduation_year=payload.graduation_year,
            cgpa=payload.cgpa,
            state=payload.state,
            bio=payload.bio,
        )
        await self._session.commit()
        refreshed = await self._repo.get_by_user_id(user_id)
        assert refreshed is not None
        return self._to_response(refreshed)

    @staticmethod
    def _to_response(student: StudentProfile) -> StudentProfileResponse:
        return StudentProfileResponse(
            id=student.id,
            user_id=student.user_id,
            college_name=student.college_name,
            degree=student.degree,
            branch=student.branch,
            graduation_year=student.graduation_year,
            cgpa=student.cgpa,
            state=student.state,
            bio=student.bio,
            education=[
                EducationItemResponse(
                    id=ed.id,
                    institution=ed.institution,
                    degree=ed.degree,
                    field_of_study=ed.field_of_study,
                    start_year=ed.start_year,
                    end_year=ed.end_year,
                    score=ed.score,
                )
                for ed in student.education_records
            ],
        )
