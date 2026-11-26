"""Domain service for basic Resume CRUD management."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import Resume
from app.repositories.profiles import ProfileRepository
from app.repositories.resumes import ResumeRepository
from app.schemas.common import ResumeCreateRequest, ResumeResponse

logger = logging.getLogger("opportunity_os.resumes")


class ResumeService:
    """Business logic for public.resumes enforcing strict user ownership."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ResumeRepository(session)
        self._profile_repo = ProfileRepository(session)

    async def list_resumes(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ResumeResponse]:
        try:
            rows = await self._repo.list_for_user(user_id, limit=limit, offset=offset)
        except (SQLAlchemyError, OSError) as exc:
            logger.warning("Database error while listing resumes.")
            raise self._db_unavailable_error() from exc
        return [self._to_response(row) for row in rows]

    async def get_resume(self, resume_id: UUID, user_id: UUID) -> ResumeResponse:
        try:
            record = await self._repo.get_for_user(resume_id, user_id)
        except (SQLAlchemyError, OSError) as exc:
            logger.warning("Database error while fetching resume.")
            raise self._db_unavailable_error() from exc
        if record is None:
            raise self._not_found_error()
        return self._to_response(record)

    async def create_resume(self, user_id: UUID, payload: ResumeCreateRequest) -> ResumeResponse:
        try:
            if await self._profile_repo.get_by_user_id(user_id) is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Profile Not Found",
                    detail="User profile must exist before creating a resume.",
                )
            created = await self._repo.create_for_user(
                user_id,
                title=payload.title,
                master_content=payload.master_content,
            )
            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error while creating resume.")
            raise self._db_unavailable_error() from exc
        return self._to_response(created)

    async def delete_resume(self, resume_id: UUID, user_id: UUID) -> None:
        try:
            deleted = await self._repo.delete_for_user(resume_id, user_id)
            if not deleted:
                raise self._not_found_error()
            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error while deleting resume.")
            raise self._db_unavailable_error() from exc

    @staticmethod
    def _not_found_error() -> ProblemDetailError:
        return ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Resume Not Found",
            detail="Requested resume does not exist.",
        )

    @staticmethod
    def _db_unavailable_error() -> ProblemDetailError:
        return ProblemDetailError(
            status_code=503,
            problem_type="urn:problem:service_unavailable",
            title="Service Unavailable",
            detail="Database is temporarily unavailable.",
        )

    @staticmethod
    def _to_response(record: Resume) -> ResumeResponse:
        return ResumeResponse(
            id=record.id,
            user_id=record.user_id,
            title=record.title,
            master_content=dict(record.master_content or {}),
            created_at=record.created_at,
        )
