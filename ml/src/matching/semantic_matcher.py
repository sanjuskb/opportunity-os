"""Decoupled inference interface for base vs. personally fine-tuned semantic bi-encoder matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ml.src.evaluation.retrieval_metrics import cosine_similarity_matrix
from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, ResourceManagedModelCache


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
        model = self._get_model()
        return model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def rank_opportunities(
        self,
        student_query: str,
        opportunities: Sequence[dict[str, str]],
        top_k: int = 5,
    ) -> list[RankedMatch]:
        if not opportunities:
            return []
        q_emb = self.encode([student_query])
        d_texts = [o["doc_text"] for o in opportunities]
        d_emb = self.encode(d_texts)
        sims = cosine_similarity_matrix(q_emb, d_emb)[0]
        order = np.argsort(-sims)[:top_k]
        return [
            RankedMatch(
                doc_id=opportunities[int(idx)]["doc_id"],
                title=opportunities[int(idx)].get("title", opportunities[int(idx)]["doc_id"]),
                score=round(float(sims[int(idx)]), 4),
            )
            for idx in order
        ]
