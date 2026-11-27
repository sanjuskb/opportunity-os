"""Voice Gateway endpoints using single-use WebSocket tickets and Gemini Live relay."""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import AuthenticatedUser, require_supabase_role
from app.core.security_middleware import rate_limit
from app.db.session import get_db_session
from app.integrations.gemini import GeminiClient, GeminiLiveRelay
from app.schemas.common import (
    VoiceSessionCreateRequest,
    VoiceSessionResponse,
    VoiceTicketResponse,
)
from app.services.voice_sessions import VoiceSessionService, execute_career_tool
from app.voice.tickets import VoiceTicketStore, get_voice_ticket_store

voice_router = APIRouter(prefix="/voice", tags=["Voice"])

_AuthenticatedUser = Annotated[AuthenticatedUser, Depends(require_supabase_role("authenticated"))]
_DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@voice_router.get(
    "/sessions",
    response_model=list[VoiceSessionResponse],
)
async def list_voice_sessions(
    current_user: _AuthenticatedUser,
    session: _DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[VoiceSessionResponse]:
    """List persisted voice interaction telemetry records for the authenticated user."""
    return await VoiceSessionService(session).list_sessions(
        current_user.user_id, limit=limit, offset=offset
    )


@voice_router.post(
    "/sessions",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voice_session(
    payload: VoiceSessionCreateRequest,
    current_user: _AuthenticatedUser,
    session: _DbSession,
) -> VoiceSessionResponse:
    """Persist a voice interaction telemetry session owned by the authenticated user."""
    return await VoiceSessionService(session).create_session(current_user.user_id, payload)


@voice_router.post(
    "/tickets",
    response_model=VoiceTicketResponse,
    dependencies=[Depends(rate_limit("voice_tickets", limit=30, window_seconds=60))],
)
async def create_voice_ticket(
    current_user: _AuthenticatedUser,
    ticket_store: Annotated[VoiceTicketStore, Depends(get_voice_ticket_store)],
) -> VoiceTicketResponse:
    """Issue a short-lived, single-use WebSocket ticket bound to the authenticated user."""
    payload = await ticket_store.issue_ticket(current_user.user_id)
    return VoiceTicketResponse(
        ticket=payload.ticket,
        expires_at=payload.expires_at,
        ttl_seconds=settings.VOICE_TICKET_TTL_SECONDS,
    )


@voice_router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    ticket_store: Annotated[VoiceTicketStore, Depends(get_voice_ticket_store)],
    ticket: str = Query(default=""),
) -> None:
    """Authenticate WebSocket via atomic single-use ticket and bridge PCM audio + text turns."""
    if not ticket:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing voice ticket")
        return

    ticket_payload = await ticket_store.consume_ticket(ticket)
    if ticket_payload is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid, expired, or already used voice ticket",
        )
        return

    await websocket.accept()
    user_id = ticket_payload.user_id
    await websocket.send_json(
        {
            "event": "session_ready",
            "userId": str(user_id),
        }
    )

    live_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    live_task: asyncio.Task[None] | None = None
    active_language = "en"
    ws_send_lock = asyncio.Lock()

    async def _send_json_safe(payload: dict[str, Any]) -> None:
        async with ws_send_lock:
            await websocket.send_json(payload)

    async def _tool_exec(name: str, args: dict[str, Any]) -> dict[str, Any]:
        db_override = getattr(websocket.app, "dependency_overrides", {}).get(get_db_session)
        if db_override is not None:
            try:
                async for db_session in db_override():
                    return await execute_career_tool(db_session, user_id, name, args)
            except Exception:
                return {"note": "Database unavailable during WebSocket session"}
        db_mgr = getattr(websocket.app.state, "db", None)
        if db_mgr is None or getattr(db_mgr, "session_factory", None) is None:
            return {"note": "Database unavailable during WebSocket session"}
        try:
            async with db_mgr.session_factory() as db_session:
                return await execute_career_tool(db_session, user_id, name, args)
        except Exception:
            return {"note": "Database unavailable during WebSocket session"}

    try:
        while True:
            frame = await websocket.receive()
            frame_type = frame.get("type")
            if frame_type == "websocket.disconnect":
                return

            raw_bytes = frame.get("bytes")
            if raw_bytes is not None:
                if len(raw_bytes) > settings.VOICE_MAX_MESSAGE_BYTES:
                    await websocket.close(
                        code=status.WS_1009_MESSAGE_TOO_BIG,
                        reason="Audio frame exceeds maximum allowed size",
                    )
                    return
                if live_task is not None and not live_task.done():
                    await live_queue.put({"kind": "pcm", "bytes": raw_bytes})
                else:
                    await _send_json_safe({"event": "audio_received", "bytes": len(raw_bytes)})
                continue

            raw_text = frame.get("text")
            if raw_text is not None:
                if len(raw_text.encode("utf-8")) > settings.VOICE_MAX_MESSAGE_BYTES:
                    await websocket.close(
                        code=status.WS_1009_MESSAGE_TOO_BIG,
                        reason="Control message exceeds maximum allowed size",
                    )
                    return
                try:
                    message = json.loads(raw_text)
                except json.JSONDecodeError:
                    await _send_json_safe({"event": "error", "code": "invalid_json"})
                    continue

                if not isinstance(message, dict):
                    await _send_json_safe({"event": "error", "code": "invalid_payload"})
                    continue

                event_type = message.get("event")
                if event_type == "session_init":
                    active_language = str(message.get("language", "en"))
                    requested_live = message.get("mode") == "live"
                    if requested_live and settings.GEMINI_API_KEY and live_task is None:
                        relay = GeminiLiveRelay()
                        live_task = asyncio.create_task(
                            relay.stream_session(
                                client_send_json=_send_json_safe,
                                client_queue=live_queue,
                                language=active_language,
                                tool_executor=_tool_exec,
                            )
                        )
                    await _send_json_safe(
                        {
                            "event": "session_acknowledged",
                            "userId": str(user_id),
                            "language": active_language,
                        }
                    )
                elif event_type == "text_turn":
                    turn_text = str(message.get("text", "")).strip()
                    turn_lang = str(message.get("language", active_language))
                    if not turn_text:
                        await _send_json_safe({"event": "error", "code": "empty_text"})
                        continue
                    if live_task is not None and not live_task.done():
                        await live_queue.put({"kind": "text", "text": turn_text})
                    else:
                        result = await GeminiClient().chat_with_tools(
                            user_message=turn_text,
                            language=turn_lang,
                            tool_executor=_tool_exec,
                        )
                        await _send_json_safe({"event": "ai_transcript", "text": result.reply})
                        await _send_json_safe({"event": "turn_complete"})
                elif event_type == "interrupted":
                    if live_task is not None and not live_task.done():
                        await live_queue.put({"kind": "interrupt"})
                    await _send_json_safe({"event": "playback_cancelled"})
                elif event_type == "ping":
                    await _send_json_safe({"event": "pong"})
                else:
                    await _send_json_safe({"event": "error", "code": "unknown_event"})
    except WebSocketDisconnect:
        return
    finally:
        if live_task is not None:
            await live_queue.put(None)
            live_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await live_task
