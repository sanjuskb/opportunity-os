"""Decoupled inference interface for base vs. personally fine-tuned semantic bi-encoder matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ml.src.evaluation.retrieval_metrics import cosine_similarity_matrix
from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, MLInferenceError, ResourceManagedModelCache
from ml.src.infrastructure.security import validate_text_input


@dataclass(frozen=True)
class RankedMatch:
    doc_id: str
    title: str
    score: float


class SemanticMatcher:
    """
    Lazy CPU bi-encoder wrapper keeping model loading cleanly decoupled from API routes.
    Automatically resolves Sanju's fine-tuned checkpoint when present, or safely falls
    back to pretrained 'sentence-transformers/all-MiniLM-L6-v2' without failing.
    """

    def __init__(
        self,
        model_name_or_path: str | Path | None = None,
        device: str = "cpu",
        *,
        cache: ResourceManagedModelCache | None = None,
        registry: ModelRegistry | None = None,
        encoder_override: Any | None = None,
    ) -> None:
        self.device = device
        self.cache = cache or GLOBAL_MODEL_CACHE
        self._encoder_override = encoder_override

        if model_name_or_path is not None:
            self.model_identifier = str(model_name_or_path)
            self.using_finetuned_checkpoint = Path(self.model_identifier).exists()
        else:
            reg = registry or ModelRegistry()
            spec = reg.get("semantic_matcher")
            self.model_identifier, self.using_finetuned_checkpoint = spec.resolve_active_identifier()

    def _get_model(self) -> Any:
        if self._encoder_override is not None:
            return self._encoder_override

        def _load() -> Any:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model_identifier, device=self.device)

        return self.cache.get_or_load(f"semantic::{self.model_identifier}", _load)

    @property
    def embedding_dimension(self) -> int:
        if self._encoder_override is not None and hasattr(self._encoder_override, "get_sentence_embedding_dimension"):
            dim = self._encoder_override.get_sentence_embedding_dimension()
            return int(dim) if dim is not None else 384
        return 384

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if texts is None:
            raise TypeError("texts sequence must not be None.")
        text_list = list(texts)
        if not text_list:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        cleaned = [validate_text_input(t, f"texts[{idx}]") for idx, t in enumerate(text_list)]

        def _encode_with(model: Any) -> np.ndarray:
            arr = model.encode(
                cleaned,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            arr = arr / np.clip(norms, 1e-12, None)
            return arr

        if self._encoder_override is not None:
            return _encode_with(self._encoder_override)

        def _load() -> Any:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model_identifier, device=self.device)

        try:
            # Respect instance monkeypatches and subclass overrides cleanly without hitting HF loader
            if "_get_model" in self.__dict__ or type(self)._get_model is not SemanticMatcher._get_model:
                return _encode_with(self._get_model())
            return self.cache.execute_with_model(
                f"semantic::{self.model_identifier}",
                _load,
                _encode_with,
            )
        except MLInferenceError:
            raise
        except Exception as exc:
            raise MLInferenceError(
                code="SEMANTIC_ENCODE_FAILED",
                message=f"Semantic embedding inference failed cleanly: {exc}",
                cause=exc,
            ) from exc

    def rank_opportunities(
        self,
        student_query: str,
        opportunities: Sequence[dict[str, str]],
        top_k: int = 5,
    ) -> list[RankedMatch]:
        validated_query = validate_text_input(student_query, "student_query")
        if not opportunities or top_k <= 0:
            return []
        d_texts: list[str] = []
        valid_opps: list[dict[str, str]] = []
        for idx, opp in enumerate(opportunities):
            if not isinstance(opp, dict) or not opp.get("doc_id") or not opp.get("doc_text"):
                raise ValueError(f"Malformed opportunity at index {idx}: 'doc_id' and 'doc_text' are required.")
            d_texts.append(validate_text_input(str(opp["doc_text"]), f"opportunities[{idx}].doc_text"))
            valid_opps.append(opp)

        q_emb = self.encode([validated_query])
        d_emb = self.encode(d_texts)
        sims = cosine_similarity_matrix(q_emb, d_emb)[0]
        order = np.argsort(-sims)[: min(top_k, len(valid_opps))]
        return [
            RankedMatch(
                doc_id=str(valid_opps[int(idx)]["doc_id"]),
                title=str(valid_opps[int(idx)].get("title") or valid_opps[int(idx)]["doc_id"]),
                score=round(float(sims[int(idx)]), 4),
            )
            for idx in order
        ]
