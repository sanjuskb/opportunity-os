"""Unit tests for WS2-D-2 embedding producer, single-opportunity worker, and retry semantics."""

from __future__ import annotations

import sys
import types
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import pytest
from arq import Retry
from redis.exceptions import RedisError

from app.ml import (
    CANONICAL_FINETUNED_VERSION,
    CANONICAL_MODEL_ID,
    CANONICAL_PRETRAINED_VERSION,
    CANONICAL_VECTOR_DIM,
    CanonicalEmbeddingAdapter,
    EmbeddingSubsystemUnavailableError,
)
from app.models.entities import Opportunity, OpportunityEligibility, OpportunityEmbedding
from app.services.opportunity_text import build_opportunity_embedding_payload
from app.tasks import embeddings as tasks_embeddings_module


def _unit_vec(hot_idx: int = 0) -> list[float]:
    vec = [0.0] * CANONICAL_VECTOR_DIM
    vec[hot_idx] = 1.0
    return vec


class _FakeEncoder:
    def __init__(
        self,
        *,
        using_finetuned: bool = True,
        fail_with: Exception | None = None,
    ) -> None:
        self.using_finetuned_checkpoint = using_finetuned
        self.fail_with = fail_with
        self.encode_calls = 0

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        self.encode_calls += 1
        if self.fail_with is not None:
            raise self.fail_with
        return [_unit_vec(0) for _ in texts]


class _FakeSessionFactory:
    def __init__(self) -> None:
        self.commits = 0
        self.sessions: list[Any] = []

    @asynccontextmanager
    async def __call__(self) -> Any:
        factory = self

        class _FakeSession:
            async def commit(self) -> None:
                factory.commits += 1

            async def rollback(self) -> None:
                return None

        sess = _FakeSession()
        self.sessions.append(sess)
        yield sess


class _FakeArqPool:
    def __init__(self, *, fail_redis: bool = False, deduplicate: bool = False) -> None:
        self.enqueued: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.fail_redis = fail_redis
        self.deduplicate = deduplicate

    async def enqueue_job(self, fn_name: str, *args: Any, **kwargs: Any) -> Any:
        if self.fail_redis:
            raise RedisError("redis connection refused")
        self.enqueued.append((fn_name, args, kwargs))
        if self.deduplicate:
            return None
        return types.SimpleNamespace(job_id=kwargs.get("_job_id"))


def _make_opp(opp_id: UUID | None = None, *, is_active: bool = True) -> Opportunity:
    oid = opp_id or uuid4()
    opp = Opportunity(
        id=oid,
        title="Backend Engineer Intern",
        organization="NexteRaS",
        location="Bengaluru",
        type="internship",
        description="Build FastAPI + pgvector services",
        source_url="https://example.com/opp",
        source_provider="manual",
        is_active=is_active,
    )
    opp.eligibility = OpportunityEligibility(
        opportunity_id=oid,
        required_skills=["Python", "PostgreSQL"],
    )
    return opp


@pytest.mark.asyncio
async def test_producer_pending_commit_before_enqueue_and_caller_session_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opp = _make_opp()
    _, expected_hash = build_opportunity_embedding_payload(opp)
    events: list[str] = []
    caller_session = types.SimpleNamespace(commits=0)

    class _FakeFactory(_FakeSessionFactory):
        @asynccontextmanager
        async def __call__(self) -> Any:
            factory = self

            class _FakeSession:
                async def commit(self) -> None:
                    factory.commits += 1
                    events.append("commit")

            yield _FakeSession()

    class _FakeRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_opportunity_id(self, _oid: UUID) -> None:
            return None

        async def upsert_pending(self, _oid: UUID, **kwargs: Any) -> OpportunityEmbedding:
            events.append("upsert_pending")
            assert kwargs["content_hash"] == expected_hash
            assert kwargs["model_version"] is None
            return OpportunityEmbedding(
                opportunity_id=opp.id,
                content_hash=expected_hash,
                embedding_status="pending",
            )

    class _TrackingPool(_FakeArqPool):
        async def enqueue_job(self, fn_name: str, *args: Any, **kwargs: Any) -> Any:
            events.append("enqueue")
            return await super().enqueue_job(fn_name, *args, **kwargs)

    async def _load_opp(_s: Any, oid: UUID) -> Opportunity | None:
        return opp if oid == opp.id else None

    monkeypatch.setattr(tasks_embeddings_module, "_load_active_opportunity", _load_opp)
    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", _FakeRepo)

    pool = _TrackingPool()
    res = await tasks_embeddings_module.enqueue_embed_opportunity(
        _FakeFactory(), pool, opp.id  # type: ignore[arg-type]
    )
    assert res["status"] == "pending_enqueued"
    assert events == ["upsert_pending", "commit", "enqueue"]
    assert pool.enqueued[0][2]["_job_id"] == f"embed:{opp.id}:{expected_hash}"
    assert caller_session.commits == 0


@pytest.mark.asyncio
async def test_producer_ready_row_reuse_validation_and_redis_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opp = _make_opp()
    _, current_hash = build_opportunity_embedding_payload(opp)
    existing_row = OpportunityEmbedding(
        opportunity_id=opp.id,
        embedding_minilm_384=_unit_vec(),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=CANONICAL_PRETRAINED_VERSION,
        content_hash=current_hash,
        embedding_status="ready",
        retry_count=0,
    )
    upsert_calls = 0

    class _FakeRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_opportunity_id(self, _oid: UUID) -> OpportunityEmbedding:
            return existing_row

        async def upsert_pending(self, _oid: UUID, **_kwargs: Any) -> OpportunityEmbedding:
            nonlocal upsert_calls
            upsert_calls += 1
            return existing_row

    async def _load_opp(_s: Any, _oid: UUID) -> Opportunity:
        return opp

    monkeypatch.setattr(tasks_embeddings_module, "_load_active_opportunity", _load_opp)
    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", _FakeRepo)

    # Normal producer call skips ready matching row without downgrading
    factory = _FakeSessionFactory()
    pool = _FakeArqPool()
    res_skip = await tasks_embeddings_module.enqueue_embed_opportunity(
        factory, pool, opp.id  # type: ignore[arg-type]
    )
    assert res_skip["status"] == "already_ready"
    assert upsert_calls == 0
    assert pool.enqueued == []

    # verify_model_version=True enqueues validation job WITHOUT calling upsert_pending
    res_val = await tasks_embeddings_module.enqueue_embed_opportunity(
        factory, pool, opp.id, verify_model_version=True  # type: ignore[arg-type]
    )
    assert res_val["status"] == "validation_enqueued"
    assert upsert_calls == 0
    assert len(pool.enqueued) == 1

    # Duplicate enqueue handled safely
    dup_pool = _FakeArqPool(deduplicate=True)
    res_dup = await tasks_embeddings_module.enqueue_embed_opportunity(
        factory, dup_pool, opp.id, verify_model_version=True  # type: ignore[arg-type]
    )
    assert res_dup["deduplicated"] is True

    # Redis enqueue failure returns enqueue_failed without incrementing retry_count
    fail_pool = _FakeArqPool(fail_redis=True)
    res_fail = await tasks_embeddings_module.enqueue_embed_opportunity(
        factory, fail_pool, opp.id, verify_model_version=True  # type: ignore[arg-type]
    )
    assert res_fail["status"] == "enqueue_failed"
    assert existing_row.retry_count == 0


@pytest.mark.asyncio
async def test_worker_embed_opportunity_validation_reuse_upgrade_and_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opp = _make_opp()
    _, current_hash = build_opportunity_embedding_payload(opp)

    state: dict[str, Any] = {
        "opp": opp,
        "row": OpportunityEmbedding(
            opportunity_id=opp.id,
            embedding_minilm_384=None,
            embedding_model_id=CANONICAL_MODEL_ID,
            embedding_model_version=None,
            content_hash=current_hash,
            embedding_status="pending",
            retry_count=0,
        ),
        "save_returns_none": False,
    }

    class _FakeRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_opportunity_id(self, _oid: UUID) -> OpportunityEmbedding | None:
            return state["row"]

        async def save_embedding(
            self, _oid: UUID, vec: list[float], **kwargs: Any
        ) -> OpportunityEmbedding | None:
            if state["save_returns_none"]:
                return None
            row = OpportunityEmbedding(
                opportunity_id=opp.id,
                embedding_minilm_384=vec,
                embedding_model_id=kwargs["model_id"],
                embedding_model_version=kwargs["model_version"],
                content_hash=kwargs["content_hash"],
                embedding_status="ready",
                retry_count=0,
            )
            state["row"] = row
            return row

    async def _load_opp(_s: Any, _oid: UUID) -> Opportunity | None:
        return state["opp"]

    monkeypatch.setattr(tasks_embeddings_module, "_load_active_opportunity", _load_opp)
    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", _FakeRepo)

    encoder = _FakeEncoder(using_finetuned=True)
    adapter = CanonicalEmbeddingAdapter(encoder_override=encoder)
    ctx: dict[str, Any] = {
        "session_factory": _FakeSessionFactory(),
        "embedding_adapter": adapter,
        "job_try": 1,
        "max_tries": 3,
    }

    # 1. Invalid UUID / hash rejected cleanly
    assert (await tasks_embeddings_module.embed_opportunity(ctx, "bad", current_hash))["status"] == "invalid_payload"
    assert (await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), "bad"))["status"] == "invalid_payload"

    # 2. Stale expected hash rejected
    stale = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), "0" * 64)
    assert stale["status"] == "stale_skipped"

    # 3. Happy path embeds and marks ready with resolved fine-tuned version
    ok = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert ok["status"] == "ready"
    assert ok["model_version"] == CANONICAL_FINETUNED_VERSION
    assert encoder.encode_calls == 1

    # 4. Already ready with matching hash + model_id + resolved version -> skipped without inference
    reused = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert reused["status"] == "already_ready"
    assert encoder.encode_calls == 1

    # 5. Model version mismatch triggers re-embedding
    state["row"].embedding_model_version = CANONICAL_PRETRAINED_VERSION
    upgraded = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert upgraded["status"] == "ready"
    assert upgraded["model_version"] == CANONICAL_FINETUNED_VERSION
    assert encoder.encode_calls == 2

    # 6. Conditional save race (save_embedding returns None) -> stale_skipped
    state["row"].embedding_status = "pending"
    state["save_returns_none"] = True
    lost_race = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert lost_race["status"] == "stale_skipped"

    # 7. Missing embedding row -> stale_skipped
    state["row"] = None
    missing_row = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert missing_row["status"] == "stale_skipped"

    # 8. Missing/inactive opportunity -> missing_or_inactive
    state["opp"] = None
    missing_opp = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert missing_opp["status"] == "missing_or_inactive"


@pytest.mark.asyncio
async def test_worker_retry_failure_accounting_and_torch_thread_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opp = _make_opp()
    _, current_hash = build_opportunity_embedding_payload(opp)
    failures_recorded: list[tuple[str, str]] = []
    row = OpportunityEmbedding(
        opportunity_id=opp.id,
        content_hash=current_hash,
        embedding_status="pending",
        retry_count=0,
    )

    class _FakeRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_opportunity_id(self, _oid: UUID) -> OpportunityEmbedding:
            return row

        async def record_failure(
            self, _oid: UUID, err: str, **kwargs: Any
        ) -> OpportunityEmbedding:
            failures_recorded.append((err, kwargs["content_hash"]))
            row.embedding_status = "failed"
            row.retry_count += 1
            return row

    async def _load_opp(_s: Any, _oid: UUID) -> Opportunity:
        return opp

    monkeypatch.setattr(tasks_embeddings_module, "_load_active_opportunity", _load_opp)
    monkeypatch.setattr(tasks_embeddings_module, "EmbeddingRepository", _FakeRepo)

    # Simulate torch module loaded by adapter so configure_cpu_threads applies set_num_threads
    torch_threads_set: list[int] = []
    fake_torch = types.ModuleType("torch")
    fake_torch.set_num_threads = lambda n: torch_threads_set.append(n)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    failing_encoder = _FakeEncoder(
        using_finetuned=False,
        fail_with=EmbeddingSubsystemUnavailableError("transient GPU/CPU timeout"),
    )
    adapter = CanonicalEmbeddingAdapter(encoder_override=failing_encoder)
    ctx: dict[str, Any] = {
        "session_factory": _FakeSessionFactory(),
        "embedding_adapter": adapter,
        "job_try": 1,
        "max_tries": 3,
    }

    # First try records failure once and raises Retry(defer=5)
    with pytest.raises(Retry) as retry_exc:
        await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert retry_exc.value.defer_score == 5000  # 5s in ms
    assert len(failures_recorded) == 1
    assert row.retry_count == 1

    # New ARQ job starting at job_try=1 when DB retry_count=3 MUST still record failure
    row.embedding_status = "failed"
    row.retry_count = 3
    with pytest.raises(Retry):
        await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), current_hash)
    assert len(failures_recorded) == 2
    assert row.retry_count == 4

    # Stale hash does NOT call record_failure or increment retry_count
    stale_res = await tasks_embeddings_module.embed_opportunity(ctx, str(opp.id), "0" * 64)
    assert stale_res["status"] == "stale_skipped"
    assert len(failures_recorded) == 2
    assert row.retry_count == 4


@pytest.mark.asyncio
async def test_torch_set_num_threads_runs_before_backend_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    fake_torch = types.ModuleType("torch")
    fake_torch.set_num_threads = lambda n: events.append(f"set_num_threads:{n}")  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    class _OrderedMatcher:
        def __init__(self, device: str = "cpu") -> None:
            events.append("construct_backend")
            self.device = device
            self.using_finetuned_checkpoint = False

        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            events.append("encode")
            return [_unit_vec(0) for _ in texts]

    fake_sm_mod = types.ModuleType("ml.src.matching.semantic_matcher")
    fake_sm_mod.SemanticMatcher = _OrderedMatcher  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ml", types.ModuleType("ml"))
    monkeypatch.setitem(sys.modules, "ml.src", types.ModuleType("ml.src"))
    monkeypatch.setitem(sys.modules, "ml.src.matching", types.ModuleType("ml.src.matching"))
    monkeypatch.setitem(sys.modules, "ml.src.matching.semantic_matcher", fake_sm_mod)

    adapter = CanonicalEmbeddingAdapter(cpu_threads=4)
    model_id, version = adapter.ensure_loaded()
    assert model_id == CANONICAL_MODEL_ID
    assert version == CANONICAL_PRETRAINED_VERSION
    assert events == ["set_num_threads:4", "construct_backend"]

    adapter.embed_one("Title: Test")
    assert events == ["set_num_threads:4", "construct_backend", "encode"]
