"""
Thin FastAPI ML Compatibility Bridge.
Lazily resolves `ml.src.integration.NexteRaSMLService` when running in monorepo full-stack runtime,
while degrading gracefully when apps/api runs standalone without torch/ml installed.
"""

from __future__ import annotations

from typing import Any


class MLSubsystemUnavailableError(RuntimeError):
    """Raised when heavy ML dependencies are absent in a lightweight API-only container."""


def is_ml_subsystem_available() -> bool:
    try:
        import ml.src.integration.fastapi_adapter  # noqa: F401

        return True
    except ImportError:
        return False


def get_ml_service(**kwargs: Any) -> Any:
    """Dependency injection factory returning NexteRaSMLService cleanly when ml package is present."""
    try:
        from ml.src.integration.fastapi_adapter import NexteRaSMLService
    except ImportError as exc:
        raise MLSubsystemUnavailableError(
            "NexteRaS ML package (`ml.src`) is not installed in the API-only environment."
        ) from exc

    return NexteRaSMLService(**kwargs)
