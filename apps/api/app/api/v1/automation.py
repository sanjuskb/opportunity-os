"""API endpoints for WS7 ARQ job dispatch, WS9 Playwright automation, and agent telemetry."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import (
    AgentCommandRequest,
    AgentCommandResponse,
    AgentEventTelemetry,
    AgentRunRequest,
    AgentRunResponse,
    AgentSessionDetailResponse,
    AgentSessionTelemetry,
    get_user_agent_session,
    list_session_events,
    list_user_agent_sessions,
)
from app.agents.orchestrator import AgentOrchestratorService
from app.automation.playwright_runner import (
    execute_approved_submission,
    load_owned_screenshot_bytes,
    prepare_application_automation,
)
from app.core.errors import ProblemDetailError
from app.core.security import AuthenticatedUser, require_supabase_role
from app.core.security_middleware import rate_limit
from app.db.session import get_db_session
from app.models.entities import AgentSession, BrowserExecutionLog
from app.schemas.common import CamelModel, StrictCamelModel

ops_router = APIRouter(tags=["Automation & Jobs"])

_AuthenticatedUser = Annotated[AuthenticatedUser, Depends(require_supabase_role("authenticated"))]
_DbSession = Annotated[AsyncSession, Depends(get_db_session)]


class AutomationPrepareRequest(StrictCamelModel):
    portal_url: str | None = Field(default=None, max_length=1000)


class AutomationExecuteRequest(StrictCamelModel):
    approval_request_id: UUID


class AutomationResultResponse(CamelModel):
    application_id: UUID
    session_id: UUID
    status: str
    approval_request_id: UUID | None = None
    screenshot_path: str | None = None
    filled_fields: dict[str, str] = {}
    logs: list[dict[str, Any]] = []
    message: str


class BrowserExecutionLogResponse(CamelModel):
    id: UUID
    approval_request_id: UUID | None = None
    session_id: UUID
    step_description: str
    action_type: str
    target_selector: str | None = None
    screenshot_url: str | None = None
    is_success: bool
    error_message: str | None = None
    executed_at: datetime | None = None


class JobEnqueueRequest(StrictCamelModel):
    job_type: Literal[
        "process_uploaded_resume",
        "run_olostep_research_job",
        "sync_crustdata_company",
        "aggregate_analytics_metrics",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


class JobStatusResponse(CamelModel):
    job_id: str
    job_type: str | None = None
    status: str
    queued_in_redis: bool = False
    result: Any | None = None


@ops_router.post(
    "/applications/{application_id}/prepare-automation",
    response_model=AutomationResultResponse,
    dependencies=[Depends(rate_limit("automation", limit=10, window_seconds=60))],
)
async def prepare_application_portal(
    application_id: UUID,
    payload: AutomationPrepareRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AutomationResultResponse:
    """Auto-fill an application portal form in Playwright and STOP for mandatory approval."""
    res = await prepare_application_automation(
        session,
        user_id=current_user.user_id,
        application_id=application_id,
        portal_url=payload.portal_url,
    )
    return AutomationResultResponse(
        application_id=res.application_id,
        session_id=res.session_id,
        status=res.status,
        approval_request_id=res.approval_request_id,
        screenshot_path=res.screenshot_path,
        filled_fields=res.filled_fields,
        logs=res.logs,
        message=res.message,
    )


@ops_router.post(
    "/applications/{application_id}/execute-approved",
    response_model=AutomationResultResponse,
    dependencies=[Depends(rate_limit("automation", limit=10, window_seconds=60))],
)
async def execute_approved_application(
    application_id: UUID,
    payload: AutomationExecuteRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AutomationResultResponse:
    """Execute portal submission ONLY after explicit approval_request approval."""
    res = await execute_approved_submission(
        session,
        user_id=current_user.user_id,
        application_id=application_id,
        approval_id=payload.approval_request_id,
    )
    return AutomationResultResponse(
        application_id=res.application_id,
        session_id=res.session_id,
        status=res.status,
        approval_request_id=res.approval_request_id,
        screenshot_path=res.screenshot_path,
        filled_fields=res.filled_fields,
        logs=res.logs,
        message=res.message,
    )


@ops_router.get(
    "/browser-logs",
    response_model=list[BrowserExecutionLogResponse],
)
async def list_browser_logs(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=30, ge=1, le=100),
) -> list[BrowserExecutionLogResponse]:
    """List Playwright execution audit logs belonging to the authenticated user."""
    stmt = (
        select(BrowserExecutionLog)
        .join(AgentSession, BrowserExecutionLog.session_id == AgentSession.id)
        .where(AgentSession.user_id == current_user.user_id)
        .order_by(BrowserExecutionLog.executed_at.desc())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [
        BrowserExecutionLogResponse(
            id=r.id,
            approval_request_id=r.approval_request_id,
            session_id=r.session_id,
            step_description=r.step_description,
            action_type=r.action_type,
            target_selector=r.target_selector,
            screenshot_url=r.screenshot_url,
            is_success=r.is_success,
            error_message=r.error_message,
            executed_at=r.executed_at,
        )
        for r in rows
    ]


@ops_router.get(
    "/agents/sessions",
    response_model=list[AgentSessionTelemetry],
    tags=["Agent Telemetry"],
)
async def get_agent_sessions(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=20, ge=1, le=50),
) -> list[AgentSessionTelemetry]:
    """Read-only telemetry endpoint for Agent Control Center session inspection."""
    return await list_user_agent_sessions(session, current_user.user_id, limit=limit)


@ops_router.get(
    "/agents/sessions/{session_id}/events",
    response_model=list[AgentEventTelemetry],
    tags=["Agent Telemetry"],
)
async def get_agent_session_events(
    session_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> list[AgentEventTelemetry]:
    """Read-only telemetry endpoint for ordered events within a user-owned session."""
    events = await list_session_events(session, current_user.user_id, session_id)
    if events is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Agent Session Not Found",
            detail="Requested agent session does not exist for this user.",
        )
    return events


@ops_router.get(
    "/browser-logs/{log_id}/screenshot",
    responses={200: {"content": {"image/png": {}}}},
)
async def get_browser_log_screenshot(
    log_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> Response:
    """Serve Playwright screenshot PNG bytes strictly scoped to authenticated owner."""
    content, filename = await load_owned_screenshot_bytes(
        session, user_id=current_user.user_id, log_id=log_id
    )
    return Response(
        content=content,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@ops_router.post(
    "/agents/runs",
    response_model=AgentRunResponse,
    tags=["Agent Orchestration"],
    dependencies=[Depends(rate_limit("agents_runs", limit=15, window_seconds=60))],
)
async def run_autonomous_agent_workflow(
    request: Request,
    payload: AgentRunRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AgentRunResponse:
    """Launch an autonomous 9-logical-agent LangGraph workflow persisted with PostgresSaver."""
    orchestrator = AgentOrchestratorService(
        session,
        olostep_client=getattr(request.app.state, "olostep_client", None),
        crustdata_client=getattr(request.app.state, "crustdata_client", None),
    )
    return await orchestrator.launch_workflow(current_user.user_id, payload)


@ops_router.get(
    "/agents/sessions/{session_id}",
    response_model=AgentSessionDetailResponse,
    tags=["Agent Telemetry"],
)
async def get_agent_session_detail(
    session_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AgentSessionDetailResponse:
    """Inspect a user-owned AgentSession along with its chronological events."""
    sess = await get_user_agent_session(session, current_user.user_id, session_id)
    if sess is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Agent Session Not Found",
            detail="Requested agent session does not exist for this user.",
        )
    events = await list_session_events(session, current_user.user_id, session_id) or []
    return AgentSessionDetailResponse(session=sess, events=events)


@ops_router.get(
    "/agents/sessions/{session_id}/stream",
    tags=["Agent Telemetry"],
)
async def stream_agent_session_events(
    session_id: UUID,
    current_user: _AuthenticatedUser,
    session: _DbSession,
    once: bool = Query(default=False),
    max_ticks: int = Query(default=6, ge=1, le=30),
) -> StreamingResponse:
    """Stream Server-Sent Events (SSE) for ordered AgentEvent telemetry of an owned session."""
    sess = await get_user_agent_session(session, current_user.user_id, session_id)
    if sess is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Agent Session Not Found",
            detail="Requested agent session does not exist for this user.",
        )

    async def _event_generator() -> Any:
        seen_ids: set[UUID] = set()
        ticks = 1 if once else max_ticks
        for tick in range(ticks):
            events = await list_session_events(session, current_user.user_id, session_id) or []
            for ev in events:
                if ev.id in seen_ids:
                    continue
                seen_ids.add(ev.id)
                yield (
                    f"event: agent_event\n"
                    f"data: {json.dumps(ev.model_dump(by_alias=True, mode='json'))}\n\n"
                )
            cur = await get_user_agent_session(session, current_user.user_id, session_id)
            if cur is None or not cur.is_active or tick + 1 >= ticks:
                yield (
                    "event: stream_end\n"
                    f"data: {json.dumps({'sessionId': str(session_id), 'isActive': bool(cur.is_active) if cur else False})}\n\n"
                )
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@ops_router.post(
    "/agents/sessions/{session_id}/command",
    response_model=AgentCommandResponse,
    tags=["Agent Orchestration"],
    dependencies=[Depends(rate_limit("agents_command", limit=30, window_seconds=60))],
)
async def command_agent_session(
    session_id: UUID,
    request: Request,
    payload: AgentCommandRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> AgentCommandResponse:
    """Execute pause, resume, or grounded query commands on an owned agent session."""
    orchestrator = AgentOrchestratorService(
        session,
        olostep_client=getattr(request.app.state, "olostep_client", None),
        crustdata_client=getattr(request.app.state, "crustdata_client", None),
    )
    return await orchestrator.execute_operator_command(
        user_id=current_user.user_id,
        session_id=session_id,
        req=payload,
    )


@ops_router.post(
    "/jobs",
    response_model=JobStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Jobs"],
    dependencies=[Depends(rate_limit("jobs", limit=20, window_seconds=60))],
)
async def enqueue_background_job(
    request: Request,
    payload: JobEnqueueRequest,
    current_user: _AuthenticatedUser,
) -> JobStatusResponse:
    """Enqueue an ARQ background worker job cleanly onto Redis."""
    job_id = f"{payload.job_type}:{uuid4()}"
    redis_client = getattr(request.app.state, "redis_client", None)
    args: tuple[Any, ...]
    if payload.job_type == "process_uploaded_resume":
        args = (str(payload.payload.get("resumeId", "")), str(current_user.user_id))
    elif payload.job_type == "run_olostep_research_job":
        args = (
            str(current_user.user_id),
            str(payload.payload.get("query", "Software Engineering Intern")),
            payload.payload.get("location"),
        )
    elif payload.job_type == "sync_crustdata_company":
        args = (payload.payload.get("domain"), payload.payload.get("companyName"))
    else:
        args = ()

    queued_in_redis = False
    if redis_client is not None:
        try:
            from arq.connections import create_pool

            from app.core.config import settings
            from app.tasks.worker import parse_redis_settings

            pool = await create_pool(parse_redis_settings(settings.REDIS_URL))
            try:
                job = await pool.enqueue_job(payload.job_type, *args, _job_id=job_id)
                if job is not None:
                    job_id = job.job_id
                queued_in_redis = True
            finally:
                await pool.aclose()
        except Exception:
            queued_in_redis = False

    return JobStatusResponse(
        job_id=job_id,
        job_type=payload.job_type,
        status="queued" if queued_in_redis else "redis_unavailable",
        queued_in_redis=queued_in_redis,
    )


@ops_router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Jobs"],
)
async def get_background_job_status(
    job_id: str,
    request: Request,
    current_user: _AuthenticatedUser,
) -> JobStatusResponse:
    """Inspect status/result of an ARQ background job."""
    _ = current_user.user_id
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is None:
        return JobStatusResponse(job_id=job_id, status="unknown", queued_in_redis=False)
    try:
        from arq.connections import create_pool
        from arq.jobs import Job

        from app.core.config import settings
        from app.tasks.worker import parse_redis_settings

        pool = await create_pool(parse_redis_settings(settings.REDIS_URL))
        try:
            job = Job(job_id, redis=pool)
            job_status = await job.status()
            info = await job.info()
            res_info = await job.result_info()
            return JobStatusResponse(
                job_id=job_id,
                job_type=info.function if info else None,
                status=job_status.value,
                queued_in_redis=True,
                result=res_info.result if res_info and res_info.success else None,
            )
        finally:
            await pool.aclose()
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Job lookup unavailable: {type(exc).__name__}"
        ) from exc
