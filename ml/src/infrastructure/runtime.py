"""CPU-safe lazy model loader, single-heavy-model eviction cache, and error wrappers."""

from __future__ import annotations

import gc
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

from ml.src.common.config import configure_cpu_runtime

logger = logging.getLogger("nexteras.ml")

T = TypeVar("T")


class MLInferenceError(RuntimeError):
    """Structured error raised when model loading, validation, or inference fails."""

    def __init__(self, code: str, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.cause = cause


class ResourceManagedModelCache:
    """
    Lazy LRU model cache designed for 16 GB CPU-only laptops.
    Keeps at most `max_loaded_models` transformer models resident simultaneously
    (default = 1) and explicitly invokes garbage collection upon eviction.
    """

    def __init__(self, max_loaded_models: int = 1, cpu_threads: int = 6) -> None:
        self.max_loaded_models = max(1, max_loaded_models)
        self.cpu_threads = cpu_threads
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._model_locks: dict[str, threading.RLock] = {}
        self._load_times_ms: dict[str, float] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._runtime_initialized = False

    def ensure_cpu_runtime(self) -> dict[str, Any]:
        with self._lock:
            info = configure_cpu_runtime(self.cpu_threads)
            self._runtime_initialized = True
            return info

    def _get_model_lock(self, cache_key: str) -> threading.RLock:
        lock = self._model_locks.get(cache_key)
        if lock is None:
            lock = threading.RLock()
            self._model_locks[cache_key] = lock
        return lock

    def get_or_load(self, cache_key: str, loader: Callable[[], T]) -> T:
        with self._lock:
            if not self._runtime_initialized:
                self.ensure_cpu_runtime()

            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                self._cache_hits += 1
                self._get_model_lock(cache_key)
                return self._cache[cache_key]

            self._cache_misses += 1
            while len(self._cache) >= self.max_loaded_models:
                evicted_key, evicted_obj = self._cache.popitem(last=False)
                evicted_lock = self._model_locks.get(evicted_key)
                if evicted_lock is not None:
                    with evicted_lock:
                        logger.info("Evicting cached ML model '%s' to protect laptop RAM.", evicted_key)
                        del evicted_obj
                else:
                    logger.info("Evicting cached ML model '%s' to protect laptop RAM.", evicted_key)
                    del evicted_obj
                gc.collect()

            t0 = time.perf_counter()
            try:
                loaded = loader()
            except Exception as exc:
                raise MLInferenceError(
                    code="MODEL_LOAD_FAILED",
                    message=f"Failed to initialize ML model '{cache_key}': {exc}",
                    cause=exc,
                ) from exc
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            self._cache[cache_key] = loaded
            self._get_model_lock(cache_key)
            self._load_times_ms[cache_key] = elapsed_ms
            logger.info("Loaded ML model '%s' in %.1f ms on CPU.", cache_key, elapsed_ms)
            return loaded

    def execute_with_model(
        self,
        cache_key: str,
        loader: Callable[[], T],
        fn: Callable[[T], Any],
    ) -> Any:
        """
        Safely retrieve or load `cache_key` and serialize shared model access across threads
        so concurrent requests neither corrupt tokenizer/torch state nor evict mid-inference.
        """
        with self._lock:
            model = self.get_or_load(cache_key, loader)
            model_lock = self._get_model_lock(cache_key)
        with model_lock:
            # Re-verify cache membership in case an eviction raced between locks
            with self._lock:
                model = self.get_or_load(cache_key, loader)
            return fn(model)

    def unload(self, cache_key: str) -> bool:
        with self._lock:
            if cache_key not in self._cache:
                return False
            obj = self._cache.pop(cache_key)
            del obj
            gc.collect()
            return True

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            gc.collect()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "loaded_keys": list(self._cache.keys()),
                "max_loaded_models": self.max_loaded_models,
                "cpu_threads": min(self.cpu_threads, os.cpu_count() or self.cpu_threads),
                "load_times_ms": dict(self._load_times_ms),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
            }


GLOBAL_MODEL_CACHE = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
