"""Voice Gateway endpoints using short-lived, single-use WebSocket tickets."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.core.config import settings
from app.core.security import AuthenticatedUser, require_supabase_role
from app.schemas.common import VoiceTicketResponse
from app.voice.tickets import VoiceTicketStore, get_voice_ticket_store

voice_router = APIRouter(prefix="/voice", tags=["Voice"])

_AuthenticatedUser = Annotated[AuthenticatedUser, Depends(require_supabase_role("authenticated"))]


@voice_router.post("/tickets", response_model=VoiceTicketResponse)
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
    """Authenticate WebSocket via atomic single-use ticket and handle PCM + JSON frames."""
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
    await websocket.send_json(
        {
            "event": "session_ready",
            "userId": str(ticket_payload.user_id),
        }
    )

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
                await websocket.send_json({"event": "audio_received", "bytes": len(raw_bytes)})
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
                    await websocket.send_json({"event": "error", "code": "invalid_json"})
                    continue

                if not isinstance(message, dict):
                    await websocket.send_json({"event": "error", "code": "invalid_payload"})
                    continue

                event_type = message.get("event")
                if event_type == "session_init":
                    await websocket.send_json(
                        {
                            "event": "session_acknowledged",
                            "userId": str(ticket_payload.user_id),
                            "language": message.get("language", "en"),
                        }
                    )
                elif event_type == "interrupted":
                    await websocket.send_json({"event": "playback_cancelled"})
                elif event_type == "ping":
                    await websocket.send_json({"event": "pong"})
                else:
                    await websocket.send_json({"event": "error", "code": "unknown_event"})
    except WebSocketDisconnect:
        return
