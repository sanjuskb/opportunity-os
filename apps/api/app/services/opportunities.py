"""Domain service for Opportunity discovery (hybrid pgvector + SQL + explainable ranking) & bookmarking."""

from __future__ import annotations

import logging
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import Opportunity, StudentEmbedding
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.opportunities import OpportunityRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    OpportunityDiscoverRequest,
    OpportunityResponse,
    PaginatedOpportunitiesResponse,
    SaveOpportunityRequest,
    SaveOpportunityResponse,
)
from app.services.eligibility import EligibilityService

logger = logging.getLogger("opportunity_os.opportunities")


class OpportunityService:
    """Business logic for public.opportunities, vector discovery, and bookmarking."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_adapter: Any | None = None,
    ) -> None:
        self._session = session
        self._repo = OpportunityRepository(session)
        self._student_repo = StudentProfileRepository(session)
        self._passport_repo = CareerPassportRepository(session)
        self._resume_repo = ResumeRepository(session)
        self._embedding_adapter = embedding_adapter

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

    async def discover(
        self,
        user_id: UUID,
        payload: OpportunityDiscoverRequest,
    ) -> PaginatedOpportunitiesResponse:
        """Hybrid pgvector semantic recall + SQL filtering + deterministic eligibility ranking."""
        query_text = payload.query.strip()
        student = await self._student_repo.get_by_user_id(user_id)
        passport = await self._passport_repo.get_by_user_id(user_id)
        resumes = await self._resume_repo.list_for_user(user_id, limit=3)

        stu_emb_vec = await self._get_student_vector(user_id)
        query_vector = await self._resolve_query_vector(query_text, fallback_vector=stu_emb_vec)

        semantic_by_id: dict[UUID, tuple[Opportunity, float]] = {}
        if query_vector is not None:
            try:
                vec_hits = await self._repo.search_similar_by_vector(
                    query_vector,
                    model_column="embedding_minilm_384",
                    limit=min(50, max(payload.limit * 2, 10)),
                    active_only=True,
                )
                for opp, score in vec_hits:
                    if payload.type and opp.type != payload.type:
                        continue
                    semantic_by_id[opp.id] = (opp, score)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Vector search unavailable (%s); continuing with SQL recall.", exc)

        # Hybrid SQL keyword recall guarantees newly inserted/un-embedded matches still surface
        sql_page = await self._repo.list_paginated(
            limit=payload.limit,
            opp_type=payload.type,
            search_query=query_text,
            active_only=True,
        )

        merged: dict[UUID, Opportunity] = {o.id: o for o in sql_page.items}
        for oid, (opp, _) in semantic_by_id.items():
            merged.setdefault(oid, opp)

        # Fallback: if both vector & keyword returned nothing (e.g. broad natural query), load active slice
        if not merged:
            broad_page = await self._repo.list_paginated(
                limit=payload.limit,
                opp_type=payload.type,
                search_query=None,
                active_only=True,
            )
            for opp in broad_page.items:
                merged.setdefault(opp.id, opp)

        query_terms = [t for t in query_text.lower().split() if len(t) > 1]
        scored_items: list[tuple[float, OpportunityResponse]] = []

        for opp in merged.values():
            vec_score = semantic_by_id[opp.id][1] if opp.id in semantic_by_id else None
            elig_result = EligibilityService.evaluate_loaded(
                user_id=user_id,
                opportunity=opp,
                student=student,
                passport=passport,
                resumes=resumes,
                semantic_similarity=vec_score,
            )
            haystack = f"{opp.title} {opp.organization} {opp.description}".lower()
            lexical_hits = sum(1 for t in query_terms if t in haystack)
            lexical_bonus = (lexical_hits / max(1, len(query_terms))) * 20.0
            elig_bonus = (
                25.0
                if elig_result.is_eligible
                else (10.0 if elig_result.status == "needs_more_info" else -15.0)
            )
            sem_bonus = (vec_score * 35.0) if vec_score is not None else 12.0
            final_rank_score = round(
                max(
                    0.0,
                    min(
                        100.0,
                        0.45 * elig_result.score + sem_bonus + lexical_bonus + elig_bonus * 0.4,
                    ),
                ),
                2,
            )

            reasons = list(elig_result.reasons)
            if vec_score is not None:
                reasons.insert(0, f"Semantic vector alignment: {round(vec_score * 100.0, 1)}%.")

            dto = self._to_response(
                opp,
                match_score=final_rank_score,
                semantic_score=round(vec_score, 4) if vec_score is not None else None,
                is_eligible=elig_result.is_eligible,
                match_reasons=reasons,
                matched_skills=elig_result.skill_overlap.matched_skills,
                missing_skills=elig_result.missing_skills,
            )
            scored_items.append((final_rank_score, dto))

        scored_items.sort(key=lambda pair: (bool(pair[1].is_eligible), pair[0]), reverse=True)
        limited = [dto for _, dto in scored_items[: payload.limit]]

        return PaginatedOpportunitiesResponse(
            items=limited,
            next_cursor=None,
            has_more=len(scored_items) > payload.limit,
        )

    async def _get_student_vector(self, user_id: UUID) -> list[float] | None:
        stmt = select(StudentEmbedding.embedding_minilm_384).where(
            StudentEmbedding.user_id == user_id
        )
        vec = (await self._session.execute(stmt)).scalar_one_or_none()
        return list(vec) if vec is not None else None

    async def _resolve_query_vector(
        self,
        query_text: str,
        *,
        fallback_vector: list[float] | None = None,
    ) -> list[float] | None:
        if self._embedding_adapter is not None:
            try:
                vec, _, _ = self._embedding_adapter.embed_one(query_text)
                return list(vec)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Injected embedding_adapter failed (%s); falling back.", exc)
        return fallback_vector

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
            saved_row = await self._repo.save_for_user(user_id, opportunity_id, notes=payload.notes)
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
    def _to_response(
        opp: Opportunity,
        *,
        match_score: float | None = None,
        semantic_score: float | None = None,
        is_eligible: bool | None = None,
        match_reasons: list[str] | None = None,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> OpportunityResponse:
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
            eligible_academic_years=list(elig.eligible_academic_years or []) if elig else [],
            min_cgpa=elig.min_cgpa if elig else None,
            max_active_backlogs=elig.max_active_backlogs if elig else None,
            min_experience_months=elig.min_experience_months if elig else None,
            allowed_locations=list(elig.allowed_locations or []) if elig else [],
            remote_allowed=(
                bool(elig.remote_allowed) if elig and elig.remote_allowed is not None else True
            ),
            required_citizenship=elig.required_citizenship if elig else None,
            preferred_skills=list(elig.preferred_skills or []) if elig else [],
            match_score=match_score,
            semantic_score=semantic_score,
            is_eligible=is_eligible,
            match_reasons=match_reasons or [],
            matched_skills=matched_skills or [],
            missing_skills=missing_skills or [],
        )
