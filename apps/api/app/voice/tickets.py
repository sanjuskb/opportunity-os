"""Short-lived, single-use WebSocket ticket store for Voice Gateway authentication."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi.requests import HTTPConnection
from pydantic import BaseModel
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.errors import ProblemDetailError

logger = logging.getLogger("opportunity_os.voice.tickets")


class VoiceTicketPayload(BaseModel):
    """Authenticated metadata bound to a single-use voice WebSocket ticket."""

    ticket: str
    user_id: UUID
    issued_at: datetime
    expires_at: datetime


class VoiceTicketStore:
    """Atomic single-use ticket store backed by Redis with dev-only in-memory fallback."""

    _KEY_PREFIX = "voice:ticket:"

    def __init__(
        self,
        *,
        ttl_seconds: int | None = None,
        redis_client: Any | None = None,
        environment: str | None = None,
    ) -> None:
        self._ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.VOICE_TICKET_TTL_SECONDS
        self._redis = redis_client
        self._environment = (environment if environment is not None else settings.ENVIRONMENT).strip().lower()
        self._memory_store: dict[str, VoiceTicketPayload] = {}
        self._lock = asyncio.Lock()

    @property
    def is_production(self) -> bool:
        return self._environment == "production"

    async def issue_ticket(self, user_id: UUID) -> VoiceTicketPayload:
        """Issue a cryptographically random, short-lived ticket bound to user_id."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        ticket = secrets.token_urlsafe(32)
        payload = VoiceTicketPayload(
            ticket=ticket,
            user_id=user_id,
            issued_at=now,
            expires_at=expires_at,
        )

        if self._redis is not None:
            key = f"{self._KEY_PREFIX}{ticket}"
            try:
                await self._redis.set(key, payload.model_dump_json(), ex=self._ttl_seconds)
                return payload
            except RedisError as exc:
                logger.warning("Redis unavailable while issuing voice ticket.")
                if self.is_production:
                    raise ProblemDetailError(
                        status_code=503,
                        problem_type="urn:problem:service_unavailable",
                        title="Service Unavailable",
                        detail="Voice session service is temporarily unavailable.",
                    ) from exc
        elif self.is_production:
            logger.error("VoiceTicketStore missing Redis client in production.")
            raise ProblemDetailError(
                status_code=503,
                problem_type="urn:problem:service_unavailable",
                title="Service Unavailable",
                detail="Voice session service is not configured for production.",
            )

        async with self._lock:
            self._prune_expired_locked(now)
            self._memory_store[ticket] = payload
        return payload

    async def consume_ticket(self, ticket: str) -> VoiceTicketPayload | None:
        """Atomically validate and consume a ticket. Returns None if missing/expired/reused."""
        if not ticket:
            return None

        now = datetime.now(UTC)
        if self._redis is not None:
            key = f"{self._KEY_PREFIX}{ticket}"
            try:
                raw = await self._redis.getdel(key)
            except RedisError:
                logger.warning("Redis unavailable while consuming voice ticket.")
                return None

            if raw is None:
                return None
            payload = VoiceTicketPayload.model_validate(json.loads(raw))
            if payload.expires_at <= now:
                return None
            return payload

        if self.is_production:
            logger.error("VoiceTicketStore missing Redis client in production.")
            return None

        async with self._lock:
            self._prune_expired_locked(now)
            mem_payload: VoiceTicketPayload | None = (
                self._memory_store.pop(ticket) if ticket in self._memory_store else None
            )
            if mem_payload is None or mem_payload.expires_at <= now:
                return None
            return mem_payload

    def _prune_expired_locked(self, now: datetime) -> None:
        expired = [k for k, v in self._memory_store.items() if v.expires_at <= now]
        for k in expired:
            del self._memory_store[k]


_fallback_ticket_store = VoiceTicketStore()


def get_voice_ticket_store(connection: HTTPConnection) -> VoiceTicketStore:
    """FastAPI dependency returning app-scoped VoiceTicketStore for HTTP and WebSocket."""
    store = getattr(connection.app.state, "voice_ticket_store", None)
    if isinstance(store, VoiceTicketStore):
        return store
    return _fallback_ticket_store
