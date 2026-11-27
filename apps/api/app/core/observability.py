"""Optional Sentry error tracking and PostHog product analytics helpers."""

from __future__ import annotations

import contextlib
import logging
from typing import Any
from uuid import UUID

from app.core.config import Settings

logger = logging.getLogger("opportunity_os.observability")

_posthog_client: Any | None = None


def configure_observability(cfg: Settings) -> None:
    """Initialize Sentry and PostHog only when DSN/API key are explicitly configured."""
    global _posthog_client

    if cfg.SENTRY_DSN.strip():
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.httpx import HttpxIntegration

            sentry_sdk.init(
                dsn=cfg.SENTRY_DSN.strip(),
                environment=cfg.ENVIRONMENT,
                traces_sample_rate=0.1 if cfg.is_production else 0.0,
                integrations=[FastApiIntegration(), HttpxIntegration()],
            )
            logger.info("Sentry observability enabled (env=%s).", cfg.ENVIRONMENT)
        except Exception as exc:
            logger.warning("Sentry initialization skipped (%s).", type(exc).__name__)

    if cfg.POSTHOG_API_KEY.strip():
        try:
            from posthog import Posthog

            _posthog_client = Posthog(
                project_api_key=cfg.POSTHOG_API_KEY.strip(),
                host=cfg.POSTHOG_HOST.strip() or "https://us.i.posthog.com",
            )
            logger.info("PostHog analytics enabled.")
        except Exception as exc:
            _posthog_client = None
            logger.warning("PostHog initialization skipped (%s).", type(exc).__name__)
    else:
        _posthog_client = None


def track_product_event(
    user_id: UUID | str,
    event_name: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """Emit anonymized product telemetry to PostHog when configured (safe no-op otherwise)."""
    if _posthog_client is None:
        return
    with contextlib.suppress(Exception):
        _posthog_client.capture(
            distinct_id=str(user_id),
            event=event_name,
            properties=properties or {},
        )


def shutdown_observability() -> None:
    """Flush PostHog queue cleanly during application shutdown."""
    global _posthog_client
    if _posthog_client is not None:
        with contextlib.suppress(Exception):
            _posthog_client.shutdown()
        _posthog_client = None
