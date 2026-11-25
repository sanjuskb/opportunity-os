"""Unit tests for Workstream B: Multilingual Preprocessing, Language Detection & Fallback."""

from __future__ import annotations

import numpy as np

from ml.src.multilingual.preprocessing import preprocess_multilingual_query
from ml.src.multilingual.service import MultilingualUnderstandingService


class _MockMultilingualEncoder:
    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False):
        vecs = []
        for t in texts:
            low = str(t).lower()
            if "fastapi" in low or "backend" in low or "बैकएंड" in low or "బ్యాకెండ్" in low:
                v = np.array([0.9, 0.1, 0.0, 0.0], dtype=float)
            elif "react" in low or "frontend" in low:
                v = np.array([0.1, 0.9, 0.0, 0.0], dtype=float)
            else:
                v = np.array([0.0, 0.0, 1.0, 0.0], dtype=float)
            vecs.append(v / np.linalg.norm(v))
        return np.vstack(vecs)


class _MockTranslator:
    def normalize_to_english(self, text: str, source_locale: str, preserved_terms: list[str]) -> str:
        return "Need a FastAPI backend API internship " + " ".join(preserved_terms)


def test_multilingual_preprocessing_all_7_languages_plus_hinglish() -> None:
    samples = {
        "en": "Looking for Python FastAPI backend internship",
        "hi": "मुझे Python और बैकएंड इंटर्नशिप चाहिए",
        "te": "నాకు SQL మరియు బ్యాకెండ్ ఇంటర్న్‌షిప్ కావాలి",
        "ta": "எனக்கு React மற்றும் இணைய பயிற்சி வேண்டும்",
        "kn": "ನನಗೆ ಡೇಟಾಬೇಸ್ ಇಂಟರ್ನ್‌షిಪ್ ಬೇಕು",
        "ml": "എനിക്ക് ബാക്കെൻഡ് ഇന്റേൺഷിപ്പ് വേണം",
        "bn": "আমার ব্যাকএন্ড ইন্টার্নশিপ দরকার",
        "hinglish": "Mujhe Python aur FastAPI wali backend internship chahiye",
    }
    for exp_locale, text in samples.items():
        prep = preprocess_multilingual_query(text)
        assert prep.original_text == text
        assert prep.predicted_locale == exp_locale
        if "Python" in text:
            assert "Python" in prep.preserved_technical_terms
        if "SQL" in text:
            assert "SQL" in prep.preserved_technical_terms


def test_multilingual_service_fallback_preserves_original_text() -> None:
    svc = MultilingualUnderstandingService(
        fallback_backend=_MockTranslator(),
        low_confidence_threshold=0.95,
        encoder_override=_MockMultilingualEncoder(),
    )
    hinglish_q = "Mujhe Python API job chahiye"
    ranked, meta = svc.match_query_to_documents(
        hinglish_q,
        ["Frontend React role", "FastAPI backend server internship"],
    )
    assert meta.preprocessed.original_text == hinglish_q
    assert meta.fallback_triggered is True
    assert ranked[0][0] == 1

    # Also verify empirically weak native South Indian script routes through fallback cleanly
    te_q = "నాకు కంప్యూటర్ ఉద్యోగం కావాలి"
    ranked_te, meta_te = svc.match_query_to_documents(
        te_q,
        ["Frontend React role", "FastAPI backend server internship"],
    )
    assert meta_te.preprocessed.original_text == te_q
    assert meta_te.fallback_triggered is True
    assert ranked_te[0][0] == 1
