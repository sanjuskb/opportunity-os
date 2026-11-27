"""Security headers middleware and Redis-backed sliding/fixed window rate limiting."""

from __future__ import annotations

import hashlib
import math
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from threading import Lock
from typing import Any

from fastapi import Request
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import ProblemDetailError

_NO_STORE_PREFIXES = (
    "/api/v1/users",
    "/api/v1/resumes",
    "/api/v1/applications",
    "/api/v1/career-passport",
    "/api/v1/voice",
    "/api/v1/agents",
)

_local_buckets: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
_local_lock = Lock()


def reset_local_rate_limits() -> None:
    """Reset in-memory fallback rate-limit buckets (used by unit tests)."""
    with _local_lock:
        _local_buckets.clear()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline OWASP security headers and strict cache controls on private routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), geolocation=()")
        response.headers.setdefault("X-XSS-Protection", "0")

        path = request.url.path
        if any(path.startswith(prefix) for prefix in _NO_STORE_PREFIXES):
            response.headers.setdefault("Cache-Control", "no-store")

        if not settings.DEBUG and settings.ENVIRONMENT.strip().lower() != "development":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


def _client_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            return f"tok:{digest}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


async def _increment_redis_bucket(
    redis_client: Any,
    key: str,
    window_seconds: int,
) -> tuple[int, int]:
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    count, ttl = await pipe.execute()
    count_int = int(count)
    ttl_int = int(ttl) if ttl is not None else -1
    if count_int == 1 or ttl_int < 0:
        await redis_client.expire(key, window_seconds)
        ttl_int = window_seconds
    return count_int, max(1, ttl_int)


def _increment_local_bucket(key: str, window_seconds: int) -> tuple[int, int]:
    now = time.monotonic()
    with _local_lock:
        count, expires_at = _local_buckets.get(key, (0, 0.0))
        if now >= expires_at:
            count = 1
            expires_at = now + window_seconds
        else:
            count += 1
        _local_buckets[key] = (count, expires_at)
        remaining = max(1, math.ceil(expires_at - now))
        return count, remaining


def rate_limit(
    scope: str,
    *,
    limit: int | None = None,
    window_seconds: int = 60,
) -> Callable[[Request], Awaitable[None]]:
    """FastAPI dependency enforcing Redis-backed rate limits with safe local fallback."""

    async def _enforce(request: Request) -> None:
        effective_limit = (
            limit
            if limit is not None
            else getattr(
                request.app.state, "rate_limit_rpm", settings.RATE_LIMIT_REQUESTS_PER_MINUTE
            )
        )
        if effective_limit <= 0:
            return

        bucket_key = f"rl:{scope}:{_client_key(request)}"
        redis_client: Any | None = getattr(request.app.state, "redis_client", None)
        count: int
        retry_after: int

        if redis_client is not None:
            try:
                count, retry_after = await _increment_redis_bucket(
                    redis_client, bucket_key, window_seconds
                )
            except (RedisError, OSError, TimeoutError):
                count, retry_after = _increment_local_bucket(bucket_key, window_seconds)
        else:
            count, retry_after = _increment_local_bucket(bucket_key, window_seconds)

        if count > effective_limit:
            raise ProblemDetailError(
                status_code=429,
                problem_type="urn:problem:rate_limit_exceeded",
                title="Too Many Requests",
                detail=f"Rate limit exceeded for {scope}. Retry in {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(effective_limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

    return _enforce
