"""WS2-D-2 embedding producer helper and single-opportunity ARQ worker job."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.ml.embeddings import CanonicalEmbeddingAdapter, EmbeddingSubsystemUnavailableError
from app.models.entities import Opportunity, OpportunityEmbedding
from app.repositories.embeddings import CANONICAL_MODEL_ID, EmbeddingRepository
from app.services.opportunity_text import build_opportunity_embedding_payload

logger = logging.getLogger("opportunity_os.tasks.embeddings")

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_BASE_BACKOFF_SECONDS = 5
_MAX_BACKOFF_SECONDS = 60


async def _load_active_opportunity(
    session: AsyncSession, opportunity_id: UUID
) -> Opportunity | None:
    stmt = (
        select(Opportunity)
        .where(Opportunity.id == opportunity_id, Opportunity.is_active.is_(True))
        .options(selectinload(Opportunity.eligibility))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _compute_backoff_seconds(job_try: int) -> int:
    exponent = max(0, job_try - 1)
    delay = _BASE_BACKOFF_SECONDS * (2**exponent)
    return int(min(_MAX_BACKOFF_SECONDS, delay))


def _is_permanent_model_error(exc: EmbeddingSubsystemUnavailableError) -> bool:
    msg = str(exc).lower()
    return "provenance" in msg or "only supports" in msg or "must not be empty" in msg


async def enqueue_embed_opportunity(
    session_factory: async_sessionmaker[AsyncSession],
    arq_pool: Any,
    opportunity_id: UUID,
    *,
    verify_model_version: bool = False,
) -> dict[str, Any]:
    """Register pending embedding state in its own short-lived transaction, then enqueue ARQ job.

    The caller must have already committed the Opportunity transaction. Never commits any
    caller-owned session.
    """
    async with session_factory() as session:
        opp = await _load_active_opportunity(session, opportunity_id)
        if opp is None:
            return {
                "status": "missing_or_inactive",
                "opportunity_id": str(opportunity_id),
            }

        _, current_hash = build_opportunity_embedding_payload(opp)
        emb_repo = EmbeddingRepository(session)
        existing = await emb_repo.get_by_opportunity_id(opp.id)

        if (
            existing is not None
            and existing.embedding_status == "ready"
            and existing.content_hash == current_hash
            and existing.embedding_model_id == CANONICAL_MODEL_ID
        ):
            if not verify_model_version:
                return {
                    "status": "already_ready",
                    "opportunity_id": str(opp.id),
                    "content_hash": current_hash,
                }
            enqueue_status = "validation_enqueued"
        else:
            await emb_repo.upsert_pending(
                opp.id,
                content_hash=current_hash,
                model_id=CANONICAL_MODEL_ID,
                model_version=None,
            )
            await session.commit()
            enqueue_status = "pending_enqueued"

    job_id = f"embed:{opp.id}:{current_hash}"
    try:
        job = await arq_pool.enqueue_job(
            "embed_opportunity",
            str(opp.id),
            current_hash,
            _job_id=job_id,
        )
    except (RedisError, OSError):
        logger.warning(
            "Failed to enqueue embedding job for opportunity_id=%s.",
            opp.id,
        )
        return {
            "status": "enqueue_failed",
            "opportunity_id": str(opp.id),
            "content_hash": current_hash,
        }

    return {
        "status": enqueue_status,
        "opportunity_id": str(opp.id),
        "content_hash": current_hash,
        "job_id": getattr(job, "job_id", job_id) if job is not None else job_id,
        "deduplicated": job is None,
    }


async def _record_failure_safely(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    opportunity_id: UUID,
    content_hash: str,
    error_message: str,
    model_id: str,
    model_version: str | None,
) -> None:
    """Persist failure in a fresh session, guarded by content_hash and non-ready status."""
    try:
        async with session_factory() as session:
            await EmbeddingRepository(session).record_failure(
                opportunity_id,
                error_message,
                content_hash=content_hash,
                model_id=model_id,
                model_version=model_version,
            )
            await session.commit()
    except (SQLAlchemyError, OSError):
        logger.warning(
            "Failed to persist embedding failure record for opportunity_id=%s.",
            opportunity_id,
        )


async def embed_opportunity(
    ctx: dict[str, Any],
    opportunity_id: str,
    expected_content_hash: str,
) -> dict[str, Any]:
    """Process one queued opportunity embedding job with strict stale-hash & provenance checks."""
    try:
        opp_uuid = UUID(str(opportunity_id))
    except (ValueError, TypeError):
        return {"status": "invalid_payload", "reason": "invalid_opportunity_id"}

    if not isinstance(expected_content_hash, str) or not _SHA256_HEX_RE.match(
        expected_content_hash
    ):
        return {"status": "invalid_payload", "reason": "invalid_expected_content_hash"}

    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    adapter: CanonicalEmbeddingAdapter = ctx["embedding_adapter"]
    job_try = int(ctx.get("job_try", 1))
    max_tries = int(ctx.get("max_tries", settings.ARQ_MAX_TRIES))

    # 1. Read & verify state in a short-lived read-only session (never held during inference)
    async with session_factory() as session:
        opp = await _load_active_opportunity(session, opp_uuid)
        if opp is None:
            return {"status": "missing_or_inactive", "opportunity_id": str(opp_uuid)}

        canonical_text, current_hash = build_opportunity_embedding_payload(opp)
        if current_hash != expected_content_hash:
            return {
                "status": "stale_skipped",
                "opportunity_id": str(opp_uuid),
                "reason": "opportunity_hash_changed",
            }

        row = await EmbeddingRepository(session).get_by_opportunity_id(opp_uuid)
        if row is None or row.content_hash != expected_content_hash:
            return {
                "status": "stale_skipped",
                "opportunity_id": str(opp_uuid),
                "reason": "embedding_row_missing_or_hash_mismatch",
            }

        row_status = row.embedding_status
        row_model_id = row.embedding_model_id
        row_model_version = row.embedding_model_version

    # 2. Resolve model provenance lazily outside any DB transaction
    from app.tasks.worker import ensure_worker_model_loaded

    try:
        model_id, resolved_version = await ensure_worker_model_loaded(ctx)
    except EmbeddingSubsystemUnavailableError as exc:
        if _is_permanent_model_error(exc):
            await _record_failure_safely(
                session_factory,
                opportunity_id=opp_uuid,
                content_hash=current_hash,
                error_message=str(exc),
                model_id=adapter.model_id,
                model_version=adapter.resolved_model_version,
            )
            return {"status": "failed_permanent", "opportunity_id": str(opp_uuid)}

        await _record_failure_safely(
            session_factory,
            opportunity_id=opp_uuid,
            content_hash=current_hash,
            error_message=str(exc),
            model_id=adapter.model_id,
            model_version=adapter.resolved_model_version,
        )
        if job_try < max_tries:
            from arq import Retry

            raise Retry(defer=_compute_backoff_seconds(job_try)) from exc
        return {"status": "failed_max_retries", "opportunity_id": str(opp_uuid)}

    # 3. Reuse ready row only when hash, model_id, AND resolved_version all match
    if (
        row_status == "ready"
        and row_model_id == model_id
        and row_model_version == resolved_version
    ):
        return {
            "status": "already_ready",
            "opportunity_id": str(opp_uuid),
            "content_hash": current_hash,
            "model_id": model_id,
            "model_version": resolved_version,
        }

    # 4. Run blocking CPU inference outside any DB transaction
    try:
        vector, inf_model_id, inf_model_version = await asyncio.to_thread(
            adapter.embed_one, canonical_text
        )
    except ValueError as exc:
        await _record_failure_safely(
            session_factory,
            opportunity_id=opp_uuid,
            content_hash=current_hash,
            error_message=str(exc),
            model_id=model_id,
            model_version=resolved_version,
        )
        return {"status": "failed_permanent", "opportunity_id": str(opp_uuid)}
    except EmbeddingSubsystemUnavailableError as exc:
        await _record_failure_safely(
            session_factory,
            opportunity_id=opp_uuid,
            content_hash=current_hash,
            error_message=str(exc),
            model_id=model_id,
            model_version=resolved_version,
        )
        if job_try < max_tries:
            from arq import Retry

            raise Retry(defer=_compute_backoff_seconds(job_try)) from exc
        return {"status": "failed_max_retries", "opportunity_id": str(opp_uuid)}

    # 5. Persist vector in a fresh short-lived session
    async with session_factory() as session:
        saved = await EmbeddingRepository(session).save_embedding(
            opp_uuid,
            vector,
            content_hash=current_hash,
            model_id=inf_model_id,
            model_version=inf_model_version,
        )
        await session.commit()

    if saved is None:
        return {
            "status": "stale_skipped",
            "opportunity_id": str(opp_uuid),
            "reason": "save_lost_hash_race",
        }

    return {
        "status": "ready",
        "opportunity_id": str(opp_uuid),
        "content_hash": current_hash,
        "model_id": inf_model_id,
        "model_version": inf_model_version,
    }


def _should_backfill_row(
    existing: OpportunityEmbedding | None,
    *,
    current_hash: str,
    active_model_id: str,
    active_model_version: str,
    max_tries: int,
    stale_pending_cutoff: datetime,
) -> bool:
    """Return True if an active opportunity requires pending registration & embedding."""
    if existing is None:
        return True

    status = existing.embedding_status
    if status == "ready":
        return (
            existing.content_hash != current_hash
            or existing.embedding_model_id != active_model_id
            or existing.embedding_model_version != active_model_version
        )

    if status == "failed":
        if existing.content_hash != current_hash:
            return True
        return existing.retry_count < max_tries

    if status == "pending":
        if existing.content_hash != current_hash:
            return True
        updated_at = existing.updated_at
        if updated_at is None:
            return True
        aware_updated = updated_at if updated_at.tzinfo is not None else updated_at.replace(tzinfo=UTC)
        return aware_updated <= stale_pending_cutoff

    return True


async def backfill_missing_embeddings(
    ctx: dict[str, Any],
    *,
    batch_size: int = 50,
    max_scanned: int = 500,
    max_enqueued: int = 200,
    after_id: str | None = None,
    stale_pending_seconds: int = 600,
) -> dict[str, Any]:
    """Keyset-paginated, resumable backfill for missing, stale, failed, and upgraded embeddings."""
    if batch_size < 1 or max_scanned < 1 or max_enqueued < 1 or stale_pending_seconds < 0:
        raise ValueError("Backfill bounds must be positive (stale_pending_seconds >= 0).")

    cursor_uuid: UUID | None = None
    if after_id is not None:
        cursor_uuid = UUID(str(after_id))

    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    arq_pool = ctx.get("arq_pool") or ctx.get("redis")
    if arq_pool is None:
        raise RuntimeError("ARQ Redis pool is required in worker ctx for backfill.")
    max_tries = int(ctx.get("max_tries", settings.ARQ_MAX_TRIES))

    # Resolve active model ID & version BEFORE evaluating ready-row reuse
    from app.tasks.worker import ensure_worker_model_loaded

    active_model_id, active_model_version = await ensure_worker_model_loaded(ctx)

    scanned = 0
    enqueued = 0
    skipped = 0
    last_processed_id = cursor_uuid
    completed = False

    while scanned < max_scanned and enqueued < max_enqueued:
        page_limit = min(batch_size, max_scanned - scanned)
        to_enqueue: list[tuple[UUID, str]] = []
        stopped_for_enqueue_cap = False

        async with session_factory() as session:
            emb_repo = EmbeddingRepository(session)
            page = await emb_repo.list_active_opportunities_page(
                after_id=last_processed_id,
                limit=page_limit,
            )
            if not page:
                completed = True
                break

            existing_map = await emb_repo.get_by_opportunity_ids([opp.id for opp in page])
            stale_cutoff = datetime.now(UTC) - timedelta(seconds=stale_pending_seconds)

            for opp in page:
                if enqueued + len(to_enqueue) >= max_enqueued:
                    stopped_for_enqueue_cap = True
                    break

                scanned += 1
                last_processed_id = opp.id
                _, current_hash = build_opportunity_embedding_payload(opp)
                existing = existing_map.get(opp.id)

                if _should_backfill_row(
                    existing,
                    current_hash=current_hash,
                    active_model_id=active_model_id,
                    active_model_version=active_model_version,
                    max_tries=max_tries,
                    stale_pending_cutoff=stale_cutoff,
                ):
                    await emb_repo.upsert_pending(
                        opp.id,
                        content_hash=current_hash,
                        model_id=active_model_id,
                        model_version=active_model_version,
                    )
                    to_enqueue.append((opp.id, current_hash))
                else:
                    skipped += 1

            if to_enqueue:
                await session.commit()

        # Enqueue outside DB session after pending commit
        for opp_id, content_hash in to_enqueue:
            try:
                await arq_pool.enqueue_job(
                    "embed_opportunity",
                    str(opp_id),
                    content_hash,
                    _job_id=f"embed:{opp_id}:{content_hash}",
                )
                enqueued += 1
            except (RedisError, OSError):
                logger.warning(
                    "Backfill failed to enqueue opportunity_id=%s; row remains pending.",
                    opp_id,
                )

        if stopped_for_enqueue_cap:
            completed = False
            break

        if len(page) < page_limit:
            completed = True
            break

        if enqueued >= max_enqueued or scanned >= max_scanned:
            completed = False
            break

    return {
        "scanned": scanned,
        "enqueued": enqueued,
        "skipped": skipped,
        "next_cursor": str(last_processed_id) if last_processed_id is not None else None,
        "completed": completed,
    }
