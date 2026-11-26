"""Unit tests for WS2-D-3 resumable embedding backfill pipeline & model-version migration."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from redis.exceptions import RedisError

from app.ml import (
    CANONICAL_FINETUNED_VERSION,
    CANONICAL_MODEL_ID,
    CANONICAL_PRETRAINED_VERSION,
    CANONICAL_VECTOR_DIM,
    CanonicalEmbeddingAdapter,
)
from app.models.entities import Opportunity, OpportunityEligibility, OpportunityEmbedding
from app.services.opportunity_text import build_opportunity_embedding_payload
from app.tasks import embeddings as tasks_embeddings_module


def _unit_vec() -> list[float]:
    vec = [0.0] * CANONICAL_VECTOR_DIM
    vec[0] = 1.0
    return vec


class _FakeEncoder:
    def __init__(self, *, using_finetuned: bool = True) -> None:
        self.using_finetuned_checkpoint = using_finetuned

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [_unit_vec() for _ in texts]


def _make_opp(opp_id: UUID, title: str = "Opp") -> Opportunity:
    opp = Opportunity(
        id=opp_id,
        title=title,
        organization="NexteRaS",
        location="Bengaluru",
        type="internship",
        description="Backend internship",
        source_url=f"https://example.com/{opp_id}",
        source_provider="manual",
        is_active=True,
    )
    opp.eligibility = OpportunityEligibility(opportunity_id=opp_id, required_skills=["Python"])
    return opp


class _InMemoryBackfillEnv:
    def __init__(self, opps: list[Opportunity]) -> None:
        self.opps = sorted(opps, key=lambda o: o.id)
        self.rows: dict[UUID, OpportunityEmbedding] = {}
        self.commits = 0
        self.page_queries = 0
        self.batch_queries = 0

    def session_factory(self) -> Any:
        env = self

        @asynccontextmanager
        async def _ctx() -> Any:
            class _Sess:
                async def commit(self) -> None:
                    env.commits += 1

            yield _Sess()

        return _ctx

    def make_repo(self, _session: Any) -> Any:
        env = self

        class _FakeRepo:
            async def list_active_opportunities_page(
                self, *, after_id: UUID | None = None, limit: int = 50
            ) -> list[Opportunity]:
                env.page_queries += 1
                eligible = [
                    o for o in env.opps if o.is_active and (after_id is None or o.id > after_id)
                ]
                return eligible[:limit]

            async def get_by_opportunity_id(self, opp_id: UUID) -> OpportunityEmbedding | None:
                return env.rows.get(opp_id)

            async def get_by_opportunity_ids(
                self, opp_ids: Sequence[UUID]
            ) -> dict[UUID, OpportunityEmbedding]:
                env.batch_queries += 1
                return {oid: env.rows[oid] for oid in opp_ids if oid in env.rows}

            async def upsert_pending(self, opp_id: UUID, **kwargs: Any) -> OpportunityEmbedding:
                existing = env.rows.get(opp_id)
                incoming_hash = kwargs["content_hash"]
                incoming_model_id = kwargs["model_id"]
                incoming_version = kwargs["model_version"]
                if (
                    existing is not None
                    and existing.embedding_status == "ready"
                    and existing.content_hash == incoming_hash
                    and existing.embedding_model_id == incoming_model_id
                    and (
                        incoming_version is None
                        or existing.embedding_model_version == incoming_version
                    )
                ):
                    return existing

                hash_changed = existing is None or existing.content_hash != incoming_hash
                row = OpportunityEmbedding(
                    opportunity_id=opp_id,
                    content_hash=incoming_hash,
                    embedding_model_id=incoming_model_id,
                    embedding_model_version=incoming_version,
                    embedding_status="pending",
                    retry_count=0 if hash_changed else existing.retry_count,
                    error_message=None if hash_changed else existing.error_message,
                    updated_at=datetime.now(UTC),
                )
                env.rows[opp_id] = row
                return row

        return _FakeRepo()


class _FakeArqPool:
    def __init__(self, *, fail_on_ids: set[str] | None = None) -> None:
        self.enqueued: list[tuple[str, str, str, str]] = []
        self.fail_on_ids = fail_on_ids or set()

    async def enqueue_job(self, fn_name: str, opp_id: str, content_hash: str, **kwargs: Any) -> Any:
        if opp_id in self.fail_on_ids:
            raise RedisError("redis timeout")
        self.enqueued.append((fn_name, opp_id, content_hash, kwargs["_job_id"]))
        return {"job_id": kwargs["_job_id"]}


@pytest.mark.asyncio
async def test_backfill_candidate_rules_and_model_version_migration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    ids = sorted([uuid4() for _ in range(9)])
    opps = [_make_opp(oid, f"Opp {idx}") for idx, oid in enumerate(ids)]
    hashes = {opp.id: build_opportunity_embedding_payload(opp)[1] for opp in opps}

    env = _InMemoryBackfillEnv(opps)
    # 0: missing
    # 1: ready + matching hash + matching model_id + matching model_version -> SKIP
    env.rows[ids[1]] = OpportunityEmbedding(
        opportunity_id=ids[1],
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_FINETUNED_VERSION,
        content_hash=hashes[ids[1]],
        embedding_status="ready",
    )
    # 2: ready + old model_version -> MIGRATE
    env.rows[ids[2]] = OpportunityEmbedding(
        opportunity_id=ids[2],
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_PRETRAINED_VERSION,
        content_hash=hashes[ids[2]],
        embedding_status="ready",
    )
    # 3: ready + old model_id -> MIGRATE
    env.rows[ids[3]] = OpportunityEmbedding(
        opportunity_id=ids[3],
        embedding_minilm_384=_unit_vec(),
        embedding_model_id="legacy-model",
        embedding_model_version="0.1.0",
        content_hash=hashes[ids[3]],
        embedding_status="ready",
    )
    # 4: ready + stale content_hash -> ENQUEUE
    env.rows[ids[4]] = OpportunityEmbedding(
        opportunity_id=ids[4],
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_FINETUNED_VERSION,
        content_hash="0" * 64,
        embedding_status="ready",
    )
    # 5: failed below retry limit (retry_count=2 < max_tries=3) -> ENQUEUE
    env.rows[ids[5]] = OpportunityEmbedding(
        opportunity_id=ids[5],
        content_hash=hashes[ids[5]],
        embedding_status="failed",
        retry_count=2,
    )
    # 6: failed at retry limit (retry_count=3 >= max_tries=3) -> SKIP
    env.rows[ids[6]] = OpportunityEmbedding(
        opportunity_id=ids[6],
        content_hash=hashes[ids[6]],
        embedding_status="failed",
        retry_count=3,
    )
    # 7: pending younger than stale_pending_seconds -> SKIP
    env.rows[ids[7]] = OpportunityEmbedding(
        opportunity_id=ids[7],
        content_hash=hashes[ids[7]],
        embedding_status="pending",
        updated_at=now - timedelta(seconds=30),
    )
    # 8: pending abandoned older than stale_pending_seconds -> ENQUEUE
    env.rows[ids[8]] = OpportunityEmbedding(
        opportunity_id=ids[8],
        content_hash=hashes[ids[8]],
        embedding_status="pending",
        updated_at=now - timedelta(seconds=900),
    )

    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env.make_repo)
    pool = _FakeArqPool()
    adapter = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder(using_finetuned=True))
    ctx: dict[str, Any] = {
        "session_factory": env.session_factory(),
        "arq_pool": pool,
        "embedding_adapter": adapter,
        "max_tries": 3,
    }

    res = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=20, max_scanned=50, max_enqueued=50, stale_pending_seconds=600
    )
    assert res["scanned"] == 9
    assert res["enqueued"] == 6
    assert res["skipped"] == 3
    assert res["completed"] is True
    assert res["next_cursor"] == str(ids[-1])
    assert env.commits == 1
    assert env.page_queries == 1
    assert env.batch_queries == 1  # Single batch lookup (no N+1)

    enqueued_ids = {UUID(item[1]) for item in pool.enqueued}
    assert enqueued_ids == {ids[0], ids[2], ids[3], ids[4], ids[5], ids[8]}
    for _, opp_id_str, content_hash, job_id in pool.enqueued:
        assert job_id == f"embed:{opp_id_str}:{content_hash}"

    # Duplicate invocation: newly pending rows are younger than stale_pending_seconds -> 0 enqueued
    res_dup = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=20, max_scanned=50, max_enqueued=50, stale_pending_seconds=600
    )
    assert res_dup["enqueued"] == 0
    assert res_dup["skipped"] == 9
    assert res_dup["completed"] is True


@pytest.mark.asyncio
async def test_backfill_cursor_bounds_resume_and_enqueue_failure_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 5 records: [0]=missing, [1]=ready, [2]=missing, [3]=missing, [4]=missing
    ids = sorted([uuid4() for _ in range(5)])
    opps = [_make_opp(oid, f"Bounded {idx}") for idx, oid in enumerate(ids)]
    env = _InMemoryBackfillEnv(opps)
    h1 = build_opportunity_embedding_payload(opps[1])[1]
    env.rows[ids[1]] = OpportunityEmbedding(
        opportunity_id=ids[1],
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_FINETUNED_VERSION,
        content_hash=h1,
        embedding_status="ready",
    )

    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env.make_repo)
    pool = _FakeArqPool()
    adapter = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder(using_finetuned=True))
    ctx: dict[str, Any] = {
        "session_factory": env.session_factory(),
        "arq_pool": pool,
        "embedding_adapter": adapter,
        "max_tries": 3,
    }

    # max_enqueued=2 stops mid-page right after ids[2] without touching ids[3] or ids[4]
    run1 = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=5, max_scanned=5, max_enqueued=2
    )
    assert run1 == {
        "scanned": 3,
        "enqueued": 2,
        "skipped": 1,
        "next_cursor": str(ids[2]),
        "completed": False,
    }

    # Resume from next_cursor -> processes ids[3] and ids[4] and completes
    run2 = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=5, max_scanned=5, max_enqueued=2, after_id=run1["next_cursor"]
    )
    assert run2 == {
        "scanned": 2,
        "enqueued": 2,
        "skipped": 0,
        "next_cursor": str(ids[4]),
        "completed": True,
    }

    # max_scanned cap stops cleanly with completed=False
    ids_more = sorted([uuid4() for _ in range(4)])
    env2 = _InMemoryBackfillEnv([_make_opp(oid, "S") for oid in ids_more])
    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env2.make_repo)
    ctx["session_factory"] = env2.session_factory()
    # Fail Redis on first item to verify row remains pending without retry_count increment
    pool2 = _FakeArqPool(fail_on_ids={str(ids_more[0])})
    ctx["arq_pool"] = pool2

    run_capped = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=2, max_scanned=2, max_enqueued=10
    )
    assert run_capped == {
        "scanned": 2,
        "enqueued": 1,
        "skipped": 0,
        "next_cursor": str(ids_more[1]),
        "completed": False,
    }
    assert env2.rows[ids_more[0]].embedding_status == "pending"
    assert env2.rows[ids_more[0]].retry_count == 0


@pytest.mark.asyncio
async def test_backfill_new_hash_resets_exhausted_retries_and_model_change_preserves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opp_id = uuid4()
    opp = _make_opp(opp_id, "Updated Title H2")
    _, h2 = build_opportunity_embedding_payload(opp)
    h1 = "a" * 64
    assert h1 != h2

    env = _InMemoryBackfillEnv([opp])
    env.rows[opp_id] = OpportunityEmbedding(
        opportunity_id=opp_id,
        content_hash=h1,
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_PRETRAINED_VERSION,
        embedding_status="failed",
        retry_count=3,
        error_message="previous inference timeout on H1",
    )

    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env.make_repo)
    pool = _FakeArqPool()
    adapter = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder(using_finetuned=True))
    ctx: dict[str, Any] = {
        "session_factory": env.session_factory(),
        "arq_pool": pool,
        "embedding_adapter": adapter,
        "max_tries": 3,
    }

    # New hash H2 replaces exhausted failed H1 -> resets retry_count=0 and error_message=None
    res = await tasks_embeddings_module.backfill_missing_embeddings(ctx, batch_size=10)
    assert res["enqueued"] == 1
    assert env.rows[opp_id].embedding_status == "pending"
    assert env.rows[opp_id].content_hash == h2
    assert env.rows[opp_id].retry_count == 0
    assert env.rows[opp_id].error_message is None

    # Subsequent failure on H2 increments retry_count=1; re-registering H2 preserves retry_count=1
    env.rows[opp_id].embedding_status = "failed"
    env.rows[opp_id].retry_count = 1
    env.rows[opp_id].error_message = "transient H2 failure"
    repo = env.make_repo(None)
    same_hash_row = await repo.upsert_pending(
        opp_id,
        content_hash=h2,
        model_id=CANONICAL_MODEL_ID,
        model_version=CANONICAL_FINETUNED_VERSION,
    )
    assert same_hash_row.retry_count == 1
    assert same_hash_row.error_message == "transient H2 failure"

    # Model-version-only change preserves retry_count
    model_change_row = await repo.upsert_pending(
        opp_id,
        content_hash=h2,
        model_id=CANONICAL_MODEL_ID,
        model_version="2.0.0-new",
    )
    assert model_change_row.retry_count == 1


@pytest.mark.asyncio
async def test_concurrent_backfill_invocations_and_stale_worker_safety(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    id_missing, id_ready = sorted([uuid4(), uuid4()])
    opp_missing = _make_opp(id_missing, "Missing Opp")
    opp_ready = _make_opp(id_ready, "Ready Opp")
    _, h_missing = build_opportunity_embedding_payload(opp_missing)
    _, h_ready = build_opportunity_embedding_payload(opp_ready)

    env = _InMemoryBackfillEnv([opp_missing, opp_ready])
    env.rows[id_ready] = OpportunityEmbedding(
        opportunity_id=id_ready,
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_FINETUNED_VERSION,
        content_hash=h_ready,
        embedding_status="ready",
        retry_count=0,
    )

    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env.make_repo)
    pool = _FakeArqPool()
    adapter = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder(using_finetuned=True))
    ctx: dict[str, Any] = {
        "session_factory": env.session_factory(),
        "arq_pool": pool,
        "embedding_adapter": adapter,
        "max_tries": 3,
    }

    res1, res2 = await asyncio.gather(
        tasks_embeddings_module.backfill_missing_embeddings(ctx, batch_size=10),
        tasks_embeddings_module.backfill_missing_embeddings(ctx, batch_size=10),
    )
    assert res1["completed"] is True
    assert res2["completed"] is True
    # Both target only id_missing with the identical deterministic job_id; id_ready stays ready
    assert len(pool.enqueued) >= 1
    assert all(item[1] == str(id_missing) for item in pool.enqueued)
    assert all(item[3] == f"embed:{id_missing}:{h_missing}" for item in pool.enqueued)
    assert env.rows[id_ready].embedding_status == "ready"
    assert env.rows[id_ready].embedding_minilm_384 is not None

    # Stale worker with an older hash cannot overwrite newer pending hash or increment retry_count
    async def _fake_load_active(_session: Any, oid: UUID) -> Opportunity | None:
        return next((o for o in env.opps if o.id == oid and o.is_active), None)

    monkeypatch.setattr(tasks_embeddings_module, "_load_active_opportunity", _fake_load_active)
    stale_hash = "b" * 64
    assert stale_hash != h_missing
    worker_res = await tasks_embeddings_module.embed_opportunity(ctx, str(id_missing), stale_hash)
    assert worker_res["status"] == "stale_skipped"
    assert env.rows[id_missing].content_hash == h_missing
    assert env.rows[id_missing].retry_count == 0


@pytest.mark.asyncio
async def test_backfill_exact_size_final_page_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ids = sorted([uuid4() for _ in range(5)])
    opps = [_make_opp(oid, f"Exact {idx}") for idx, oid in enumerate(ids)]
    env = _InMemoryBackfillEnv(opps)

    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", env.make_repo)
    pool = _FakeArqPool()
    adapter = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder(using_finetuned=True))
    ctx: dict[str, Any] = {
        "session_factory": env.session_factory(),
        "arq_pool": pool,
        "embedding_adapter": adapter,
        "max_tries": 3,
    }

    res = await tasks_embeddings_module.backfill_missing_embeddings(
        ctx, batch_size=5, max_scanned=50, max_enqueued=50
    )
    assert res == {
        "scanned": 5,
        "enqueued": 5,
        "skipped": 0,
        "next_cursor": str(ids[-1]),
        "completed": True,
    }
    # Page 1 returns 5 rows (== batch_size); Page 2 returns [] confirming exhaustion
    assert env.page_queries == 2
    assert [UUID(item[1]) for item in pool.enqueued] == ids
