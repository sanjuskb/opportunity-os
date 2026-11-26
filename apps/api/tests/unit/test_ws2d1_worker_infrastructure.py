"""Unit tests for WS2-D-1 embedding worker infrastructure and ensure_loaded()."""

from __future__ import annotations

import asyncio
import sys
import types
from collections.abc import Sequence
from typing import Any

import pytest

from app.core.config import Settings
from app.ml import (
    CANONICAL_FINETUNED_VERSION,
    CANONICAL_MODEL_ID,
    CANONICAL_PRETRAINED_VERSION,
    CANONICAL_VECTOR_DIM,
    CanonicalEmbeddingAdapter,
    EmbeddingSubsystemUnavailableError,
)
from app.tasks import worker as worker_module


def _fake_vec() -> list[float]:
    vec = [0.0] * CANONICAL_VECTOR_DIM
    vec[0] = 1.0
    return vec


def test_ensure_loaded_caches_model_and_avoids_duplicate_init(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_calls = 0

    class _FakeMatcher:
        def __init__(self, device: str = "cpu") -> None:
            nonlocal init_calls
            init_calls += 1
            self.device = device
            self.using_finetuned_checkpoint = True
            self.encode_called = False

        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            self.encode_called = True
            return [_fake_vec() for _ in texts]

    fake_sm_mod = types.ModuleType("ml.src.matching.semantic_matcher")
    fake_sm_mod.SemanticMatcher = _FakeMatcher  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ml", types.ModuleType("ml"))
    monkeypatch.setitem(sys.modules, "ml.src", types.ModuleType("ml.src"))
    monkeypatch.setitem(sys.modules, "ml.src.matching", types.ModuleType("ml.src.matching"))
    monkeypatch.setitem(sys.modules, "ml.src.matching.semantic_matcher", fake_sm_mod)

    adapter = CanonicalEmbeddingAdapter()
    assert adapter.resolved_model_version is None

    # First ensure_loaded initializes once without calling encode()
    model_id, version = adapter.ensure_loaded()
    assert model_id == CANONICAL_MODEL_ID
    assert version == CANONICAL_FINETUNED_VERSION
    assert init_calls == 1
    assert adapter._backend is not None
    assert adapter._backend.encode_called is False  # type: ignore[attr-defined]

    # Second ensure_loaded hits cache
    model_id_2, version_2 = adapter.ensure_loaded()
    assert (model_id_2, version_2) == (CANONICAL_MODEL_ID, CANONICAL_FINETUNED_VERSION)
    assert init_calls == 1


@pytest.mark.asyncio
async def test_ensure_loaded_concurrent_calls_initialize_only_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_calls = 0

    class _SlowMatcher:
        def __init__(self, device: str = "cpu") -> None:
            nonlocal init_calls
            init_calls += 1
            self.using_finetuned_checkpoint = False

        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            return [_fake_vec() for _ in texts]

    fake_sm_mod = types.ModuleType("ml.src.matching.semantic_matcher")
    fake_sm_mod.SemanticMatcher = _SlowMatcher  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ml", types.ModuleType("ml"))
    monkeypatch.setitem(sys.modules, "ml.src", types.ModuleType("ml.src"))
    monkeypatch.setitem(sys.modules, "ml.src.matching", types.ModuleType("ml.src.matching"))
    monkeypatch.setitem(sys.modules, "ml.src.matching.semantic_matcher", fake_sm_mod)

    adapter = CanonicalEmbeddingAdapter()
    results = await asyncio.gather(
        asyncio.to_thread(adapter.ensure_loaded),
        asyncio.to_thread(adapter.ensure_loaded),
        asyncio.to_thread(adapter.ensure_loaded),
    )
    assert all(r == (CANONICAL_MODEL_ID, CANONICAL_PRETRAINED_VERSION) for r in results)
    assert init_calls == 1


def test_ensure_loaded_unverifiable_and_init_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Unverifiable:
        def __init__(self, device: str = "cpu") -> None:
            pass

        def encode(self, texts: Sequence[str]) -> list[list[float]]:
            return [_fake_vec() for _ in texts]

    fake_sm_mod = types.ModuleType("ml.src.matching.semantic_matcher")
    fake_sm_mod.SemanticMatcher = _Unverifiable  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ml", types.ModuleType("ml"))
    monkeypatch.setitem(sys.modules, "ml.src", types.ModuleType("ml.src"))
    monkeypatch.setitem(sys.modules, "ml.src.matching", types.ModuleType("ml.src.matching"))
    monkeypatch.setitem(sys.modules, "ml.src.matching.semantic_matcher", fake_sm_mod)

    with pytest.raises(EmbeddingSubsystemUnavailableError, match="provenance"):
        CanonicalEmbeddingAdapter().ensure_loaded()

    class _Boom:
        def __init__(self, device: str = "cpu") -> None:
            raise OSError("corrupt weights")

    fake_sm_mod.SemanticMatcher = _Boom  # type: ignore[attr-defined]
    with pytest.raises(EmbeddingSubsystemUnavailableError, match="Failed to initialize"):
        CanonicalEmbeddingAdapter().ensure_loaded()


@pytest.mark.asyncio
async def test_worker_settings_lifecycle_hooks_and_entrypoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert worker_module.WorkerSettings.max_jobs == 1
    assert worker_module.WorkerSettings.job_timeout == 300
    assert worker_module.WorkerSettings.max_tries == 3
    assert len(worker_module.WorkerSettings.functions) == 7
    assert len(worker_module.WorkerSettings.cron_jobs) == 3

    # Lifecycle hooks initialize and dispose DB + Redis cleanly
    disposed = False
    redis_closed = False

    class _FakeDb:
        def __init__(self, _cfg: Settings) -> None:
            self.session_factory = "fake-session-factory"

        async def dispose(self) -> None:
            nonlocal disposed
            disposed = True

    class _FakeRedis:
        async def aclose(self) -> None:
            nonlocal redis_closed
            redis_closed = True

    monkeypatch.setattr(worker_module, "DatabaseManager", _FakeDb)
    ctx: dict[str, Any] = {"redis": _FakeRedis()}
    await worker_module.on_startup(ctx)
    assert ctx["session_factory"] == "fake-session-factory"
    assert isinstance(ctx["embedding_adapter"], CanonicalEmbeddingAdapter)
    assert ctx["embedding_adapter"].resolved_model_version is None

    await worker_module.on_shutdown(ctx)
    assert disposed is True
    assert redis_closed is True

    # parse_redis_settings + main() entrypoint using stubbed arq package
    captured_redis_kwargs: dict[str, Any] = {}
    ran_worker_cls: list[Any] = []

    class _FakeRedisSettings:
        def __init__(self, **kwargs: Any) -> None:
            captured_redis_kwargs.update(kwargs)

    fake_arq = types.ModuleType("arq")
    fake_arq_conn = types.ModuleType("arq.connections")
    fake_arq_conn.RedisSettings = _FakeRedisSettings  # type: ignore[attr-defined]
    fake_arq_worker = types.ModuleType("arq.worker")
    fake_arq_worker.run_worker = lambda cls: ran_worker_cls.append(cls)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "arq", fake_arq)
    monkeypatch.setitem(sys.modules, "arq.connections", fake_arq_conn)
    monkeypatch.setitem(sys.modules, "arq.worker", fake_arq_worker)

    worker_module.parse_redis_settings("rediss://user:pass@redis.example.com:6380/2")
    assert captured_redis_kwargs == {
        "host": "redis.example.com",
        "port": 6380,
        "database": 2,
        "username": "user",
        "password": "pass",
        "ssl": True,
    }

    worker_module.main()
    assert ran_worker_cls == [worker_module.WorkerSettings]


@pytest.mark.asyncio
async def test_worker_dependency_healthcheck_does_not_load_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeDb:
        pass

    class _FakeRedisPing:
        async def ping(self) -> bool:
            return True

    async def _ok_db(_db: Any) -> bool:
        return True

    monkeypatch.setattr(worker_module, "check_db_health", _ok_db)
    deps = await worker_module.check_worker_dependencies(_FakeDb(), _FakeRedisPing())  # type: ignore[arg-type]
    assert deps == {"database": True, "redis": True}

    async def _fail_db(_db: Any) -> bool:
        return False

    monkeypatch.setattr(worker_module, "check_db_health", _fail_db)
    deps_down = await worker_module.check_worker_dependencies(_FakeDb(), _FakeRedisPing())  # type: ignore[arg-type]
    assert deps_down == {"database": False, "redis": True}

    # Liveness requires a recent heartbeat written by the running worker process
    assert worker_module.check_worker_liveness() is False
    worker_module._write_heartbeat()
    try:
        assert worker_module.check_worker_liveness() is True
    finally:
        worker_module._heartbeat_path().unlink(missing_ok=True)
