"""Worker-facing ML adapters (lazy-loaded; never imported into API request paths)."""

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
