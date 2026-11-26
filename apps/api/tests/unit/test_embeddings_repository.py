"""Unit tests for WS2-B OpportunityEmbedding ORM alignment and EmbeddingRepository."""

from __future__ import annotations

import math
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.models.entities import OpportunityEmbedding
from app.repositories.embeddings import (
    CANONICAL_MODEL_ID,
    CANONICAL_VECTOR_DIM,
    EmbeddingRepository,
    sanitize_embedding_error,
    validate_embedding_vector,
)
from app.repositories.opportunities import OpportunityRepository


class _FakeScalarSeq:
    def __init__(self, rows: list[Any] | None = None) -> None:
        self._rows = rows or []

    def all(self) -> list[Any]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[Any] | None = None, scalar: Any = None) -> None:
        self._rows = rows or []
        self._scalar = scalar

    def scalars(self) -> _FakeScalarSeq:
        return _FakeScalarSeq(self._rows)

    def scalar_one_or_none(self) -> Any:
        return self._scalar

    def all(self) -> list[Any]:
        return self._rows


class _SpyAsyncSession:
    def __init__(self, rows: list[Any] | None = None, scalar: Any = None) -> None:
        self.compiled_sql: list[str] = []
        self._rows = rows or []
        self._scalar = scalar

    async def execute(self, stmt: Any) -> _FakeResult:
        self.compiled_sql.append(
            str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": False}))
        )
        return _FakeResult(rows=self._rows, scalar=self._scalar)


def _unit_vec(dim: int = CANONICAL_VECTOR_DIM, hot_idx: int = 0) -> list[float]:
    vec = [0.0] * dim
    vec[hot_idx] = 1.0
    return vec


def test_orm_opportunity_embedding_matches_migration_columns_and_constraints() -> None:
    table = OpportunityEmbedding.__table__
    expected_cols = {
        "id",
        "opportunity_id",
        "embedding",
        "embedding_minilm_384",
        "embedding_model_id",
        "embedding_model_version",
        "content_hash",
        "embedding_status",
        "error_message",
        "retry_count",
        "created_at",
        "updated_at",
    }
    assert expected_cols.issubset(set(table.columns.keys()))
    assert table.c.embedding.type.dim == 768
    assert table.c.embedding_minilm_384.type.dim == 384
    assert table.c.embedding_status.nullable is False
    assert table.c.retry_count.nullable is False

    constraint_names = {c.name for c in table.constraints if c.name}
    assert "chk_opportunity_embeddings_status" in constraint_names
    assert "chk_opportunity_embeddings_retry_count_non_negative" in constraint_names
    assert "chk_opportunity_embeddings_ready_requires_vector" in constraint_names


def test_validate_embedding_vector_rejects_invalid_dimensions_and_values() -> None:
    assert len(validate_embedding_vector(_unit_vec(384))) == 384

    for bad_dim in (0, 383, 385, 768):
        with pytest.raises(ValueError, match="Expected 384-dimensional"):
            validate_embedding_vector([0.1] * bad_dim)

    nan_vec = _unit_vec(384)
    nan_vec[5] = math.nan
    with pytest.raises(ValueError, match="finite"):
        validate_embedding_vector(nan_vec)

    with pytest.raises(ValueError, match="sequence of floats"):
        validate_embedding_vector("not-a-vector")  # type: ignore[arg-type]


def test_sanitize_embedding_error_strips_stack_traces_and_secrets() -> None:
    raw = (
        "OperationalError: postgresql+asyncpg://postgres:super-secret@db.internal:5432/prod "
        "password=my_secret_pw Bearer eyJhbGciOiJIUzI1NiJ9\n"
        "Traceback (most recent call last):\n"
        "  File 'secret_path.py', line 99"
    )
    sanitized = sanitize_embedding_error(raw)
    assert "super-secret" not in sanitized
    assert "my_secret_pw" not in sanitized
    assert "eyJhbGciOiJIUzI1NiJ9" not in sanitized
    assert "Traceback" not in sanitized
    assert "\n" not in sanitized


@pytest.mark.asyncio
async def test_embedding_repository_upsert_save_and_failure_sql_contracts() -> None:
    opp_id = uuid4()
    fake_row = OpportunityEmbedding(
        opportunity_id=opp_id,
        embedding_minilm_384=_unit_vec(384),
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version="1.0.0",
        content_hash="hash_v1",
        embedding_status="ready",
        retry_count=0,
    )
    spy = _SpyAsyncSession(scalar=fake_row)
    repo = EmbeddingRepository(spy)  # type: ignore[arg-type]

    # Upsert pending with model_version=None must NOT include embedding_model_version in WHERE
    pending = await repo.upsert_pending(
        opp_id, content_hash="hash_v1", model_version=None
    )
    assert pending.opportunity_id == opp_id
    pending_sql = spy.compiled_sql[-1]
    assert "INSERT INTO public.opportunity_embeddings" in pending_sql
    assert "ON CONFLICT (opportunity_id) DO UPDATE" in pending_sql
    pending_where = pending_sql.split("WHERE ", 1)[1]
    assert "embedding_model_version IS DISTINCT FROM" not in pending_where

    # Upsert pending with explicit model_version DOES check embedding_model_version in WHERE
    await repo.upsert_pending(opp_id, content_hash="hash_v1", model_version="1.0.0")
    pending_ver_where = spy.compiled_sql[-1].split("WHERE ", 1)[1]
    assert "embedding_model_version IS DISTINCT FROM" in pending_ver_where

    # Save valid 384-dim embedding: WHERE guard must enforce content_hash match (no status bypass)
    saved = await repo.save_embedding(
        opp_id,
        _unit_vec(384),
        content_hash="hash_v1",
        model_version="1.0.0",
    )
    assert saved is not None
    save_sql = spy.compiled_sql[-1]
    assert "ON CONFLICT (opportunity_id) DO UPDATE" in save_sql
    where_clause = save_sql.split("WHERE ", 1)[1]
    assert "public.opportunity_embeddings.content_hash IS NULL" in where_clause
    assert "public.opportunity_embeddings.content_hash =" in where_clause
    assert "embedding_status !=" not in where_clause
    assert "embedding_minilm_384" in save_sql
    assert "embedding_status" in save_sql
    assert "error_message" in save_sql
    assert "retry_count" in save_sql

    # Invalid dimension rejected before SQL execution
    sql_count_before = len(spy.compiled_sql)
    with pytest.raises(ValueError, match="Expected 384-dimensional"):
        await repo.save_embedding(opp_id, [0.1] * 768, content_hash="hash_v1")
    assert len(spy.compiled_sql) == sql_count_before

    # Hashless failure rejected before SQL execution
    with pytest.raises(ValueError, match="content_hash"):
        await repo.record_failure(opp_id, "error", content_hash="")
    with pytest.raises(ValueError, match="content_hash"):
        await repo.record_failure(opp_id, "error", content_hash="   ")
    assert len(spy.compiled_sql) == sql_count_before

    # Record failure increments retry_count atomically and guards both status and content_hash
    await repo.record_failure(
        opp_id,
        "Timeout connecting to worker password=secret-pass",
        content_hash="hash_v1",
    )
    fail_sql = spy.compiled_sql[-1]
    assert "retry_count = (public.opportunity_embeddings.retry_count +" in fail_sql
    fail_where = fail_sql.split("WHERE ", 1)[1]
    assert "public.opportunity_embeddings.embedding_status !=" in fail_where
    assert "public.opportunity_embeddings.content_hash IS NULL" in fail_where
    assert "public.opportunity_embeddings.content_hash =" in fail_where


@pytest.mark.asyncio
async def test_missing_and_stale_embedding_lookups() -> None:
    opp_missing = uuid4()
    opp_pending = uuid4()
    opp_stale_hash = uuid4()
    opp_stale_model = uuid4()
    opp_ready = uuid4()

    rows = [
        OpportunityEmbedding(
            opportunity_id=opp_pending,
            embedding_minilm_384=None,
            embedding_model_id=CANONICAL_MODEL_ID,
            embedding_model_version="1.0.0",
            content_hash="h2",
            embedding_status="pending",
        ),
        OpportunityEmbedding(
            opportunity_id=opp_stale_hash,
            embedding_minilm_384=_unit_vec(384),
            embedding_model_id=CANONICAL_MODEL_ID,
            embedding_model_version="1.0.0",
            content_hash="old_hash",
            embedding_status="ready",
        ),
        OpportunityEmbedding(
            opportunity_id=opp_stale_model,
            embedding_minilm_384=_unit_vec(384),
            embedding_model_id=CANONICAL_MODEL_ID,
            embedding_model_version="0.9.0",
            content_hash="h4",
            embedding_status="ready",
        ),
        OpportunityEmbedding(
            opportunity_id=opp_ready,
            embedding_minilm_384=_unit_vec(384),
            embedding_model_id=CANONICAL_MODEL_ID,
            embedding_model_version="1.0.0",
            content_hash="h5",
            embedding_status="ready",
        ),
    ]
    spy = _SpyAsyncSession(rows=rows)
    repo = EmbeddingRepository(spy)  # type: ignore[arg-type]

    stale = await repo.list_stale_or_missing_opportunity_ids(
        {
            opp_missing: "h1",
            opp_pending: "h2",
            opp_stale_hash: "new_hash",
            opp_stale_model: "h4",
            opp_ready: "h5",
        },
        model_version="1.0.0",
    )
    assert set(stale) == {opp_missing, opp_pending, opp_stale_hash, opp_stale_model}
    assert opp_ready not in stale

    await repo.list_opportunities_without_embeddings(limit=25)
    assert "LEFT OUTER JOIN public.opportunity_embeddings" in spy.compiled_sql[-1]
    assert "opportunity_embeddings.id IS NULL" in spy.compiled_sql[-1]

    await repo.list_by_status(("pending", "failed"), limit=25)
    assert "opportunity_embeddings.embedding_status IN" in spy.compiled_sql[-1]

    after_uid = uuid4()
    await repo.list_active_opportunities_page(after_id=after_uid, limit=25)
    page_sql = spy.compiled_sql[-1]
    assert "opportunities.is_active IS true" in page_sql
    assert "opportunities.id >" in page_sql
    assert "ORDER BY public.opportunities.id ASC" in page_sql
    assert "OFFSET" not in page_sql

    await repo.get_by_opportunity_ids([opp_missing, opp_ready])
    batch_sql = spy.compiled_sql[-1]
    assert "opportunity_embeddings.opportunity_id IN" in batch_sql


@pytest.mark.asyncio
async def test_similarity_search_validates_dimension_and_excludes_non_ready() -> None:
    spy = _SpyAsyncSession(rows=[])
    emb_repo = EmbeddingRepository(spy)  # type: ignore[arg-type]
    opp_repo = OpportunityRepository(spy)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Expected 384-dimensional"):
        await emb_repo.search_similar_by_vector([0.1] * 768)

    with pytest.raises(ValueError, match="Expected 384-dimensional"):
        await opp_repo.search_similar_by_vector([0.1] * 768, model_column="embedding_minilm_384")

    await emb_repo.search_similar_by_vector(_unit_vec(384), model_version="1.0.0")
    sql = spy.compiled_sql[-1]
    assert "embedding_minilm_384 <=>" in sql
    assert "opportunity_embeddings.embedding_status =" in sql
    assert "opportunities.is_active IS true" in sql

    await opp_repo.search_similar_by_vector(_unit_vec(384), model_column="embedding_minilm_384")
    compat_sql = spy.compiled_sql[-1]
    assert "embedding_minilm_384 <=>" in compat_sql
    assert "opportunity_embeddings.embedding_status =" in compat_sql


@pytest.mark.asyncio
async def test_upsert_pending_isolates_retry_count_by_content_hash() -> None:
    opp_id = uuid4()
    fake_row = OpportunityEmbedding(
        opportunity_id=opp_id,
        content_hash="hash_v2",
        embedding_model_id=CANONICAL_MODEL_ID,
        embedding_model_version=None,
        embedding_status="pending",
        retry_count=0,
        error_message=None,
    )
    spy = _SpyAsyncSession(scalar=fake_row)
    repo = EmbeddingRepository(spy)  # type: ignore[arg-type]

    await repo.upsert_pending(opp_id, content_hash="hash_v2", model_version=None)
    sql = spy.compiled_sql[-1]
    assert "ON CONFLICT (opportunity_id) DO UPDATE" in sql
    assert (
        "retry_count = CASE WHEN (public.opportunity_embeddings.content_hash IS DISTINCT FROM"
        in sql
    )
    assert "ELSE public.opportunity_embeddings.retry_count END" in sql
    assert (
        "error_message = CASE WHEN (public.opportunity_embeddings.content_hash IS DISTINCT FROM"
        in sql
    )
    assert "ELSE public.opportunity_embeddings.error_message END" in sql
