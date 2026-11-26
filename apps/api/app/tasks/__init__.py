"""Background tasks package (ARQ worker infrastructure)."""

from app.tasks.embeddings import (
    backfill_missing_embeddings,
    embed_opportunity,
    enqueue_embed_opportunity,
)
from app.tasks.worker import (
    WorkerSettings,
    configure_cpu_threads,
    ensure_worker_model_loaded,
    on_shutdown,
    on_startup,
    parse_redis_settings,
)

__all__ = [
    "WorkerSettings",
    "backfill_missing_embeddings",
    "configure_cpu_threads",
    "embed_opportunity",
    "enqueue_embed_opportunity",
    "ensure_worker_model_loaded",
    "on_shutdown",
    "on_startup",
    "parse_redis_settings",
]
