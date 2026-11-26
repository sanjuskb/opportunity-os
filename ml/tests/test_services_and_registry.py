"""Tests for ModelRegistry, placeholder checkpoint resolution, and ResourceManagedModelCache."""

from __future__ import annotations

from pathlib import Path

import pytest

from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import MLInferenceError, ResourceManagedModelCache
from ml.src.matching.semantic_matcher import SemanticMatcher


def test_registry_and_personal_minilm_fallback(tmp_path: Path) -> None:
    reg = ModelRegistry("ml/model_configs/ml_registry.yaml")
    spec = reg.get("semantic_matcher")
    assert spec.embedding_dimension == 384
    assert spec.fine_tuning_status == "completed_synthetic_cpu"

    matcher = SemanticMatcher(registry=reg)
    if Path("ml/artifacts/minilm-nexteras-v1").exists() and any(Path("ml/artifacts/minilm-nexteras-v1").iterdir()):
        assert matcher.using_finetuned_checkpoint is True
        assert "minilm-nexteras-v1" in matcher.model_identifier
    else:
        assert matcher.model_identifier == "sentence-transformers/all-MiniLM-L6-v2"
        assert matcher.using_finetuned_checkpoint is False

    # Explicitly verify safe fallback when local checkpoint directory is missing
    missing_spec = spec.model_copy(update={"local_path": str(tmp_path / "does-not-exist")})
    fb_id, fb_tuned = missing_spec.resolve_active_identifier()
    assert fb_tuned is False
    assert fb_id == "sentence-transformers/all-MiniLM-L6-v2"

    # Simulate resolved local checkpoint cleanly
    fake_ckpt = tmp_path / "minilm-nexteras-v1"
    fake_ckpt.mkdir()
    (fake_ckpt / "config.json").write_text("{}", encoding="utf-8")
    tuned_spec = spec.model_copy(update={"local_path": str(fake_ckpt)})
    active_id, is_tuned = tuned_spec.resolve_active_identifier()
    assert is_tuned is True
    assert str(fake_ckpt) in active_id


def test_resource_managed_cache_eviction_and_error() -> None:
    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=4)
    cache.get_or_load("m1", lambda: {"name": "model_1"})
    assert cache.stats()["loaded_keys"] == ["m1"]

    cache.get_or_load("m2", lambda: {"name": "model_2"})
    # Evicts m1 to protect 16 GB laptop RAM
    assert cache.stats()["loaded_keys"] == ["m2"]

    assert cache.unload("m2") is True
    assert cache.stats()["loaded_keys"] == []

    def _boom():
        raise OSError("Missing weights")

    with pytest.raises(MLInferenceError) as exc_info:
        cache.get_or_load("bad", _boom)
    assert exc_info.value.code == "MODEL_LOAD_FAILED"


def test_cache_concurrency_reuse_and_semantic_matcher_input_guards(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    import numpy as np

    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=4)
    load_count = 0

    def _loader() -> dict[str, str]:
        nonlocal load_count
        load_count += 1
        return {"tag": "shared"}

    with ThreadPoolExecutor(max_workers=6) as pool:
        outs = list(
            pool.map(
                lambda i: cache.execute_with_model("shared_key", _loader, lambda m: f"{m['tag']}-{i}"),
                range(12),
            )
        )
    assert len(outs) == 12
    assert load_count == 1
    assert cache.stats()["cache_hits"] >= 11

    class _UnnormalizedEncoder:
        def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False):
            return np.full((len(texts), 384), 2.0, dtype=np.float32)

    matcher = SemanticMatcher(encoder_override=_UnnormalizedEncoder())
    empty_vecs = matcher.encode([])
    assert empty_vecs.shape == (0, 384)

    vecs = matcher.encode(["Backend Python FastAPI"])
    assert vecs.shape == (1, 384)
    assert np.isclose(np.linalg.norm(vecs[0]), 1.0, atol=1e-5)

    assert matcher.rank_opportunities("Backend Python", [], top_k=5) == []
    assert matcher.rank_opportunities("Backend Python", [{"doc_id": "d1", "doc_text": "Python"}], top_k=0) == []

    with pytest.raises(ValueError):
        matcher.rank_opportunities("   ", [{"doc_id": "d1", "doc_text": "Python"}])
    with pytest.raises(ValueError):
        matcher.rank_opportunities("Backend Python", [{"doc_id": "d1", "doc_text": ""}])
