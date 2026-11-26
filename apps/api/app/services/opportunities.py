"""Domain service for Opportunity discovery, detail retrieval, and bookmarking."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import Opportunity
from app.repositories.opportunities import OpportunityRepository
from app.schemas.common import (
    OpportunityResponse,
    PaginatedOpportunitiesResponse,
    SaveOpportunityRequest,
    SaveOpportunityResponse,
)


class OpportunityService:
    """Business logic for public.opportunities and public.saved_opportunities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OpportunityRepository(session)

    async def list_opportunities(
        self,
        *,
        cursor: str | None = None,
        limit: int = 20,
        opp_type: str | None = None,
        search_query: str | None = None,
        active_only: bool = True,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> PaginatedOpportunitiesResponse:
        try:
            page = await self._repo.list_paginated(
                cursor=cursor,
                limit=limit,
                opp_type=opp_type,
                search_query=search_query,
                active_only=active_only,
                sort_order=sort_order,
            )
        except (ValueError, KeyError) as exc:
            raise ProblemDetailError(
                status_code=422,
                problem_type="urn:problem:validation_failed",
                title="Invalid Pagination Cursor",
                detail="The provided pagination cursor is malformed.",
            ) from exc

        return PaginatedOpportunitiesResponse(
            items=[self._to_response(o) for o in page.items],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )

    async def get_opportunity(self, opportunity_id: UUID) -> OpportunityResponse:
        opp = await self._repo.get_by_id(opportunity_id)
        if opp is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Opportunity Not Found",
                detail="Requested opportunity does not exist.",
            )
        return self._to_response(opp)

    async def list_saved_opportunities(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True,
    ) -> list[OpportunityResponse]:
        rows = await self._repo.list_saved_for_user(
            user_id, limit=limit, offset=offset, active_only=active_only
        )
        return [self._to_response(o) for o in rows]

    async def toggle_save(
        self,
        user_id: UUID,
        opportunity_id: UUID,
        payload: SaveOpportunityRequest,
    ) -> SaveOpportunityResponse:
        opp = await self._repo.get_by_id(opportunity_id)
        if opp is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Opportunity Not Found",
                detail="Requested opportunity does not exist.",
            )

        if payload.saved:
            saved_row = await self._repo.save_for_user(
                user_id, opportunity_id, notes=payload.notes
            )
            await self._session.commit()
            return SaveOpportunityResponse(
                opportunity_id=opportunity_id,
                saved=True,
                notes=saved_row.notes,
            )

        await self._repo.unsave_for_user(user_id, opportunity_id)
        await self._session.commit()
        return SaveOpportunityResponse(
            opportunity_id=opportunity_id,
            saved=False,
            notes=None,
        )

    @staticmethod
    def _to_response(opp: Opportunity) -> OpportunityResponse:
        elig = opp.eligibility
        return OpportunityResponse(
            id=opp.id,
            title=opp.title,
            organization=opp.organization,
            location=opp.location,
            type=opp.type,
            description=opp.description,
            stipend_or_salary=opp.stipend_or_salary,
            deadline=opp.deadline,
            source_url=opp.source_url,
            source_provider=opp.source_provider,
            retrieval_timestamp=opp.retrieval_timestamp,
            is_active=bool(opp.is_active) if opp.is_active is not None else True,
            required_skills=list(elig.required_skills or []) if elig else [],
            eligible_batches=list(elig.eligible_batches or []) if elig else [],
            eligible_degrees=list(elig.eligible_degrees or []) if elig else [],
            eligible_branches=list(elig.eligible_branches or []) if elig else [],
            min_cgpa=elig.min_cgpa if elig else None,
        )
