"""Domain services for user profiles, student academic profiles & education records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.core.security import AuthenticatedUser
from app.models.entities import Education, Profile, StudentProfile
from app.repositories.profiles import ProfileRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    EducationCreateRequest,
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
            user_role=payload.user_role,
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
            user_role=profile.user_role or "student",
            supabase_role=supabase_role,
        )


class StudentProfileService:
    """Business logic for public.student_profiles and public.education."""

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
            current_academic_year=payload.current_academic_year,
            active_backlogs=payload.active_backlogs,
            experience_months=payload.experience_months,
            citizenship=payload.citizenship,
            skills=payload.skills,
            preferred_locations=payload.preferred_locations,
            open_to_relocate=payload.open_to_relocate,
        )
        await self._session.commit()
        refreshed = await self._repo.get_by_user_id(user_id)
        assert refreshed is not None
        return self._to_response(refreshed)

    async def list_education(self, user_id: UUID) -> list[EducationItemResponse]:
        rows = await self._repo.list_education_for_user(user_id)
        return [self._edu_to_response(ed) for ed in rows]

    async def add_education(
        self, user_id: UUID, payload: EducationCreateRequest
    ) -> EducationItemResponse:
        created = await self._repo.add_education_for_user(
            user_id,
            institution=payload.institution,
            degree=payload.degree,
            field_of_study=payload.field_of_study,
            start_year=payload.start_year,
            end_year=payload.end_year,
            score=payload.score,
        )
        if created is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Student Profile Not Found",
                detail="Create your student profile before adding education records.",
            )
        await self._session.commit()
        return self._edu_to_response(created)

    async def delete_education(self, user_id: UUID, education_id: UUID) -> None:
        deleted = await self._repo.delete_education_for_user(user_id, education_id)
        if not deleted:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Education Record Not Found",
                detail="Requested education record does not exist.",
            )
        await self._session.commit()

    @staticmethod
    def _edu_to_response(ed: Education) -> EducationItemResponse:
        return EducationItemResponse(
            id=ed.id,
            institution=ed.institution,
            degree=ed.degree,
            field_of_study=ed.field_of_study,
            start_year=ed.start_year,
            end_year=ed.end_year,
            score=ed.score,
        )

    @classmethod
    def _to_response(cls, student: StudentProfile) -> StudentProfileResponse:
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
            current_academic_year=student.current_academic_year,
            active_backlogs=student.active_backlogs if student.active_backlogs is not None else 0,
            experience_months=(
                student.experience_months if student.experience_months is not None else 0
            ),
            citizenship=student.citizenship,
            skills=list(student.skills or []),
            preferred_locations=list(student.preferred_locations or []),
            open_to_relocate=(
                True if student.open_to_relocate is None else bool(student.open_to_relocate)
            ),
            education=[cls._edu_to_response(ed) for ed in student.education_records],
        )
