"""Agent-ready state contracts, telemetry schemas, and checkpoint configuration helpers.

NOTE: Full autonomous LangGraph multi-agent execution is intentionally deferred pending
explicit user sign-off on docs/NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md. This module
provides strictly typed contracts, read-only session/event telemetry logging, and
PostgreSQL checkpoint configuration helpers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import AgentEvent, AgentSession


class AgentCheckpointConfig(BaseModel):
    """Connection config for LangGraph PostgresSaver checkpoint persistence."""

    conn_uri: str
    checkpoint_namespace: str = "nexteras_agents"
    interrupt_before_nodes: list[str] = Field(default_factory=lambda: ["submit_application"])


def build_postgres_checkpoint_config() -> AgentCheckpointConfig:
    """Build sync libpq-compatible PostgreSQL URI for LangGraph PostgresSaver."""
    uri = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return AgentCheckpointConfig(conn_uri=uri)


class AgentStateEnvelope(BaseModel):
    """Canonical serializable state contract shared by future LangGraph orchestrator nodes."""

    session_id: UUID
    user_id: UUID
    agent_type: str
    language: str = "en"
    current_stage: Literal[
        "initialized",
        "discovered",
        "evaluated",
        "tailored",
        "awaiting_human_approval",
        "requires_manual_completion",
        "submitted",
        "rejected",
    ] = "initialized"
    opportunity_id: UUID | None = None
    approval_request_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentSessionTelemetry(BaseModel):
    id: UUID
    user_id: UUID
    agent_type: str
    state: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None


class AgentEventTelemetry(BaseModel):
    id: UUID
    session_id: UUID
    node_name: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


async def record_agent_event(
    session: AsyncSession,
    *,
    session_id: UUID,
    node_name: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> AgentEvent:
    event = AgentEvent(
        session_id=session_id,
        node_name=node_name,
        event_type=event_type,
        payload=payload or {},
    )
    session.add(event)
    await session.flush()
    return event


async def list_user_agent_sessions(
    session: AsyncSession, user_id: UUID, *, limit: int = 20
) -> list[AgentSessionTelemetry]:
    rows = list(
        (
            await session.execute(
                select(AgentSession)
                .where(AgentSession.user_id == user_id)
                .order_by(AgentSession.created_at.desc())
                .limit(max(1, min(limit, 50)))
            )
        )
        .scalars()
        .all()
    )
    return [
        AgentSessionTelemetry(
            id=r.id,
            user_id=r.user_id,
            agent_type=r.agent_type,
            state=dict(r.state or {}),
            is_active=bool(r.is_active) if r.is_active is not None else True,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def list_session_events(
    session: AsyncSession, user_id: UUID, session_id: UUID, *, limit: int = 50
) -> list[AgentEventTelemetry] | None:
    parent = (
        await session.execute(
            select(AgentSession).where(
                AgentSession.id == session_id,
                AgentSession.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if parent is None:
        return None
    rows = list(
        (
            await session.execute(
                select(AgentEvent)
                .where(AgentEvent.session_id == session_id)
                .order_by(AgentEvent.created_at.asc())
                .limit(max(1, min(limit, 100)))
            )
        )
        .scalars()
        .all()
    )
    return [
        AgentEventTelemetry(
            id=r.id,
            session_id=r.session_id,
            node_name=r.node_name,
            event_type=r.event_type,
            payload=dict(r.payload or {}),
            created_at=r.created_at,
        )
        for r in rows
    ]
