"""Worker-facing ML embedding adapter for canonical 384-dim all-MiniLM-L6-v2 vectors."""

from __future__ import annotations

import math
import os
import threading
from array import array
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from app.repositories.embeddings import CANONICAL_MODEL_ID, CANONICAL_VECTOR_DIM

CANONICAL_FINETUNED_VERSION = "1.0.0-nexteras-v1"
CANONICAL_PRETRAINED_VERSION = "1.0.0-pretrained"
DEFAULT_MAX_BATCH_SIZE = 64
_ZERO_NORM_EPSILON = 1e-12


class EmbeddingSubsystemUnavailableError(RuntimeError):
    """Raised when no ML embedding backend is available or provenance cannot be verified."""


class TextEncoderBackend(Protocol):
    """Minimal inference protocol compatible with origin/ml SemanticMatcher."""

    def encode(self, texts: Sequence[str]) -> Any: ...


@dataclass(frozen=True)
class CanonicalEmbeddingOutput:
    """Validated 384-dim float32 L2-normalized embedding batch with verified model metadata."""

    vectors: list[list[float]]
    model_id: str
    model_version: str
    dimension: int = CANONICAL_VECTOR_DIM


def _to_float32_normalized(raw_vector: Any, *, row_index: int) -> list[float]:
    """Validate dimension, finiteness, and non-zero norm; return float32 L2-normalized list."""
    seq = raw_vector.tolist() if hasattr(raw_vector, "tolist") else raw_vector

    if isinstance(seq, (str, bytes)) or not isinstance(seq, Sequence):
        raise ValueError(f"Embedding output at index {row_index} must be a numeric sequence.")
    if len(seq) != CANONICAL_VECTOR_DIM:
        raise ValueError(
            f"Expected {CANONICAL_VECTOR_DIM}-dimensional embedding at index {row_index}, "
            f"got {len(seq)}."
        )

    values: list[float] = []
    sq_sum = 0.0
    for col_idx, item in enumerate(seq):
        if isinstance(item, bool):
            raise ValueError(
                f"Embedding element at ({row_index}, {col_idx}) must be float, not bool."
            )
        val = float(item)
        if not math.isfinite(val):
            raise ValueError(f"Embedding element at ({row_index}, {col_idx}) must be finite.")
        values.append(val)
        sq_sum += val * val

    norm = math.sqrt(sq_sum)
    if norm <= _ZERO_NORM_EPSILON:
        raise ValueError(f"Embedding vector at index {row_index} has zero norm.")

    # Normalize and cast to IEEE 754 float32 precision without requiring numpy.
    f32 = array("f", (val / norm for val in values))
    return [float(x) for x in f32]


class CanonicalEmbeddingAdapter:
    """Lazy, worker-only adapter producing validated 384-dim all-MiniLM-L6-v2 embeddings.

    Prefers `ml.src.matching.semantic_matcher.SemanticMatcher` (registry-resolved
    checkpoint vs pretrained fallback) and falls back to `sentence_transformers.SentenceTransformer`
    explicitly labeled as `1.0.0-pretrained`. Never loads models at import time.
    """

    def __init__(
        self,
        *,
        model_id: str = CANONICAL_MODEL_ID,
        model_version: str | None = None,
        device: str = "cpu",
        max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
        cpu_threads: int | None = None,
        encoder_override: TextEncoderBackend | None = None,
    ) -> None:
        if max_batch_size < 1:
            raise ValueError("max_batch_size must be at least 1.")
        if cpu_threads is not None and cpu_threads < 1:
            raise ValueError("cpu_threads must be at least 1.")
        self.model_id = model_id
        self._explicit_model_version = model_version
        self.device = device
        self.max_batch_size = max_batch_size
        self.cpu_threads = cpu_threads
        self._encoder_override = encoder_override
        self._backend: TextEncoderBackend | None = encoder_override
        self._resolved_version: str | None = None
        self._init_lock = threading.Lock()

    def _configure_torch_threads(self) -> None:
        """Set OMP/MKL env vars and apply torch.set_num_threads() before backend construction."""
        if self.cpu_threads is None:
            return
        os.environ.setdefault("OMP_NUM_THREADS", str(self.cpu_threads))
        os.environ.setdefault("MKL_NUM_THREADS", str(self.cpu_threads))
        try:
            import torch
        except ImportError:
            return
        if hasattr(torch, "set_num_threads"):
            torch.set_num_threads(self.cpu_threads)

    @property
    def resolved_model_version(self) -> str | None:
        """Return the verified model version once the backend has been resolved."""
        return self._resolved_version

    def ensure_loaded(self) -> tuple[str, str]:
        """Lazily initialize the canonical backend and verify provenance without inference.

        Thread-safe: concurrent calls share one lock and never initialize duplicate models.
        """
        if self._backend is not None and self._resolved_version is not None:
            return self.model_id, self._resolved_version
        with self._init_lock:
            _, resolved_version = self._resolve_backend()
            return self.model_id, resolved_version

    def _resolve_override_version(self, backend: TextEncoderBackend) -> str:
        if self._explicit_model_version is not None:
            cleaned = self._explicit_model_version.strip()
            if not cleaned:
                raise EmbeddingSubsystemUnavailableError(
                    "Explicit model_version must not be empty."
                )
            return cleaned

        flag = getattr(backend, "using_finetuned_checkpoint", None)
        if isinstance(flag, bool):
            return CANONICAL_FINETUNED_VERSION if flag else CANONICAL_PRETRAINED_VERSION

        attr_ver = getattr(backend, "model_version", None)
        if isinstance(attr_ver, str) and attr_ver.strip():
            return attr_ver.strip()

        raise EmbeddingSubsystemUnavailableError(
            "Unable to verify model version provenance for injected encoder."
        )

    def _resolve_backend(self) -> tuple[TextEncoderBackend, str]:
        if self._backend is not None:
            if self._resolved_version is None:
                self._resolved_version = self._resolve_override_version(self._backend)
            return self._backend, self._resolved_version

        # 1. Prefer origin/ml SemanticMatcher using ModelRegistry (model_name_or_path=None)
        self._configure_torch_threads()
        try:
            from ml.src.matching.semantic_matcher import SemanticMatcher

            matcher = SemanticMatcher(device=self.device)
            flag = getattr(matcher, "using_finetuned_checkpoint", None)
            if not isinstance(flag, bool):
                raise EmbeddingSubsystemUnavailableError(
                    "Unable to verify SemanticMatcher checkpoint provenance."
                )
            resolved_version = CANONICAL_FINETUNED_VERSION if flag else CANONICAL_PRETRAINED_VERSION
            backend = cast(TextEncoderBackend, matcher)
            self._backend = backend
            self._resolved_version = resolved_version
            return backend, resolved_version
        except ImportError:
            pass
        except EmbeddingSubsystemUnavailableError:
            raise
        except Exception as exc:
            raise EmbeddingSubsystemUnavailableError(
                "Failed to initialize canonical SemanticMatcher backend."
            ) from exc

        # 2. Direct SentenceTransformer fallback: explicitly pretrained provenance only
        if self.model_id != CANONICAL_MODEL_ID:
            raise EmbeddingSubsystemUnavailableError(
                "Direct SentenceTransformer fallback only supports the canonical MiniLM model ID."
            )
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_id, device=self.device)
            self._backend = _SentenceTransformerBackend(model)
            self._resolved_version = CANONICAL_PRETRAINED_VERSION
            return self._backend, self._resolved_version
        except ImportError as exc:
            raise EmbeddingSubsystemUnavailableError(
                "No ML embedding backend is installed in this runtime."
            ) from exc
        except Exception as exc:
            raise EmbeddingSubsystemUnavailableError(
                "Failed to initialize SentenceTransformer embedding backend."
            ) from exc

    def embed_texts(self, texts: Sequence[str]) -> CanonicalEmbeddingOutput:
        """Encode a validated batch of canonical texts into 384-dim float32 unit vectors."""
        if texts is None or isinstance(texts, (str, bytes)):
            raise ValueError("texts must be a non-empty sequence of strings.")
        text_list = list(texts)
        if not text_list:
            raise ValueError("texts batch must not be empty.")
        if len(text_list) > self.max_batch_size:
            raise ValueError(
                f"Batch size {len(text_list)} exceeds max_batch_size={self.max_batch_size}."
            )

        cleaned: list[str] = []
        for idx, text in enumerate(text_list):
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Input text at index {idx} must be a non-empty string.")
            cleaned.append(text)

        self.ensure_loaded()
        backend, resolved_version = self._resolve_backend()
        try:
            raw_outputs = backend.encode(cleaned)
        except EmbeddingSubsystemUnavailableError:
            raise
        except Exception as exc:
            raise EmbeddingSubsystemUnavailableError(
                "Embedding inference failed in backend."
            ) from exc

        raw_rows = raw_outputs.tolist() if hasattr(raw_outputs, "tolist") else list(raw_outputs)

        if len(raw_rows) != len(cleaned):
            raise ValueError(
                f"Embedding backend returned {len(raw_rows)} vectors for {len(cleaned)} inputs."
            )

        vectors = [_to_float32_normalized(row, row_index=idx) for idx, row in enumerate(raw_rows)]
        return CanonicalEmbeddingOutput(
            vectors=vectors,
            model_id=self.model_id,
            model_version=resolved_version,
            dimension=CANONICAL_VECTOR_DIM,
        )

    def embed_one(self, text: str) -> tuple[list[float], str, str]:
        """Convenience wrapper encoding one canonical text -> (vector_384, model_id, model_version)."""
        result = self.embed_texts([text])
        return result.vectors[0], result.model_id, result.model_version


class _SentenceTransformerBackend:
    """Thin wrapper normalizing SentenceTransformer.encode kwargs."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def encode(self, texts: Sequence[str]) -> Any:
        return self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
