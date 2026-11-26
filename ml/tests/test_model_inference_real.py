"""
Real Model Inference & Sequential Memory/Eviction Lifecycle Tests (`ml/tests`).

Executes REAL Hugging Face & fine-tuned PyTorch inference on CPU under
ResourceManagedModelCache(max_loaded_models=1) so heavy checkpoints never stack in RAM:
  1. Fine-tuned `ml/artifacts/minilm-nexteras-v1` (or fallback baseline verification)
  2. Pretrained `sentence-transformers/all-MiniLM-L6-v2`
  3. Multilingual `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (8 Indian languages + Hinglish)
  4. Auxiliary NLI `cross-encoder/nli-deberta-v3-small` (supported, contradicted, insufficient_evidence)
"""

from __future__ import annotations

from pathlib import Path
import time

import numpy as np
import pytest

from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import ResourceManagedModelCache
from ml.src.matching.semantic_matcher import SemanticMatcher
from ml.src.multilingual.service import MultilingualUnderstandingService
from ml.src.verification.schemas import VerificationRequest
from ml.src.verification.verifier import CrossEncoderNLIBackend, EvidenceVerificationService


@pytest.mark.slow
def test_real_minilm_finetuned_and_baseline_inference() -> None:
    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
    try:
        reg = ModelRegistry("ml/model_configs/ml_registry.yaml")
        tuned_matcher = SemanticMatcher(cache=cache, registry=reg)

        ckpt_dir = Path("ml/artifacts/minilm-nexteras-v1")
        if ckpt_dir.exists() and any(ckpt_dir.iterdir()):
            assert tuned_matcher.using_finetuned_checkpoint is True

        opps = [
            {
                "doc_id": "be-pos",
                "title": "Transactional Backend Platform Intern",
                "doc_text": "Opportunity: Transactional Backend Platform Intern | Domain: backend_systems | Atomic booking state transitions and SQL row locks.",
            },
            {
                "doc_id": "sec-trap",
                "title": "Python Database Security Audit Intern",
                "doc_text": "Opportunity: Python Database Security Audit Intern | Domain: security | Write SQL injection fuzzers against login forms.",
            },
        ]
        student_bio = (
            "3rd Year B.Tech CSE | Skills: Python, PostgreSQL, Row Locks | "
            "Built auditorium reservation server preventing duplicate bookings."
        )
        t0 = time.perf_counter()
        ranked_1 = tuned_matcher.rank_opportunities(student_bio, opps, top_k=2)
        first_ms = (time.perf_counter() - t0) * 1000.0

        # Repeat inference must reuse cached weights identically and fast
        t1 = time.perf_counter()
        ranked_2 = tuned_matcher.rank_opportunities(student_bio, opps, top_k=2)
        repeat_ms = (time.perf_counter() - t1) * 1000.0

        assert [r.doc_id for r in ranked_1] == [r.doc_id for r in ranked_2]
        assert ranked_1[0].doc_id == "be-pos"
        assert cache.stats()["cache_hits"] >= 1
        assert repeat_ms <= first_ms + 500.0

        vecs = tuned_matcher.encode([student_bio, opps[0]["doc_text"]])
        assert vecs.shape == (2, 384)
        assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-4)

        # Explicitly verify pretrained baseline swaps cleanly via max_loaded_models=1 eviction
        base_matcher = SemanticMatcher("sentence-transformers/all-MiniLM-L6-v2", cache=cache)
        assert base_matcher.using_finetuned_checkpoint is False
        base_vecs = base_matcher.encode([student_bio])
        assert base_vecs.shape == (1, 384)
        assert len(cache.stats()["loaded_keys"]) == 1
    finally:
        cache.clear()


@pytest.mark.slow
def test_real_multilingual_encoder_8_locales_and_eviction() -> None:
    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
    try:
        svc = MultilingualUnderstandingService(cache=cache)
        docs = [
            "Opportunity: Backend REST API engineering internship in Python and SQL",
            "Opportunity: Embedded microcontroller C and robotics internship",
        ]
        queries = {
            "en": "Python backend API internship",
            "hi": "मुझे बैकएंड एपीआई इंटर्नशिप चाहिए",
            "te": "నాకు బ్యాకెండ్ ఇంటర్న్‌షిప్ కావాలి",
            "ta": "பின்தள இணைய பயிற்சி வேலை",
            "kn": "ಬ್ಯಾಕೆಂಡ್ ಅಭಿವೃದ್ಧಿ ಇಂಟರ್ನ್‌ಶಿಪ್",
            "ml": "ബാക്കെൻഡ് ഇന്റേൺഷിപ്പ് വേണം",
            "bn": "ব্যাকএন্ড ইন্টার্নশিপ খুঁজছি",
            "hinglish": "Mujhe Python API wali backend internship chahiye",
        }
        for locale, q in queries.items():
            ranked, meta = svc.match_query_to_documents(q, docs)
            assert meta.preprocessed.original_text == q
            assert meta.preprocessed.predicted_locale == locale
            assert meta.embedding_dimension == 384
            assert len(ranked) == 2

        embs = svc.encode([queries["en"], queries["hi"]])
        assert embs.shape == (2, 384)
        assert np.allclose(np.linalg.norm(embs, axis=1), 1.0, atol=1e-4)
        assert len(cache.stats()["loaded_keys"]) == 1
    finally:
        cache.clear()


@pytest.mark.slow
def test_real_nli_cross_encoder_inference() -> None:
    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)
    try:
        backend = CrossEncoderNLIBackend(cache=cache)
        svc = EvidenceVerificationService(backend=backend, timeout_seconds=30.0)

        sup = svc.verify_claim(
            VerificationRequest(
                claim_id="real-sup",
                premise_text="Developed asynchronous FastAPI REST services backed by PostgreSQL and Docker.",
                hypothesis_claim="Built FastAPI web APIs using PostgreSQL and Docker containers.",
            )
        )
        assert sup.verdict == "supported"
        assert sup.is_advisory_only is True

        con = svc.verify_claim(
            VerificationRequest(
                claim_id="real-con",
                premise_text="Graduated B.Tech ECE with 7.4 CGPA and 2-month embedded project.",
                hypothesis_claim="Maintained 9.9 CGPA in Computer Science with 4 years backend employment.",
            )
        )
        assert con.verdict == "contradicted"

        ins = svc.verify_claim(
            VerificationRequest(
                claim_id="real-ins",
                premise_text="Participated in regional hackathon building an Android campus guide.",
                hypothesis_claim="Won 1st prize nationally and lowered latency by 70 percent.",
            )
        )
        assert ins.verdict == "insufficient_evidence"
    finally:
        cache.clear()
