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
    assert spec.fine_tuning_status == "pending_personal_training"

    matcher = SemanticMatcher(registry=reg)
    # Until Sanju trains ml/artifacts/minilm-nexteras-v1, active fallback is pretrained base
    if not (Path("ml/artifacts/minilm-nexteras-v1").exists()):
        assert matcher.model_identifier == "sentence-transformers/all-MiniLM-L6-v2"
        assert matcher.using_finetuned_checkpoint is False

    # Simulate Sanju placing a trained checkpoint cleanly
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
