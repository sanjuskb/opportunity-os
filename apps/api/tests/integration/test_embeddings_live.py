"""Live PostgreSQL 17 + pgvector integration tests for WS2-B EmbeddingRepository."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings, settings
from app.db.session import DatabaseManager, check_db_health
from app.models.entities import Opportunity
from app.repositories.embeddings import CANONICAL_MODEL_ID, EmbeddingRepository


async def _ensure_live_db() -> DatabaseManager:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(db):
        await db.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for WS2-B embedding integration tests")
    return db


def _unit_vec(hot_idx: int = 0) -> list[float]:
    vec = [0.0] * 384
    vec[hot_idx] = 1.0
    return vec


@pytest.mark.asyncio
async def test_embedding_constraints_upserts_concurrency_and_search_live() -> None:
    db = await _ensure_live_db()
    opp_ready_id = uuid4()
    opp_pending_id = uuid4()
    opp_missing_id = uuid4()

    try:
        async with db.session_factory() as session, session.begin():
            for idx, oid in enumerate((opp_ready_id, opp_pending_id, opp_missing_id)):
                session.add(
                    Opportunity(
                        id=oid,
                        title=f"WS2-B Vector Opp {idx}",
                        organization="NexteRaS",
                        location="Remote",
                        type="internship",
                        description="Vector test opportunity",
                        source_url=f"https://example.com/ws2b/{oid}",
                        source_provider="manual",
                        is_active=True,
                    )
                )
            await session.flush()

            repo = EmbeddingRepository(session)

            # 1. Idempotent upsert_pending
            p1 = await repo.upsert_pending(
                opp_ready_id, content_hash="hash_v1", model_version="1.0.0"
            )
            p2 = await repo.upsert_pending(
                opp_ready_id, content_hash="hash_v1", model_version="1.0.0"
            )
            assert p1.id == p2.id
            assert p2.embedding_status == "pending"

            # 2. record_failure increments retry_count atomically and rejects stale/hashless failures
            f1 = await repo.record_failure(
                opp_ready_id,
                "ConnectionError: password=secret123\nTraceback...",
                content_hash="hash_v1",
            )
            assert f1 is not None and f1.retry_count == 1
            assert "secret123" not in (f1.error_message or "")

            f2 = await repo.record_failure(
                opp_ready_id,
                "Second transient failure",
                content_hash="hash_v1",
            )
            assert f2 is not None and f2.retry_count == 2

            # Same-hash retry can still succeed and reset retry_count/error_message
            retried_ok = await repo.save_embedding(
                opp_ready_id,
                _unit_vec(1),
                content_hash="hash_v1",
                model_version="1.0.0",
            )
            assert retried_ok is not None
            assert retried_ok.embedding_status == "ready"
            assert retried_ok.retry_count == 0
            assert retried_ok.error_message is None

            # 3. Worker B queues hash_v2: stale hash_v1 save and stale hash_v1 failure are both rejected
            await repo.upsert_pending(
                opp_ready_id, content_hash="hash_v2", model_version="1.0.0"
            )
            stale_save_pending = await repo.save_embedding(
                opp_ready_id,
                _unit_vec(0),
                content_hash="hash_v1",
                model_version="1.0.0",
            )
            assert stale_save_pending is None
            stale_fail_pending = await repo.record_failure(
                opp_ready_id, "late fail for hash_v1", content_hash="hash_v1"
            )
            assert stale_fail_pending is None

            # 4. Worker B saves hash_v2 -> ready; late Worker A save for hash_v1 MUST still be rejected
            saved = await repo.save_embedding(
                opp_ready_id,
                _unit_vec(0),
                content_hash="hash_v2",
                model_version="1.0.0",
            )
            assert saved is not None
            assert saved.embedding_status == "ready"
            assert saved.error_message is None
            assert saved.retry_count == 0

            late_save_after_ready = await repo.save_embedding(
                opp_ready_id,
                _unit_vec(2),
                content_hash="hash_v1",
                model_version="1.0.0",
            )
            assert late_save_after_ready is None
            still_v2 = await repo.get_by_opportunity_id(opp_ready_id)
            assert still_v2 is not None
            assert still_v2.content_hash == "hash_v2"
            assert still_v2.embedding_status == "ready"

            # 5. Late failure cannot overwrite a 'ready' embedding (same or stale hash)
            late_fail = await repo.record_failure(
                opp_ready_id, "late timeout", content_hash="hash_v2"
            )
            assert late_fail is None

            # 6. Pending row is excluded from similarity search; ready row is returned
            await repo.upsert_pending(
                opp_pending_id, content_hash="hash_p", model_version="1.0.0"
            )
            results = await repo.search_similar_by_vector(
                _unit_vec(0), limit=5, model_id=CANONICAL_MODEL_ID
            )
            returned_ids = {opp.id for opp, _ in results}
            assert opp_ready_id in returned_ids
            assert opp_pending_id not in returned_ids

            # 7. Missing & stale lookups
            missing = await repo.list_opportunities_without_embeddings(limit=50)
            assert any(o.id == opp_missing_id for o in missing)

            stale_ids = await repo.list_stale_or_missing_opportunity_ids(
                {opp_ready_id: "hash_v2", opp_pending_id: "hash_p", opp_missing_id: "hash_m"},
                model_version="1.0.0",
            )
            assert set(stale_ids) == {opp_pending_id, opp_missing_id}

            # 8. DB CHECK constraints reject invalid status, negative retry_count, and ready+NULL vector
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(
                        text(
                            "INSERT INTO public.opportunity_embeddings "
                            "(opportunity_id, embedding_status) VALUES (:oid, 'invalid')"
                        ),
                        {"oid": opp_missing_id},
                    )
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(
                        text(
                            "INSERT INTO public.opportunity_embeddings "
                            "(opportunity_id, retry_count) VALUES (:oid, -1)"
                        ),
                        {"oid": opp_missing_id},
                    )
            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await session.execute(
                        text(
                            "INSERT INTO public.opportunity_embeddings "
                            "(opportunity_id, embedding_status, embedding_minilm_384) "
                            "VALUES (:oid, 'ready', NULL)"
                        ),
                        {"oid": opp_missing_id},
                    )
    finally:
        await db.dispose()
