"""Domain service for persistent voice session telemetry records."""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import VoiceSession
from app.repositories.profiles import ProfileRepository
from app.repositories.voice_sessions import VoiceSessionRepository
from app.schemas.common import VoiceSessionCreateRequest, VoiceSessionResponse

logger = logging.getLogger("opportunity_os.voice.sessions")


class VoiceSessionService:
    """Business logic for public.voice_sessions enforcing strict user ownership."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VoiceSessionRepository(session)
        self._profile_repo = ProfileRepository(session)

    async def create_session(
        self, user_id: UUID, payload: VoiceSessionCreateRequest
    ) -> VoiceSessionResponse:
        try:
            if await self._profile_repo.get_by_user_id(user_id) is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Profile Not Found",
                    detail="User profile must exist before recording a voice session.",
                )
            created = await self._repo.create_for_user(
                user_id,
                detected_language=payload.detected_language,
                audio_duration_seconds=payload.audio_duration_seconds,
                transcript=payload.transcript,
                status=payload.status,
            )
            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error while creating voice session.")
            raise ProblemDetailError(
                status_code=503,
                problem_type="urn:problem:service_unavailable",
                title="Service Unavailable",
                detail="Database is temporarily unavailable.",
            ) from exc
        return self._to_response(created)

    @staticmethod
    def _to_response(record: VoiceSession) -> VoiceSessionResponse:
        return VoiceSessionResponse(
            id=record.id,
            user_id=record.user_id,
            detected_language=record.detected_language or "en",
            audio_duration_seconds=record.audio_duration_seconds
            if record.audio_duration_seconds is not None
            else Decimal("0"),
            transcript=record.transcript,
            status=record.status or "completed",
            created_at=record.created_at,
        )
