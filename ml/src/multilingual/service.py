"""Replaceable Multilingual Understanding Service with confidence-gated LLM/translation fallback."""

from __future__ import annotations

import logging
from typing import Any, Protocol, Sequence

import numpy as np
from pydantic import BaseModel, Field

from ml.src.evaluation.retrieval_metrics import cosine_similarity_matrix
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, ResourceManagedModelCache
from ml.src.infrastructure.security import safe_log_preview
from ml.src.multilingual.preprocessing import PreprocessedMultilingualQuery, preprocess_multilingual_query

logger = logging.getLogger("nexteras.ml.multilingual")

DEFAULT_MULTILINGUAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Empirically measured on nexteras_multilingual_7_languages_eval: native South/East Indic queries
# to English postings show low/negative retrieval margins and should route via translation/LLM fallback when available.
EMPIRICALLY_WEAK_DIRECT_LOCALES = {"bn", "kn", "ml", "ta", "te"}


class TranslationFallbackBackend(Protocol):
    """Optional external LLM/translation fallback preserving technical terminology."""

    def normalize_to_english(self, text: str, source_locale: str, preserved_terms: list[str]) -> str:
        ...


class MultilingualUnderstandingResult(BaseModel):
    preprocessed: PreprocessedMultilingualQuery
    model_id: str
    embedding_dimension: int
    top_similarity_score: float | None = None
    fallback_triggered: bool = False
    fallback_query_text: str | None = None
    warnings: list[str] = Field(default_factory=list)


class MultilingualUnderstandingService:
    """
    Lazy CPU encoder for English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and Hinglish.
    Supports fallback hooks when confidence is below threshold without overwriting original_text.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MULTILINGUAL_MODEL,
        cache: ResourceManagedModelCache | None = None,
        fallback_backend: TranslationFallbackBackend | None = None,
        low_confidence_threshold: float = 0.28,
        encoder_override: Any | None = None,
    ) -> None:
        self.model_id = model_id
        self.cache = cache or GLOBAL_MODEL_CACHE
        self.fallback_backend = fallback_backend
        self.low_confidence_threshold = low_confidence_threshold
        self._encoder_override = encoder_override

    def _get_model(self) -> Any:
        if self._encoder_override is not None:
            return self._encoder_override

        def _load() -> Any:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model_id, device="cpu")

        return self.cache.get_or_load(f"multilingual::{self.model_id}", _load)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._get_model()
        return model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def match_query_to_documents(
        self,
        query_text: str,
        doc_texts: Sequence[str],
    ) -> tuple[list[tuple[int, float]], MultilingualUnderstandingResult]:
        logger.debug("Processing multilingual query preview=%s", safe_log_preview(query_text))
        prep = preprocess_multilingual_query(query_text)
        q_emb = self.encode([prep.normalized_text])
        d_emb = self.encode(doc_texts)
        sims = cosine_similarity_matrix(q_emb, d_emb)[0]
        top_score = float(np.max(sims)) if len(sims) else 0.0

        warnings: list[str] = []
        fallback_triggered = False
        fallback_text: str | None = None

        needs_fallback = (
            prep.predicted_locale in EMPIRICALLY_WEAK_DIRECT_LOCALES
            or prep.predicted_locale == "hinglish"
            or top_score < self.low_confidence_threshold
        )
        if needs_fallback:
            if self.fallback_backend is not None:
                fallback_triggered = True
                fallback_text = self.fallback_backend.normalize_to_english(
                    prep.original_text, prep.predicted_locale, prep.preserved_technical_terms
                )
                fb_emb = self.encode([fallback_text])
                fb_sims = cosine_similarity_matrix(fb_emb, d_emb)[0]
                if float(np.max(fb_sims)) > top_score or prep.predicted_locale in EMPIRICALLY_WEAK_DIRECT_LOCALES:
                    sims = fb_sims
                    top_score = float(np.max(sims))
                warnings.append(
                    f"Locale '{prep.predicted_locale}' routed through translation fallback while retaining original text."
                )
            else:
                warnings.append(
                    f"Locale '{prep.predicted_locale}' has low/unreliable direct cross-lingual retrieval confidence ({top_score:.3f}); LLM/translation fallback recommended."
                )

        order = np.argsort(-sims)
        ranked = [(int(idx), round(float(sims[int(idx)]), 4)) for idx in order]
        meta = MultilingualUnderstandingResult(
            preprocessed=prep,
            model_id=self.model_id,
            embedding_dimension=int(q_emb.shape[1]),
            top_similarity_score=round(top_score, 4),
            fallback_triggered=fallback_triggered,
            fallback_query_text=fallback_text,
            warnings=warnings,
        )
        return ranked, meta
