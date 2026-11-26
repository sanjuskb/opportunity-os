"""Voice session repository enforcing strict user ownership."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import VoiceSession


class VoiceSessionRepository:
    """Data access for public.voice_sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_for_user(
        self,
        user_id: UUID,
        *,
        detected_language: str = "en",
        audio_duration_seconds: Decimal = Decimal("0"),
        transcript: str | None = None,
        status: str = "completed",
    ) -> VoiceSession:
        record = VoiceSession(
            user_id=user_id,
            detected_language=detected_language,
            audio_duration_seconds=audio_duration_seconds,
            transcript=transcript,
            status=status,
        )
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VoiceSession]:
        stmt = (
            select(VoiceSession)
            .where(VoiceSession.user_id == user_id)
            .order_by(VoiceSession.created_at.desc(), VoiceSession.id.desc())
            .limit(max(1, min(limit, 100)))
            .offset(max(0, offset))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
