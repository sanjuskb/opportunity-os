"""Repository for canonical 384-dim opportunity embeddings and similarity search."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, case, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Opportunity, OpportunityEmbedding

CANONICAL_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
CANONICAL_VECTOR_DIM = 384
LEGACY_VECTOR_DIM = 768

_CREDENTIAL_URL_RE = re.compile(r"([a-zA-Z0-9+.-]+://)([^:@\s]+):([^@\s]+)@")
_SECRET_KV_RE = re.compile(
    r"(?i)\b(password|passwd|secret|token|api_key|apikey|authorization)\s*[:=]\s*\S+"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]+")


def validate_embedding_vector(
    vector: Sequence[float],
    *,
    expected_dim: int = CANONICAL_VECTOR_DIM,
) -> list[float]:
    """Validate exact vector dimension and finite numeric values without padding or truncation."""
    if isinstance(vector, (str, bytes)) or not isinstance(vector, Sequence):
        raise ValueError("Embedding vector must be a sequence of floats.")
    if len(vector) != expected_dim:
        raise ValueError(
            f"Expected {expected_dim}-dimensional embedding vector, got {len(vector)}."
        )
    validated: list[float] = []
    for idx, val in enumerate(vector):
        if isinstance(val, bool):
            raise ValueError(f"Embedding element at index {idx} must be a float, not bool.")
        num = float(val)
        if not math.isfinite(num):
            raise ValueError(f"Embedding element at index {idx} must be finite.")
        validated.append(num)
    return validated


def sanitize_embedding_error(message: str, *, max_length: int = 500) -> str:
    """Strip stack traces, credentials, and newlines from failure messages."""
    first_line = next((line.strip() for line in message.splitlines() if line.strip()), "")
    if not first_line:
        return "Embedding generation failed."
    cleaned = _CREDENTIAL_URL_RE.sub(r"\1***:***@", first_line)
    cleaned = _SECRET_KV_RE.sub(r"\1=[REDACTED]", cleaned)
    cleaned = _BEARER_RE.sub("Bearer [REDACTED]", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned[:max_length]


class EmbeddingRepository:
    """Data access for public.opportunity_embeddings (canonical 384-dim pipeline)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_opportunity_id(self, opportunity_id: UUID) -> OpportunityEmbedding | None:
        stmt = select(OpportunityEmbedding).where(
            OpportunityEmbedding.opportunity_id == opportunity_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_opportunity_ids(
        self, opportunity_ids: Sequence[UUID]
    ) -> dict[UUID, OpportunityEmbedding]:
        """Fetch existing embedding rows for a batch of opportunity IDs in one query."""
        if not opportunity_ids:
            return {}
        stmt = select(OpportunityEmbedding).where(
            OpportunityEmbedding.opportunity_id.in_(list(opportunity_ids))
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        return {row.opportunity_id: row for row in rows}

    async def list_active_opportunities_page(
        self,
        *,
        after_id: UUID | None = None,
        limit: int = 50,
    ) -> list[Opportunity]:
        """Fetch a keyset-paginated page of active opportunities ordered by ID ascending."""
        stmt = (
            select(Opportunity)
            .where(Opportunity.is_active.is_(True))
            .options(selectinload(Opportunity.eligibility))
        )
        if after_id is not None:
            stmt = stmt.where(Opportunity.id > after_id)
        stmt = stmt.order_by(Opportunity.id.asc()).limit(max(1, min(limit, 500)))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_pending(
        self,
        opportunity_id: UUID,
        *,
        content_hash: str | None = None,
        model_id: str = CANONICAL_MODEL_ID,
        model_version: str | None = None,
    ) -> OpportunityEmbedding:
        """Idempotently mark an opportunity embedding as pending without erasing valid vectors.

        If an existing row is already 'ready' with the same content_hash, model_id, and
        model_version, it is left 'ready' and returned unchanged.
        """
        update_conditions = [
            OpportunityEmbedding.embedding_status != "ready",
            OpportunityEmbedding.content_hash.is_distinct_from(content_hash),
            OpportunityEmbedding.embedding_model_id.is_distinct_from(model_id),
        ]
        if model_version is not None:
            update_conditions.append(
                OpportunityEmbedding.embedding_model_version.is_distinct_from(model_version)
            )

        now = datetime.now(UTC)
        hash_changed = OpportunityEmbedding.content_hash.is_distinct_from(content_hash)
        stmt = (
            pg_insert(OpportunityEmbedding)
            .values(
                opportunity_id=opportunity_id,
                content_hash=content_hash,
                embedding_model_id=model_id,
                embedding_model_version=model_version,
                embedding_status="pending",
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["opportunity_id"],
                set_={
                    "content_hash": content_hash,
                    "embedding_model_id": model_id,
                    "embedding_model_version": model_version,
                    "embedding_status": "pending",
                    "retry_count": case(
                        (hash_changed, 0),
                        else_=OpportunityEmbedding.retry_count,
                    ),
                    "error_message": case(
                        (hash_changed, None),
                        else_=OpportunityEmbedding.error_message,
                    ),
                    "updated_at": now,
                },
                where=or_(*update_conditions),
            )
            .returning(OpportunityEmbedding)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        existing = await self.get_by_opportunity_id(opportunity_id)
        assert existing is not None
        return existing

    async def save_embedding(
        self,
        opportunity_id: UUID,
        vector: Sequence[float],
        *,
        content_hash: str,
        model_id: str = CANONICAL_MODEL_ID,
        model_version: str | None = None,
    ) -> OpportunityEmbedding | None:
        """Persist a validated 384-dim vector and mark status 'ready'.

        Returns None if a newer pending content_hash is already in flight so a late
        result for an outdated content_hash cannot overwrite current state.
        """
        validated = validate_embedding_vector(vector, expected_dim=CANONICAL_VECTOR_DIM)
        now = datetime.now(UTC)
        stmt = (
            pg_insert(OpportunityEmbedding)
            .values(
                opportunity_id=opportunity_id,
                embedding_minilm_384=validated,
                embedding_model_id=model_id,
                embedding_model_version=model_version,
                content_hash=content_hash,
                embedding_status="ready",
                error_message=None,
                retry_count=0,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["opportunity_id"],
                set_={
                    "embedding_minilm_384": validated,
                    "embedding_model_id": model_id,
                    "embedding_model_version": model_version,
                    "content_hash": content_hash,
                    "embedding_status": "ready",
                    "error_message": None,
                    "retry_count": 0,
                    "updated_at": now,
                },
                where=or_(
                    OpportunityEmbedding.content_hash.is_(None),
                    OpportunityEmbedding.content_hash == content_hash,
                ),
            )
            .returning(OpportunityEmbedding)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def record_failure(
        self,
        opportunity_id: UUID,
        error_message: str,
        *,
        content_hash: str,
        model_id: str = CANONICAL_MODEL_ID,
        model_version: str | None = None,
    ) -> OpportunityEmbedding | None:
        """Atomically record a sanitized failure and increment retry_count.

        Requires a non-empty content_hash and returns None if the row is already 'ready'
        or has a different content_hash, preventing late failures from overwriting
        newer pending or successful embeddings.
        """
        if not isinstance(content_hash, str) or not content_hash.strip():
            raise ValueError("content_hash must be a non-empty string when recording failure.")
        sanitized = sanitize_embedding_error(error_message)
        now = datetime.now(UTC)
        conflict_guard = and_(
            OpportunityEmbedding.embedding_status != "ready",
            or_(
                OpportunityEmbedding.content_hash.is_(None),
                OpportunityEmbedding.content_hash == content_hash,
            ),
        )

        stmt = (
            pg_insert(OpportunityEmbedding)
            .values(
                opportunity_id=opportunity_id,
                content_hash=content_hash,
                embedding_model_id=model_id,
                embedding_model_version=model_version,
                embedding_status="failed",
                error_message=sanitized,
                retry_count=1,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["opportunity_id"],
                set_={
                    "embedding_status": "failed",
                    "error_message": sanitized,
                    "retry_count": OpportunityEmbedding.retry_count + 1,
                    "updated_at": now,
                },
                where=conflict_guard,
            )
            .returning(OpportunityEmbedding)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_opportunities_without_embeddings(
        self, *, limit: int = 100, active_only: bool = True
    ) -> list[Opportunity]:
        """Return opportunities that have no OpportunityEmbedding row yet."""
        stmt = (
            select(Opportunity)
            .outerjoin(
                OpportunityEmbedding,
                OpportunityEmbedding.opportunity_id == Opportunity.id,
            )
            .where(OpportunityEmbedding.id.is_(None))
        )
        if active_only:
            stmt = stmt.where(Opportunity.is_active.is_(True))
        stmt = stmt.order_by(Opportunity.created_at.desc(), Opportunity.id.desc()).limit(
            max(1, min(limit, 500))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        statuses: Sequence[str] = ("pending", "failed"),
        *,
        limit: int = 100,
    ) -> list[OpportunityEmbedding]:
        """Return embedding records matching any of the given statuses."""
        stmt = (
            select(OpportunityEmbedding)
            .where(OpportunityEmbedding.embedding_status.in_(list(statuses)))
            .order_by(OpportunityEmbedding.updated_at.asc(), OpportunityEmbedding.id.asc())
            .limit(max(1, min(limit, 500)))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_stale_or_missing_opportunity_ids(
        self,
        current_hashes: dict[UUID, str],
        *,
        model_id: str = CANONICAL_MODEL_ID,
        model_version: str | None = None,
    ) -> list[UUID]:
        """Identify opportunity IDs with missing, non-ready, or hash/model-mismatched embeddings."""
        if not current_hashes:
            return []
        stmt = select(OpportunityEmbedding).where(
            OpportunityEmbedding.opportunity_id.in_(list(current_hashes.keys()))
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        by_opp_id = {row.opportunity_id: row for row in rows}

        stale_ids: list[UUID] = []
        for opp_id, expected_hash in current_hashes.items():
            rec = by_opp_id.get(opp_id)
            if (
                rec is None
                or rec.embedding_status != "ready"
                or rec.embedding_minilm_384 is None
                or rec.content_hash != expected_hash
                or rec.embedding_model_id != model_id
                or (model_version is not None and rec.embedding_model_version != model_version)
            ):
                stale_ids.append(opp_id)
        return stale_ids

    async def search_similar_by_vector(
        self,
        query_vector: Sequence[float],
        *,
        limit: int = 10,
        active_only: bool = True,
        model_id: str | None = CANONICAL_MODEL_ID,
        model_version: str | None = None,
    ) -> list[tuple[Opportunity, float]]:
        """Query canonical 384-dim pgvector cosine similarity over ready embeddings."""
        validated = validate_embedding_vector(query_vector, expected_dim=CANONICAL_VECTOR_DIM)
        distance_expr = OpportunityEmbedding.embedding_minilm_384.cosine_distance(validated).label(
            "distance"
        )

        stmt = (
            select(Opportunity, distance_expr)
            .join(OpportunityEmbedding, OpportunityEmbedding.opportunity_id == Opportunity.id)
            .where(
                OpportunityEmbedding.embedding_minilm_384.is_not(None),
                OpportunityEmbedding.embedding_status == "ready",
            )
            .options(selectinload(Opportunity.eligibility))
        )
        if active_only:
            stmt = stmt.where(Opportunity.is_active.is_(True))
        if model_id is not None:
            stmt = stmt.where(OpportunityEmbedding.embedding_model_id == model_id)
        if model_version is not None:
            stmt = stmt.where(OpportunityEmbedding.embedding_model_version == model_version)

        stmt = stmt.order_by(distance_expr.asc()).limit(max(1, min(limit, 50)))
        rows = (await self._session.execute(stmt)).all()
        return [(opp, float(1.0 - dist)) for opp, dist in rows]
