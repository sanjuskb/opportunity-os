"""Agent state contracts, PostgreSQL checkpoint helpers, and telemetry DTOs/queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import AgentEvent, AgentSession
from app.schemas.common import CamelModel, StrictCamelModel


class AgentCheckpointConfig(BaseModel):
    """Connection config for LangGraph PostgresSaver checkpoint persistence."""

    conn_uri: str
    checkpoint_namespace: str = "nexteras_agents"
    interrupt_before_nodes: list[str] = Field(default_factory=lambda: ["submit_application"])


def build_postgres_checkpoint_config() -> AgentCheckpointConfig:
    """Build sync/async psycopg-compatible PostgreSQL URI for LangGraph PostgresSaver."""
    uri = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return AgentCheckpointConfig(conn_uri=uri)


class AgentStateEnvelope(BaseModel):
    """Canonical serializable state contract shared by autonomous LangGraph orchestrator nodes."""

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


class AgentSessionTelemetry(CamelModel):
    id: UUID
    user_id: UUID
    agent_type: str
    state: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None


class AgentEventTelemetry(CamelModel):
    id: UUID
    session_id: UUID
    node_name: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AgentRunRequest(StrictCamelModel):
    """Launch an autonomous multi-agent workflow thread."""

    query: str = Field(
        default="Find eligible software and ML internships in India",
        min_length=2,
        max_length=500,
    )
    workflow_type: Literal[
        "full_pipeline",
        "discovery",
        "resume_tailoring",
        "application_prepare",
    ] = "full_pipeline"
    language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu"] = "en"
    target_opportunity_id: UUID | None = None
    portal_url: str | None = Field(default=None, max_length=1000)
    enable_web_research: bool = False
    run_playwright: bool = False
    max_candidates: int = Field(default=6, ge=1, le=20)


class AgentRunResponse(CamelModel):
    """Summary returned when an autonomous workflow pauses at M11 or completes."""

    session_id: UUID
    thread_id: str
    agent_type: str
    status: str
    current_stage: str
    checkpointer_backend: str
    language: str
    selected_opportunity_id: UUID | None = None
    application_id: UUID | None = None
    approval_request_id: UUID | None = None
    tailored_resume_id: UUID | None = None
    screenshot_path: str | None = None
    interview_session_id: UUID | None = None
    ranked_shortlist: list[dict[str, Any]] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    events: list[AgentEventTelemetry] = Field(default_factory=list)
    message: str


class AgentSessionDetailResponse(CamelModel):
    session: AgentSessionTelemetry
    events: list[AgentEventTelemetry] = Field(default_factory=list)


class AgentCommandRequest(StrictCamelModel):
    action: Literal["query", "pause", "resume"] = "query"
    command: str = Field(default="", max_length=500)
    language: Literal["en", "hi", "te", "ta", "kn", "ml", "bn", "mr", "gu"] = "en"


class AgentCommandResponse(CamelModel):
    session_id: UUID
    action: str
    reply: str
    is_active: bool
    event: AgentEventTelemetry | None = None


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


async def get_user_agent_session(
    session: AsyncSession, user_id: UUID, session_id: UUID
) -> AgentSessionTelemetry | None:
    row = (
        await session.execute(
            select(AgentSession).where(
                AgentSession.id == session_id,
                AgentSession.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    return AgentSessionTelemetry(
        id=row.id,
        user_id=row.user_id,
        agent_type=row.agent_type,
        state=dict(row.state or {}),
        is_active=bool(row.is_active) if row.is_active is not None else True,
        created_at=row.created_at,
    )


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
                .order_by(AgentEvent.created_at.asc(), AgentEvent.id.asc())
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
