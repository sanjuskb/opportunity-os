"""Opportunity repository with keyset cursor pagination and pgvector similarity interface."""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Opportunity, OpportunityEmbedding, SavedOpportunity
from app.repositories.embeddings import (
    CANONICAL_VECTOR_DIM,
    LEGACY_VECTOR_DIM,
    validate_embedding_vector,
)


@dataclass(frozen=True)
class OpportunityPage:
    """Cursor-paginated opportunity slice."""

    items: list[Opportunity]
    next_cursor: str | None
    has_more: bool


def encode_opportunity_cursor(created_at: datetime, opp_id: UUID) -> str:
    """Encode (created_at, id) into an opaque URL-safe Base64 cursor."""
    payload = json.dumps({"created_at": created_at.isoformat(), "id": str(opp_id)})
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_opportunity_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Decode an opaque Base64 cursor into (created_at, id)."""
    raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    data = json.loads(raw)
    return datetime.fromisoformat(data["created_at"]), UUID(data["id"])


class OpportunityRepository:
    """Data access for public.opportunities, eligibility, and pgvector embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, opportunity_id: UUID) -> Opportunity | None:
        stmt = (
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(selectinload(Opportunity.eligibility))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        cursor: str | None = None,
        limit: int = 20,
        opp_type: str | None = None,
        search_query: str | None = None,
        active_only: bool = True,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> OpportunityPage:
        bounded_limit = max(1, min(limit, 100))
        stmt = select(Opportunity).options(selectinload(Opportunity.eligibility))

        if active_only:
            stmt = stmt.where(Opportunity.is_active.is_(True))
        if opp_type:
            stmt = stmt.where(Opportunity.type == opp_type)
        if search_query:
            pattern = f"%{search_query.strip()}%"
            stmt = stmt.where(
                or_(
                    Opportunity.title.ilike(pattern),
                    Opportunity.organization.ilike(pattern),
                    Opportunity.description.ilike(pattern),
                )
            )

        if cursor:
            cursor_ts, cursor_id = decode_opportunity_cursor(cursor)
            if sort_order == "desc":
                stmt = stmt.where(
                    or_(
                        Opportunity.created_at < cursor_ts,
                        and_(Opportunity.created_at == cursor_ts, Opportunity.id < cursor_id),
                    )
                )
            else:
                stmt = stmt.where(
                    or_(
                        Opportunity.created_at > cursor_ts,
                        and_(Opportunity.created_at == cursor_ts, Opportunity.id > cursor_id),
                    )
                )

        if sort_order == "desc":
            stmt = stmt.order_by(Opportunity.created_at.desc(), Opportunity.id.desc())
        else:
            stmt = stmt.order_by(Opportunity.created_at.asc(), Opportunity.id.asc())

        stmt = stmt.limit(bounded_limit + 1)
        rows = list((await self._session.execute(stmt)).scalars().all())

        has_more = len(rows) > bounded_limit
        items = rows[:bounded_limit]
        next_cursor: str | None = None
        if has_more and items and items[-1].created_at is not None:
            next_cursor = encode_opportunity_cursor(items[-1].created_at, items[-1].id)

        return OpportunityPage(items=items, next_cursor=next_cursor, has_more=has_more)

    async def search_similar_by_vector(
        self,
        query_vector: Sequence[float],
        *,
        model_column: Literal["embedding", "embedding_minilm_384"] = "embedding_minilm_384",
        limit: int = 10,
        active_only: bool = True,
    ) -> list[tuple[Opportunity, float]]:
        """Query pgvector cosine similarity without fabricating embedding rows."""
        expected_dim = (
            CANONICAL_VECTOR_DIM
            if model_column == "embedding_minilm_384"
            else LEGACY_VECTOR_DIM
        )
        validated = validate_embedding_vector(query_vector, expected_dim=expected_dim)
        vec_col = (
            OpportunityEmbedding.embedding_minilm_384
            if model_column == "embedding_minilm_384"
            else OpportunityEmbedding.embedding
        )
        distance_expr = vec_col.cosine_distance(validated).label("distance")

        stmt = (
            select(Opportunity, distance_expr)
            .join(OpportunityEmbedding, OpportunityEmbedding.opportunity_id == Opportunity.id)
            .where(vec_col.is_not(None))
            .options(selectinload(Opportunity.eligibility))
        )
        if model_column == "embedding_minilm_384":
            stmt = stmt.where(OpportunityEmbedding.embedding_status == "ready")
        if active_only:
            stmt = stmt.where(Opportunity.is_active.is_(True))

        stmt = stmt.order_by(distance_expr.asc()).limit(max(1, min(limit, 50)))
        rows = (await self._session.execute(stmt)).all()
        return [(opp, float(1.0 - dist)) for opp, dist in rows]

    async def save_for_user(
        self, user_id: UUID, opportunity_id: UUID, *, notes: str | None = None
    ) -> SavedOpportunity:
        """Idempotently bookmark an opportunity for user_id."""
        stmt = (
            pg_insert(SavedOpportunity)
            .values(user_id=user_id, opportunity_id=opportunity_id, notes=notes)
            .on_conflict_do_update(
                index_elements=["user_id", "opportunity_id"],
                set_={"notes": notes},
            )
            .returning(SavedOpportunity)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def unsave_for_user(self, user_id: UUID, opportunity_id: UUID) -> bool:
        """Remove an opportunity bookmark owned by user_id."""
        stmt = delete(SavedOpportunity).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0  # type: ignore[attr-defined]

    async def is_saved_by_user(self, user_id: UUID, opportunity_id: UUID) -> bool:
        stmt = select(SavedOpportunity.id).where(
            SavedOpportunity.user_id == user_id,
            SavedOpportunity.opportunity_id == opportunity_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def list_saved_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True,
    ) -> list[Opportunity]:
        """List opportunities saved by user_id with deterministic ordering."""
        stmt = (
            select(Opportunity)
            .join(SavedOpportunity, SavedOpportunity.opportunity_id == Opportunity.id)
            .where(SavedOpportunity.user_id == user_id)
            .options(selectinload(Opportunity.eligibility))
        )
        if active_only:
            stmt = stmt.where(Opportunity.is_active.is_(True))
        stmt = (
            stmt.order_by(SavedOpportunity.saved_at.desc(), SavedOpportunity.id.desc())
            .limit(max(1, min(limit, 100)))
            .offset(max(0, offset))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())
