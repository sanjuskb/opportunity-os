"""Dedicated ARQ background worker entrypoint and lifecycle management."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from app.core.config import settings
from app.db.session import DatabaseManager, check_db_health
from app.ml.embeddings import CanonicalEmbeddingAdapter

logger = logging.getLogger("opportunity_os.worker")

_HEARTBEAT_INTERVAL_SECONDS = 10.0
_HEARTBEAT_MAX_AGE_SECONDS = 60.0


def _heartbeat_path() -> Path:
    default_path = os.path.join(tempfile.gettempdir(), "opportunity_os_worker_heartbeat")
    return Path(os.getenv("WORKER_HEARTBEAT_FILE", default_path))


def _write_heartbeat() -> None:
    path = _heartbeat_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{time.time():.6f}", encoding="utf-8")


def check_worker_liveness(*, max_age_seconds: float = _HEARTBEAT_MAX_AGE_SECONDS) -> bool:
    """Return True only if the live worker process updated its heartbeat recently."""
    path = _heartbeat_path()
    try:
        raw = path.read_text(encoding="utf-8").strip()
        ts = float(raw)
    except (OSError, ValueError):
        return False
    return (time.time() - ts) <= max_age_seconds


async def _heartbeat_loop() -> None:
    while True:
        try:
            _write_heartbeat()
        except OSError:
            logger.warning("Failed to update worker heartbeat file.")
        await asyncio.sleep(_HEARTBEAT_INTERVAL_SECONDS)


def configure_cpu_threads(num_threads: int) -> None:
    """Configure bounded CPU thread env vars without forcing torch import."""
    bounded = max(1, num_threads)
    os.environ.setdefault("OMP_NUM_THREADS", str(bounded))
    os.environ.setdefault("MKL_NUM_THREADS", str(bounded))
    torch_mod = sys.modules.get("torch")
    if torch_mod is not None and hasattr(torch_mod, "set_num_threads"):
        torch_mod.set_num_threads(bounded)


def parse_redis_settings(redis_url: str) -> Any:
    """Parse REDIS_URL into arq.connections.RedisSettings."""
    try:
        from arq.connections import RedisSettings
    except ImportError as exc:
        raise RuntimeError(
            "ARQ package ('arq>=0.26.0') is required to build WorkerSettings.redis_settings."
        ) from exc

    raw = redis_url.strip()
    if not raw:
        raise ValueError("REDIS_URL must not be empty for ARQ worker.")
    parsed = urlparse(raw)
    if parsed.scheme not in ("redis", "rediss"):
        raise ValueError(f"Unsupported REDIS_URL scheme for ARQ: {parsed.scheme}")

    db_index = 0
    if parsed.path and parsed.path != "/":
        db_index = int(parsed.path.lstrip("/"))

    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=db_index,
        username=parsed.username,
        password=parsed.password,
        ssl=(parsed.scheme == "rediss"),
    )


def _optional_redis_settings(redis_url: str) -> Any:
    try:
        return parse_redis_settings(redis_url)
    except (RuntimeError, ValueError):
        return None


async def ensure_worker_model_loaded(ctx: dict[str, Any]) -> tuple[str, str]:
    """Run blocking adapter initialization outside the async event loop."""
    adapter: CanonicalEmbeddingAdapter = ctx["embedding_adapter"]
    return await asyncio.to_thread(adapter.ensure_loaded)


async def check_worker_dependencies(
    db: DatabaseManager,
    redis_conn: Any | None = None,
) -> dict[str, bool]:
    """Verify PostgreSQL and Redis readiness without loading the ML model."""
    db_ok = await check_db_health(db)
    redis_ok = False
    if redis_conn is not None and hasattr(redis_conn, "ping"):
        try:
            redis_ok = bool(await redis_conn.ping())
        except Exception:
            redis_ok = False
    else:
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(settings.REDIS_URL)
            try:
                redis_ok = bool(await client.ping())
            finally:
                await client.aclose()
        except Exception:
            redis_ok = False
    return {"database": db_ok, "redis": redis_ok}


async def _run_healthcheck() -> int:
    liveness_ok = check_worker_liveness()
    db = DatabaseManager(settings)
    try:
        deps = await check_worker_dependencies(db)
        healthy = liveness_ok and deps["database"] and deps["redis"]
        print(f"worker_liveness={liveness_ok} database={deps['database']} redis={deps['redis']}")
        return 0 if healthy else 1
    finally:
        await db.dispose()


async def on_startup(ctx: dict[str, Any]) -> None:
    """Initialize worker DB pool and single lazy CanonicalEmbeddingAdapter instance."""
    configure_cpu_threads(settings.TORCH_NUM_THREADS)
    db = DatabaseManager(settings)
    ctx["db"] = db
    ctx["session_factory"] = db.session_factory
    ctx["embedding_adapter"] = CanonicalEmbeddingAdapter(cpu_threads=settings.TORCH_NUM_THREADS)
    if hasattr(db, "engine"):
        deps = await check_worker_dependencies(db, ctx.get("redis"))
        if not deps["database"] or not deps["redis"]:
            logger.warning("Worker startup dependency check degraded: %s", deps)
    _write_heartbeat()
    ctx["heartbeat_task"] = asyncio.create_task(_heartbeat_loop())
    logger.info(
        "ARQ embedding worker initialized (max_jobs=%s, torch_threads=%s).",
        settings.ARQ_MAX_CONCURRENT_TASKS,
        settings.TORCH_NUM_THREADS,
    )


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Dispose worker DB pool and close Redis connection cleanly."""
    heartbeat_task: asyncio.Task[None] | None = ctx.get("heartbeat_task")
    if heartbeat_task is not None:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
    with contextlib.suppress(OSError):
        _heartbeat_path().unlink(missing_ok=True)

    db: DatabaseManager | None = ctx.get("db")
    if db is not None:
        await db.dispose()

    redis_conn = ctx.get("redis")
    if redis_conn is not None:
        if hasattr(redis_conn, "aclose"):
            await redis_conn.aclose()
        elif hasattr(redis_conn, "close"):
            maybe_coro = redis_conn.close()
            if asyncio.iscoroutine(maybe_coro):
                await maybe_coro
    logger.info("ARQ embedding worker shut down cleanly.")


def _default_worker_functions() -> list[Any]:
    from app.tasks.embeddings import backfill_missing_embeddings, embed_opportunity

    return [embed_opportunity, backfill_missing_embeddings]


class WorkerSettings:
    """ARQ WorkerSettings for dedicated background embedding worker."""

    functions: list[Any] = _default_worker_functions()
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = _optional_redis_settings(settings.REDIS_URL)
    max_jobs = settings.ARQ_MAX_CONCURRENT_TASKS
    job_timeout = settings.ARQ_TASK_TIMEOUT_SECONDS
    max_tries = settings.ARQ_MAX_TRIES


def main(argv: list[str] | None = None) -> None:
    """Entrypoint matching `python -m app.tasks.worker` in Dockerfile.worker."""
    parser = argparse.ArgumentParser(description="Opportunity OS ARQ embedding worker")
    parser.add_argument(
        "--healthcheck",
        action="store_true",
        help="Verify PostgreSQL and Redis readiness without loading the ML model.",
    )
    args, _ = parser.parse_known_args(argv)
    if args.healthcheck:
        raise SystemExit(asyncio.run(_run_healthcheck()))

    try:
        from arq.worker import run_worker
    except ImportError as exc:
        raise RuntimeError(
            "ARQ package ('arq>=0.26.0') is required to run the background worker."
        ) from exc

    WorkerSettings.redis_settings = parse_redis_settings(settings.REDIS_URL)
    run_worker(cast(Any, WorkerSettings))


if __name__ == "__main__":
    main()
