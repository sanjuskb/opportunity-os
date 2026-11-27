"""Persistent voice session, AI conversation, and multilingual tool execution services."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.integrations.gemini import GeminiClient
from app.models.entities import (
    Application,
    CareerPassport,
    Conversation,
    ConversationMessage,
    VoiceSession,
)
from app.repositories.profiles import ProfileRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.repositories.voice_sessions import VoiceSessionRepository
from app.schemas.common import (
    AiChatRequest,
    AiChatResponse,
    ConversationDetailResponse,
    ConversationMessageResponse,
    ConversationSummaryResponse,
    OpportunityDiscoverRequest,
    VoiceSessionCreateRequest,
    VoiceSessionResponse,
)
from app.services.eligibility import EligibilityService
from app.services.opportunities import OpportunityService

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

    async def list_sessions(
        self, user_id: UUID, *, limit: int = 20, offset: int = 0
    ) -> list[VoiceSessionResponse]:
        records = await self._repo.list_for_user(user_id, limit=limit, offset=offset)
        return [self._to_response(r) for r in records]

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


class ConversationService:
    """Orchestrates multilingual Gemini AI chat + live DB function calling + transcript persistence."""

    def __init__(self, session: AsyncSession, gemini_client: GeminiClient | None = None) -> None:
        self._session = session
        self._gemini = gemini_client or GeminiClient()

    async def chat(self, user_id: UUID, payload: AiChatRequest) -> AiChatResponse:
        conv: Conversation | None = None
        if payload.conversation_id is not None:
            conv = (
                await self._session.execute(
                    select(Conversation).where(
                        Conversation.id == payload.conversation_id,
                        Conversation.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if conv is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Conversation Not Found",
                    detail="Conversation was not found for this user.",
                )
        else:
            title = payload.message.strip()[:80] or "Career Consultation"
            conv = Conversation(user_id=user_id, title=title)
            self._session.add(conv)
            await self._session.flush()
            await self._session.refresh(conv)

        prior_rows = list(
            (
                await self._session.execute(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conv.id)
                    .order_by(ConversationMessage.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        history = [{"role": row.role, "content": row.content} for row in prior_rows]

        async def _execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
            return await execute_career_tool(self._session, user_id, name, args)

        result = await self._gemini.chat_with_tools(
            user_message=payload.message,
            history=history,
            language=payload.language,
            tool_executor=_execute_tool,
        )

        self._session.add(
            ConversationMessage(
                conversation_id=conv.id,
                role="user",
                content=payload.message,
                language=payload.language,
            )
        )
        self._session.add(
            ConversationMessage(
                conversation_id=conv.id,
                role="assistant",
                content=result.reply,
                language=payload.language,
            )
        )
        await self._session.commit()

        return AiChatResponse(
            conversation_id=conv.id,
            language=payload.language,
            reply=result.reply,
            provider=result.provider,
            model=result.model,
            tool_calls=result.tool_calls_executed,
        )

    async def list_conversations(
        self, user_id: UUID, limit: int = 20
    ) -> list[ConversationSummaryResponse]:
        rows = list(
            (
                await self._session.execute(
                    select(Conversation)
                    .where(Conversation.user_id == user_id)
                    .order_by(Conversation.created_at.desc())
                    .limit(max(1, min(limit, 50)))
                )
            )
            .scalars()
            .all()
        )
        return [
            ConversationSummaryResponse(
                id=row.id,
                title=row.title or "Career Consultation",
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_conversation(
        self, user_id: UUID, conversation_id: UUID
    ) -> ConversationDetailResponse:
        conv = (
            await self._session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if conv is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Conversation Not Found",
                detail="Conversation was not found for this user.",
            )
        msgs = list(
            (
                await self._session.execute(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conv.id)
                    .order_by(ConversationMessage.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title or "Career Consultation",
            created_at=conv.created_at,
            messages=[
                ConversationMessageResponse(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    language=m.language or "en",
                    created_at=m.created_at,
                )
                for m in msgs
            ],
        )


async def execute_career_tool(
    session: AsyncSession,
    user_id: UUID,
    tool_name: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Safely execute grounded Career OS database tools on behalf of Gemini Live / REST."""
    if tool_name == "search_opportunities":
        query = str(args.get("query") or "")
        opp_type = args.get("opportunity_type")
        limit = int(args.get("limit") or 5)
        page = await OpportunityService(session).discover(
            user_id,
            OpportunityDiscoverRequest(
                query=query if len(query) >= 2 else "internship",
                type=opp_type if isinstance(opp_type, str) else None,
                limit=max(1, min(limit, 10)),
            ),
        )
        return {
            "opportunities": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "organization": item.organization,
                    "type": item.type,
                    "location": item.location,
                    "matchScore": item.match_score,
                }
                for item in page.items
            ]
        }

    if tool_name == "check_eligibility":
        raw_id = args.get("opportunity_id")
        if not raw_id:
            return {"error": "opportunity_id is required"}
        try:
            opp_uuid = UUID(str(raw_id))
        except ValueError:
            return {"error": "Invalid opportunity_id UUID"}
        res = await EligibilityService(session).evaluate(user_id, opp_uuid)
        return res.model_dump(mode="json")

    if tool_name == "get_career_passport":
        profile = await StudentProfileRepository(session).get_by_user_id(user_id)
        passport = (
            await session.execute(
                select(CareerPassport).where(CareerPassport.student_id == profile.id)
            )
            if profile is not None
            else None
        )
        cp_row = passport.scalar_one_or_none() if passport is not None else None
        return {
            "profile": {
                "collegeName": profile.college_name if profile else None,
                "degree": profile.degree if profile else None,
                "branch": profile.branch if profile else None,
                "cgpa": float(profile.cgpa) if profile and profile.cgpa is not None else None,
                "graduationYear": profile.graduation_year if profile else None,
            },
            "careerPassport": {
                "projects": list(cp_row.projects or []) if cp_row else [],
                "certifications": list(cp_row.certifications or []) if cp_row else [],
                "coursework": list(cp_row.coursework or []) if cp_row else [],
                "verifiedAchievements": list(cp_row.verified_achievements or []) if cp_row else [],
            },
        }

    if tool_name == "list_applications":
        apps = list(
            (
                await session.execute(
                    select(Application)
                    .where(Application.user_id == user_id)
                    .order_by(Application.created_at.desc())
                    .limit(10)
                )
            )
            .scalars()
            .all()
        )
        return {
            "applications": [
                {
                    "id": str(app.id),
                    "opportunityId": str(app.opportunity_id),
                    "status": app.status,
                }
                for app in apps
            ]
        }

    return {"error": f"Unknown tool: {tool_name}"}
