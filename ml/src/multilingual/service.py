"""Replaceable Multilingual Understanding Service with confidence-gated LLM/translation fallback."""

from __future__ import annotations

import logging
from typing import Any, Protocol, Sequence

import numpy as np
from pydantic import BaseModel, Field

from ml.src.evaluation.retrieval_metrics import cosine_similarity_matrix
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, ResourceManagedModelCache
from ml.src.infrastructure.security import safe_log_preview, validate_text_input
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
        if texts is None:
            raise TypeError("texts sequence must not be None.")
        text_list = list(texts)
        if not text_list:
            return np.empty((0, 384), dtype=np.float32)

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
            return arr / np.clip(norms, 1e-12, None)

        if self._encoder_override is not None:
            return _encode_with(self._encoder_override)

        def _load() -> Any:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model_id, device="cpu")

        return self.cache.execute_with_model(
            f"multilingual::{self.model_id}",
            _load,
            _encode_with,
        )

    def match_query_to_documents(
        self,
        query_text: str,
        doc_texts: Sequence[str],
    ) -> tuple[list[tuple[int, float]], MultilingualUnderstandingResult]:
        validated_query = validate_text_input(query_text, "query_text")
        logger.debug("Processing multilingual query preview=%s", safe_log_preview(validated_query))
        prep = preprocess_multilingual_query(validated_query)

        if not doc_texts:
            meta = MultilingualUnderstandingResult(
                preprocessed=prep,
                model_id=self.model_id,
                embedding_dimension=384,
                top_similarity_score=None,
                fallback_triggered=False,
                fallback_query_text=None,
                warnings=["No candidate documents provided; returning empty ranked list cleanly."],
            )
            return [], meta

        validated_docs = [validate_text_input(d, f"doc_texts[{idx}]") for idx, d in enumerate(doc_texts)]
        q_emb = self.encode([prep.normalized_text])
        d_emb = self.encode(validated_docs)
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
                try:
                    candidate_fb = self.fallback_backend.normalize_to_english(
                        prep.original_text, prep.predicted_locale, prep.preserved_technical_terms
                    )
                    fallback_text = validate_text_input(candidate_fb, "fallback_query_text")
                    fallback_triggered = True
                    fb_emb = self.encode([fallback_text])
                    fb_sims = cosine_similarity_matrix(fb_emb, d_emb)[0]
                    if float(np.max(fb_sims)) > top_score or prep.predicted_locale in EMPIRICALLY_WEAK_DIRECT_LOCALES:
                        sims = fb_sims
                        top_score = float(np.max(sims))
                    warnings.append(
                        f"Locale '{prep.predicted_locale}' routed through translation fallback while retaining original text."
                    )
                except Exception as exc:
                    fallback_triggered = True
                    fallback_text = None
                    logger.warning(
                        "Translation fallback failed (%s); preserving original text and direct scores.",
                        type(exc).__name__,
                    )
                    warnings.append(
                        f"Translation fallback failed ({type(exc).__name__}); retained original text and direct embeddings safely."
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
