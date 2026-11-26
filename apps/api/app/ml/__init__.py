"""Worker-facing ML adapters (lazy-loaded; never eagerly imported into API request paths)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.ml.embeddings import (
        CANONICAL_FINETUNED_VERSION,
        CANONICAL_PRETRAINED_VERSION,
        CanonicalEmbeddingAdapter,
        CanonicalEmbeddingOutput,
        EmbeddingSubsystemUnavailableError,
        TextEncoderBackend,
    )
    from app.repositories.embeddings import CANONICAL_MODEL_ID, CANONICAL_VECTOR_DIM

__all__ = [
    "CANONICAL_FINETUNED_VERSION",
    "CANONICAL_MODEL_ID",
    "CANONICAL_PRETRAINED_VERSION",
    "CANONICAL_VECTOR_DIM",
    "CanonicalEmbeddingAdapter",
    "CanonicalEmbeddingOutput",
    "EmbeddingSubsystemUnavailableError",
    "TextEncoderBackend",
]

_EMBEDDING_EXPORTS = {
    "CANONICAL_FINETUNED_VERSION",
    "CANONICAL_PRETRAINED_VERSION",
    "CanonicalEmbeddingAdapter",
    "CanonicalEmbeddingOutput",
    "EmbeddingSubsystemUnavailableError",
    "TextEncoderBackend",
}
_REPO_EXPORTS = {"CANONICAL_MODEL_ID", "CANONICAL_VECTOR_DIM"}


def __getattr__(name: str) -> Any:
    if name in _EMBEDDING_EXPORTS:
        from app.ml import embeddings as emb_module

        return getattr(emb_module, name)
    if name in _REPO_EXPORTS:
        from app.repositories import embeddings as repo_module

        return getattr(repo_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
