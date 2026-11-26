"""Profile repository with explicit user_id ownership predicates."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Profile


class ProfileRepository:
    """Data access for public.profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> Profile | None:
        stmt = select(Profile).where(Profile.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_user_id(
        self,
        user_id: UUID,
        *,
        full_name: str | None = None,
        avatar_url: str | None = None,
        preferred_language: str | None = None,
    ) -> Profile | None:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            return None
        if full_name is not None:
            profile.full_name = full_name
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        if preferred_language is not None:
            profile.preferred_language = preferred_language
        await self._session.flush()
        await self._session.refresh(profile)
        return profile
