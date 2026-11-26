"""Unit tests for WS2-C ML Embedding Adapter, Canonical Text Builder, SHA-256 Hashing & WS2-B compatibility."""

from __future__ import annotations

import math
import struct
import sys
import types
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.ml import (
    CANONICAL_FINETUNED_VERSION,
    CANONICAL_MODEL_ID,
    CANONICAL_PRETRAINED_VERSION,
    CANONICAL_VECTOR_DIM,
    CanonicalEmbeddingAdapter,
    EmbeddingSubsystemUnavailableError,
)
from app.models.entities import Opportunity, OpportunityEligibility, OpportunityEmbedding
from app.repositories.embeddings import EmbeddingRepository
from app.services import (
    CanonicalOpportunityInput,
    build_canonical_opportunity_text,
    build_canonical_opportunity_text_from_fields,
    build_opportunity_embedding_payload,
    compute_content_hash,
)


class _FakeEncoder:
    def __init__(
        self,
        outputs: Sequence[Sequence[float]] | None = None,
        *,
        using_finetuned_checkpoint: bool = False,
    ) -> None:
        self._outputs = outputs
        self.using_finetuned_checkpoint = using_finetuned_checkpoint
        self.calls: list[list[str]] = []

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self._outputs is not None:
            return [list(row) for row in self._outputs]
        rows: list[list[float]] = []
        for idx, _ in enumerate(texts):
            vec = [0.0] * CANONICAL_VECTOR_DIM
            vec[idx % CANONICAL_VECTOR_DIM] = 3.0
            vec[(idx + 1) % CANONICAL_VECTOR_DIM] = 4.0
            rows.append(vec)
        return rows


def test_adapter_valid_single_and_batch_float32_l2_normalized() -> None:
    fake = _FakeEncoder()
    adapter = CanonicalEmbeddingAdapter(
        model_id=CANONICAL_MODEL_ID,
        model_version="1.0.0-test",
        encoder_override=fake,
    )

    vec, model_id, model_version = adapter.embed_one("Title: Backend Intern")
    assert len(vec) == 384
    assert model_id == CANONICAL_MODEL_ID
    assert model_version == "1.0.0-test"

    # L2 normalized (~1.0) and IEEE 754 float32 precision
    norm = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-5, abs_tol=1e-5)
    for x in vec[:4]:
        roundtrip = struct.unpack("f", struct.pack("f", x))[0]
        assert math.isclose(x, roundtrip, rel_tol=0.0, abs_tol=1e-12)

    batch = adapter.embed_texts(["Doc 1", "Doc 2"])
    assert batch.dimension == 384
    assert len(batch.vectors) == 2
    assert batch.model_id == CANONICAL_MODEL_ID
    assert batch.model_version == "1.0.0-test"


def test_adapter_rejects_invalid_inputs_and_outputs() -> None:
    adapter = CanonicalEmbeddingAdapter(max_batch_size=2, encoder_override=_FakeEncoder())

    with pytest.raises(ValueError, match="must not be empty"):
        adapter.embed_texts([])
    with pytest.raises(ValueError, match="non-empty"):
        adapter.embed_texts(["   "])
    with pytest.raises(ValueError, match="max_batch_size"):
        adapter.embed_texts(["a", "b", "c"])

    # Wrong dimension (768 and 383)
    bad_dim_768 = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder([[0.1] * 768]))
    with pytest.raises(ValueError, match="Expected 384-dimensional"):
        bad_dim_768.embed_one("hello")

    bad_dim_383 = CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder([[0.1] * 383]))
    with pytest.raises(ValueError, match="Expected 384-dimensional"):
        bad_dim_383.embed_one("hello")

    # NaN / Infinity
    nan_vec = [0.0] * 384
    nan_vec[0] = math.nan
    with pytest.raises(ValueError, match="finite"):
        CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder([nan_vec])).embed_one("hello")

    inf_vec = [0.0] * 384
    inf_vec[0] = math.inf
    with pytest.raises(ValueError, match="finite"):
        CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder([inf_vec])).embed_one("hello")

    # Zero-norm vector
    zero_vec = [0.0] * 384
    with pytest.raises(ValueError, match="zero norm"):
        CanonicalEmbeddingAdapter(encoder_override=_FakeEncoder([zero_vec])).embed_one("hello")


def test_adapter_missing_backend_fails_safely_and_no_model_loaded_on_api_import() -> None:
    import app.main  # noqa: F401

    assert "sentence_transformers" not in sys.modules
    assert "torch" not in sys.modules

    adapter = CanonicalEmbeddingAdapter()
    with pytest.raises(EmbeddingSubsystemUnavailableError, match="No ML embedding backend"):
        adapter.embed_one("Title: Test")


def test_adapter_model_version_provenance_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. SemanticMatcher with fine-tuned checkpoint -> 1.0.0-nexteras-v1
    class _FakeMatcherFinetuned(_FakeEncoder):
        def __init__(self, device: str = "cpu") -> None:
            super().__init__(using_finetuned_checkpoint=True)
            self.device = device

    fake_sm_mod = types.ModuleType("ml.src.matching.semantic_matcher")
    fake_sm_mod.SemanticMatcher = _FakeMatcherFinetuned  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ml", types.ModuleType("ml"))
    monkeypatch.setitem(sys.modules, "ml.src", types.ModuleType("ml.src"))
    monkeypatch.setitem(sys.modules, "ml.src.matching", types.ModuleType("ml.src.matching"))
    monkeypatch.setitem(sys.modules, "ml.src.matching.semantic_matcher", fake_sm_mod)

    adapter_ft = CanonicalEmbeddingAdapter()
    assert adapter_ft.resolved_model_version is None  # Lazy until first embed
    _, _, ver_ft = adapter_ft.embed_one("Title: Fine-tuned")
    assert ver_ft == CANONICAL_FINETUNED_VERSION
    assert adapter_ft.resolved_model_version == CANONICAL_FINETUNED_VERSION

    # 2. SemanticMatcher falling back to pretrained -> 1.0.0-pretrained
    class _FakeMatcherPretrained(_FakeEncoder):
        def __init__(self, device: str = "cpu") -> None:
            super().__init__(using_finetuned_checkpoint=False)
            self.device = device

    fake_sm_mod.SemanticMatcher = _FakeMatcherPretrained  # type: ignore[attr-defined]
    _, _, ver_pt = CanonicalEmbeddingAdapter().embed_one("Title: Pretrained fallback")
    assert ver_pt == CANONICAL_PRETRAINED_VERSION

    # 3. Unverifiable SemanticMatcher provenance -> fails safely
    class _UnverifiableMatcher:
        def __init__(self, device: str = "cpu") -> None:
            self.device = device

        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            return _FakeEncoder().encode(texts)

    fake_sm_mod.SemanticMatcher = _UnverifiableMatcher  # type: ignore[attr-defined]
    with pytest.raises(EmbeddingSubsystemUnavailableError, match="provenance"):
        CanonicalEmbeddingAdapter().embed_one("Title: Unverifiable")

    # 4. Direct SentenceTransformer fallback -> strictly 1.0.0-pretrained
    for mod_name in ("ml.src.matching.semantic_matcher", "ml.src.matching", "ml.src", "ml"):
        monkeypatch.delitem(sys.modules, mod_name, raising=False)

    class _FakeSentenceTransformer:
        def __init__(self, model_id: str, device: str = "cpu") -> None:
            self.model_id = model_id
            self.device = device

        def encode(self, texts: Sequence[str], **_kwargs: Any) -> list[list[float]]:
            return _FakeEncoder().encode(texts)

    fake_st_mod = types.ModuleType("sentence_transformers")
    fake_st_mod.SentenceTransformer = _FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st_mod)

    _, _, ver_direct = CanonicalEmbeddingAdapter().embed_one("Title: Direct ST")
    assert ver_direct == CANONICAL_PRETRAINED_VERSION
    assert ver_direct != CANONICAL_FINETUNED_VERSION

    # 5. Unverifiable injected encoder -> fails safely
    with pytest.raises(EmbeddingSubsystemUnavailableError, match="provenance"):
        CanonicalEmbeddingAdapter(encoder_override=_UnverifiableMatcher()).embed_one("Title: X")


def test_canonical_text_builder_determinism_normalization_and_metadata_exclusion() -> None:
    base_fields = CanonicalOpportunityInput(
        title="  Backend\n\tEngineer   Intern  ",
        organization="NexteRaS   Labs",
        opp_type="internship",
        location="Bengaluru",
        description="Build   FastAPI   services\nin  Caf\u0065\u0301",  # NFD e + combining acute
        stipend_or_salary="25000 INR/month",
        required_skills=["PyTorch", "FastAPI", "fastapi", "PostgreSQL"],
        eligible_degrees=["B.Tech", "M.Tech"],
        eligible_branches=["CSE", "ECE"],
        eligible_batches=[2027, 2026, 2027],
        min_cgpa=Decimal("7.50"),
    )
    text_1 = build_canonical_opportunity_text_from_fields(base_fields)
    # Same content with reordered lists and NFC Café
    reordered = CanonicalOpportunityInput(
        title="Backend Engineer Intern",
        organization="NexteRaS Labs",
        opp_type="internship",
        location="Bengaluru",
        description="Build FastAPI services in Caf\u00e9",
        stipend_or_salary="25000 INR/month",
        required_skills=["PostgreSQL", "FastAPI", "PyTorch"],
        eligible_degrees=["M.Tech", "B.Tech"],
        eligible_branches=["ECE", "CSE"],
        eligible_batches=[2026, 2027],
        min_cgpa=Decimal("7.5"),
    )
    text_2 = build_canonical_opportunity_text_from_fields(reordered)
    assert text_1 == text_2

    expected_prefixes = [
        "Title: Backend Engineer Intern",
        "Organization: NexteRaS Labs",
        "Type: internship",
        "Location: Bengaluru",
        "Compensation: 25000 INR/month",
        "Required Skills: FastAPI, PostgreSQL, PyTorch",
        "Eligible Degrees: B.Tech, M.Tech",
        "Eligible Branches: CSE, ECE",
        "Eligible Batches: 2026, 2027",
        "Minimum CGPA: 7.5",
        "Description: Build FastAPI services in Caf\u00e9",
    ]
    assert text_1.splitlines() == expected_prefixes

    # Null/empty optional fields omitted cleanly
    minimal = build_canonical_opportunity_text_from_fields(
        CanonicalOpportunityInput(
            title="Intern",
            organization="Org",
            opp_type="internship",
            location="Remote",
            description="Desc",
            stipend_or_salary="   ",
            required_skills=[],
            eligible_degrees=None,
            eligible_branches=None,
            eligible_batches=[],
            min_cgpa=None,
        )
    )
    assert minimal.splitlines() == [
        "Title: Intern",
        "Organization: Org",
        "Type: internship",
        "Location: Remote",
        "Description: Desc",
    ]


def test_canonical_text_and_sha256_hash_ignore_operational_metadata() -> None:
    now = datetime.now(UTC)
    opp_1 = Opportunity(
        id=uuid4(),
        title="AI Intern",
        organization="Lab",
        location="Remote",
        type="internship",
        description="Work on embeddings",
        source_url="https://example.com/1",
        source_provider="olostep",
        retrieval_timestamp=now,
        is_active=True,
        raw_data={"views": 10},
        created_at=now,
    )
    opp_1.eligibility = OpportunityEligibility(
        opportunity_id=opp_1.id,
        required_skills=["Python", "SQL"],
        eligible_batches=[2026],
        eligible_degrees=["B.Tech"],
        eligible_branches=["CSE"],
        min_cgpa=Decimal("8.00"),
    )

    opp_2 = Opportunity(
        id=uuid4(),
        title="AI Intern",
        organization="Lab",
        location="Remote",
        type="internship",
        description="Work on embeddings",
        source_url="https://example.com/different-url",
        source_provider="crustdata",
        retrieval_timestamp=now + timedelta(days=2),
        is_active=False,
        raw_data={"views": 999},
        created_at=now + timedelta(days=2),
    )
    opp_2.eligibility = OpportunityEligibility(
        opportunity_id=opp_2.id,
        required_skills=["SQL", "Python"],
        eligible_batches=[2026],
        eligible_degrees=["B.Tech"],
        eligible_branches=["CSE"],
        min_cgpa=Decimal("8.0"),
    )

    text_1, hash_1 = build_opportunity_embedding_payload(opp_1)
    text_2, hash_2 = build_opportunity_embedding_payload(opp_2)
    assert text_1 == text_2
    assert hash_1 == hash_2
    assert len(hash_1) == 64

    # Meaningful field change updates both canonical text and hash
    opp_2.title = "Senior AI Intern"
    text_3 = build_canonical_opportunity_text(opp_2)
    hash_3 = compute_content_hash(text_3)
    assert text_3 != text_1
    assert hash_3 != hash_1


@pytest.mark.asyncio
async def test_ws2b_repository_compatibility_with_ws2c_adapter_and_hashing() -> None:
    opp = Opportunity(
        id=uuid4(),
        title="Data Intern",
        organization="NexteRaS",
        location="Hyderabad",
        type="internship",
        description="PostgreSQL and pgvector",
        source_url="https://example.com/opp",
        source_provider="manual",
    )
    canonical_text, content_hash = build_opportunity_embedding_payload(opp)
    adapter = CanonicalEmbeddingAdapter(
        encoder_override=_FakeEncoder(using_finetuned_checkpoint=True)
    )
    vec, model_id, model_version = adapter.embed_one(canonical_text)
    assert model_version == CANONICAL_FINETUNED_VERSION

    compiled_sql: list[str] = []

    class _FakeResult:
        def __init__(self, row: OpportunityEmbedding) -> None:
            self._row = row

        def scalar_one_or_none(self) -> OpportunityEmbedding:
            return self._row

    fake_row = OpportunityEmbedding(
        opportunity_id=opp.id,
        embedding_minilm_384=vec,
        embedding_model_id=model_id,
        embedding_model_version=model_version,
        content_hash=content_hash,
        embedding_status="ready",
        retry_count=0,
    )

    class _SpySession:
        async def execute(self, stmt: Any) -> _FakeResult:
            compiled_sql.append(str(stmt.compile(dialect=postgresql.dialect())))
            return _FakeResult(fake_row)

    repo = EmbeddingRepository(_SpySession())  # type: ignore[arg-type]
    pending = await repo.upsert_pending(
        opp.id,
        content_hash=content_hash,
        model_id=model_id,
        model_version=model_version,
    )
    assert pending.opportunity_id == opp.id

    saved = await repo.save_embedding(
        opp.id,
        vec,
        content_hash=content_hash,
        model_id=model_id,
        model_version=model_version,
    )
    assert saved is not None
    assert saved.embedding_status == "ready"
    save_where = compiled_sql[-1].split("WHERE ", 1)[1]
    assert "public.opportunity_embeddings.content_hash IS NULL" in save_where
    assert "public.opportunity_embeddings.content_hash =" in save_where

    await repo.record_failure(
        opp.id,
        "transient failure",
        content_hash=content_hash,
        model_id=model_id,
        model_version=model_version,
    )
    assert "INSERT INTO public.opportunity_embeddings" in compiled_sql[-1]
