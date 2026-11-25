"""Decoupled inference interface for base vs. fine-tuned semantic bi-encoder matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from ml.src.evaluation.retrieval_metrics import cosine_similarity_matrix


@dataclass(frozen=True)
class RankedMatch:
    doc_id: str
    title: str
    score: float


class SemanticMatcher:
    """Wrapper over SentenceTransformer keeping model loading decoupled from API routes."""

    def __init__(self, model_name_or_path: str | Path, device: str = "cpu") -> None:
        from sentence_transformers import SentenceTransformer

        self.model_identifier = str(model_name_or_path)
        self.device = device
        self._model = SentenceTransformer(self.model_identifier, device=device)

    @property
    def embedding_dimension(self) -> int:
        dim = self._model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return self._model.encode(
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
