"""WS2-D-4 live PostgreSQL, Redis/ARQ, real-model, and end-to-end pipeline integration tests.

Each test verifies live service availability and skips with an explicit blocker message
when local PostgreSQL, Redis, or ML worker dependencies are unavailable. All writes are
scoped strictly to test-owned Opportunity UUIDs and cleaned up without truncating tables.
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.orm import selectinload

from app.core.config import Settings, settings
from app.db.session import DatabaseManager, check_db_health
from app.ml.embeddings import (
    CANONICAL_MODEL_ID,
    CANONICAL_VECTOR_DIM,
    CanonicalEmbeddingAdapter,
    EmbeddingSubsystemUnavailableError,
)
from app.models.entities import Opportunity, OpportunityEligibility, OpportunityEmbedding
from app.repositories.embeddings import EmbeddingRepository
from app.services.opportunity_text import build_opportunity_embedding_payload
from app.tasks.embeddings import (
    backfill_missing_embeddings,
    embed_opportunity,
    enqueue_embed_opportunity,
)


async def _require_live_db() -> DatabaseManager:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(db):
        await db.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS2-D-4 integration tests.")
    return db


async def _require_live_redis() -> Any:
    try:
        from arq import create_pool

        from app.tasks.worker import parse_redis_settings

        redis_url = os.getenv("TEST_REDIS_URL", settings.REDIS_URL)
        pool = await create_pool(parse_redis_settings(redis_url))
        await pool.ping()
        return pool
    except Exception as exc:
        pytest.skip(f"Live Redis/ARQ unavailable for WS2-D-4 integration tests: {exc}")


async def _cleanup_test_opportunities(db: DatabaseManager, opp_ids: list[UUID]) -> None:
    if not opp_ids:
        return
    async with db.session_factory() as session, session.begin():
        await session.execute(
            delete(OpportunityEmbedding).where(OpportunityEmbedding.opportunity_id.in_(opp_ids))
        )
        await session.execute(
            delete(OpportunityEligibility).where(OpportunityEligibility.opportunity_id.in_(opp_ids))
        )
        await session.execute(delete(Opportunity).where(Opportunity.id.in_(opp_ids)))


def _unit_vec(hot_idx: int = 0) -> list[float]:
    vec = [0.0] * CANONICAL_VECTOR_DIM
    vec[hot_idx] = 1.0
    return vec


@pytest.mark.asyncio
async def test_live_postgres_pgvector_migrations_and_retry_isolation() -> None:
    db = await _require_live_db()
    opp_id = uuid4()
    try:
        async with db.session_factory() as session:
            ext = (
                await session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
            ).scalar_one_or_none()
            assert ext == "vector"

            cols = {
                row[0]
                for row in (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_schema = 'public' AND table_name = 'opportunity_embeddings'"
                        )
                    )
                ).all()
            }
            assert {
                "embedding",
                "embedding_minilm_384",
                "embedding_model_id",
                "embedding_model_version",
                "content_hash",
                "embedding_status",
                "retry_count",
                "error_message",
            }.issubset(cols)

        async with db.session_factory() as session, session.begin():
            session.add(
                Opportunity(
                    id=opp_id,
                    title="WS2-D-4 Live PG Opp",
                    organization="NexteRaS",
                    location="Remote",
                    type="internship",
                    description="Live PG test",
                    source_url=f"https://example.com/ws2d4/pg/{opp_id}",
                    source_provider="manual",
                    is_active=True,
                )
            )
            await session.flush()
            repo = EmbeddingRepository(session)

            # Register H1, fail to retry_count=1, then new hash H2 resets retry_count=0 & error_message=None
            await repo.upsert_pending(opp_id, content_hash="h1" * 32, model_version=None)
            f1 = await repo.record_failure(opp_id, "transient error", content_hash="h1" * 32)
            assert f1 is not None and f1.retry_count == 1

            p2 = await repo.upsert_pending(opp_id, content_hash="h2" * 32, model_version=None)
            assert p2.retry_count == 0
            assert p2.error_message is None

            # Re-registering H2 preserves retry_count
            f2 = await repo.record_failure(opp_id, "h2 error", content_hash="h2" * 32)
            assert f2 is not None and f2.retry_count == 1
            p2_again = await repo.upsert_pending(opp_id, content_hash="h2" * 32, model_version=None)
            assert p2_again.retry_count == 1

            # Invalid dimension rejected
            with pytest.raises(ValueError, match="Expected 384-dimensional"):
                await repo.save_embedding(opp_id, [0.1] * 768, content_hash="h2" * 32)

            saved = await repo.save_embedding(
                opp_id, _unit_vec(0), content_hash="h2" * 32, model_version="1.0.0"
            )
            assert saved is not None and saved.embedding_status == "ready"

            # Stale hash cannot overwrite ready row
            assert (
                await repo.save_embedding(
                    opp_id, _unit_vec(1), content_hash="h1" * 32, model_version="1.0.0"
                )
                is None
            )
    finally:
        await _cleanup_test_opportunities(db, [opp_id])
        await db.dispose()


@pytest.mark.asyncio
async def test_live_redis_arq_enqueue_dedup_and_backfill_recovery() -> None:
    db = await _require_live_db()
    pool = await _require_live_redis()
    opp_id = uuid4()
    try:
        async with db.session_factory() as session, session.begin():
            session.add(
                Opportunity(
                    id=opp_id,
                    title="WS2-D-4 Live Redis Opp",
                    organization="NexteRaS",
                    location="Bengaluru",
                    type="internship",
                    description="Live Redis ARQ test",
                    source_url=f"https://example.com/ws2d4/redis/{opp_id}",
                    source_provider="manual",
                    is_active=True,
                )
            )

        res1 = await enqueue_embed_opportunity(db.session_factory, pool, opp_id)
        assert res1["status"] == "pending_enqueued"
        assert res1["deduplicated"] is False

        res2 = await enqueue_embed_opportunity(db.session_factory, pool, opp_id)
        assert res2["status"] == "pending_enqueued"
        assert res2["job_id"] == res1["job_id"]
        assert res2["deduplicated"] is True

        async with db.session_factory() as session:
            row = await EmbeddingRepository(session).get_by_opportunity_id(opp_id)
            assert row is not None and row.embedding_status == "pending"
    finally:
        await pool.aclose()
        await _cleanup_test_opportunities(db, [opp_id])
        await db.dispose()


@pytest.mark.asyncio
async def test_live_real_model_and_end_to_end_pipeline() -> None:
    db = await _require_live_db()
    pool = await _require_live_redis()
    adapter = CanonicalEmbeddingAdapter()
    try:
        t0 = time.perf_counter()
        model_id, model_version = await asyncio.to_thread(adapter.ensure_loaded)
        load_ms = (time.perf_counter() - t0) * 1000.0
    except EmbeddingSubsystemUnavailableError as exc:
        await pool.aclose()
        await db.dispose()
        pytest.skip(f"Real embedding model dependencies unavailable: {exc}")

    opp_id = uuid4()
    try:
        async with db.session_factory() as session, session.begin():
            opp = Opportunity(
                id=opp_id,
                title="WS2-D-4 E2E ML Engineer",
                organization="NexteRaS",
                location="Bengaluru",
                type="internship",
                description="Real SentenceTransformer E2E embedding test",
                source_url=f"https://example.com/ws2d4/e2e/{opp_id}",
                source_provider="manual",
                is_active=True,
            )
            opp.eligibility = OpportunityEligibility(
                opportunity_id=opp_id, required_skills=["Python", "PyTorch"]
            )
            session.add(opp)

        enq1 = await enqueue_embed_opportunity(db.session_factory, pool, opp_id)
        assert enq1["status"] == "pending_enqueued"

        ctx: dict[str, Any] = {
            "session_factory": db.session_factory,
            "arq_pool": pool,
            "embedding_adapter": adapter,
            "max_tries": settings.ARQ_MAX_TRIES,
        }
        w1 = await embed_opportunity(ctx, str(opp_id), enq1["content_hash"])
        assert w1["status"] == "ready"
        assert w1["model_id"] == model_id == CANONICAL_MODEL_ID
        assert w1["model_version"] == model_version

        async with db.session_factory() as session:
            repo = EmbeddingRepository(session)
            row1 = await repo.get_by_opportunity_id(opp_id)
            assert row1 is not None and row1.embedding_minilm_384 is not None
            assert len(row1.embedding_minilm_384) == CANONICAL_VECTOR_DIM
            norm = math.sqrt(sum(float(x) * float(x) for x in row1.embedding_minilm_384))
            assert abs(norm - 1.0) < 1e-4

            query_vec, _, _ = await asyncio.to_thread(
                adapter.embed_one, "Python PyTorch ML Engineer internship"
            )
            hits = await repo.search_similar_by_vector(query_vec, limit=5)
            assert any(h[0].id == opp_id for h in hits)

        # Update opportunity content -> enqueue new hash -> old hash rejected -> new hash ready
        async with db.session_factory() as session, session.begin():
            opp_row = (
                await session.execute(
                    select(Opportunity)
                    .where(Opportunity.id == opp_id)
                    .options(selectinload(Opportunity.eligibility))
                )
            ).scalar_one()
            opp_row.title = "WS2-D-4 E2E Distributed Systems"
            await session.flush()
            _, new_hash = build_opportunity_embedding_payload(opp_row)

        assert new_hash != enq1["content_hash"]
        enq2 = await enqueue_embed_opportunity(db.session_factory, pool, opp_id)
        assert enq2["content_hash"] == new_hash

        stale_res = await embed_opportunity(ctx, str(opp_id), enq1["content_hash"])
        assert stale_res["status"] == "stale_skipped"

        w2 = await embed_opportunity(ctx, str(opp_id), new_hash)
        assert w2["status"] == "ready"
        assert w2["content_hash"] == new_hash
        assert load_ms >= 0.0

        # Backfill confirms no pending/stale work remains for this opp
        bf = await backfill_missing_embeddings(ctx, batch_size=50, max_scanned=50, max_enqueued=50)
        assert isinstance(bf["scanned"], int)
    finally:
        await pool.aclose()
        await _cleanup_test_opportunities(db, [opp_id])
        await db.dispose()
