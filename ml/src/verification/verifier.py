"""Replaceable Evidence Verification Service supporting NLI DeBERTa-v3-small and mock/heuristic backends."""

from __future__ import annotations

import logging
import re
from typing import Protocol

from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, ResourceManagedModelCache
from ml.src.infrastructure.security import safe_log_preview
from ml.src.verification.schemas import VerificationRequest, VerificationResult, VerdictLabel

logger = logging.getLogger("nexteras.ml.verification")

DEFAULT_NLI_MODEL = "cross-encoder/nli-deberta-v3-small"


class NLIProbabilityBackend(Protocol):
    """Replaceable protocol returning normalized {entailment, contradiction, neutral} probabilities."""

    model_name: str

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        ...


class CrossEncoderNLIBackend:
    """CPU lazy-loaded Hugging Face NLI cross-encoder (reads id2label dynamically)."""

    def __init__(self, model_name: str = DEFAULT_NLI_MODEL, cache: ResourceManagedModelCache | None = None) -> None:
        self.model_name = model_name
        self.cache = cache or GLOBAL_MODEL_CACHE

    def _get_bundle(self):
        def _load():
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            model.eval()
            model.to(torch.device("cpu"))
            return tokenizer, model

        return self.cache.get_or_load(f"nli::{self.model_name}", _load)

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        import torch

        tokenizer, model = self._get_bundle()
        encoded = tokenizer(premise, hypothesis, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad():
            logits = model(**encoded).logits[0]
            probs = torch.softmax(logits, dim=-1).tolist()

        id2label = getattr(model.config, "id2label", {0: "contradiction", 1: "entailment", 2: "neutral"})
        mapped = {"entailment": 0.0, "contradiction": 0.0, "neutral": 0.0}
        for idx, p in enumerate(probs):
            lbl = str(id2label.get(idx, "")).lower()
            if "entail" in lbl:
                mapped["entailment"] = round(float(p), 4)
            elif "contra" in lbl:
                mapped["contradiction"] = round(float(p), 4)
            else:
                mapped["neutral"] = round(float(p), 4)
        return mapped


class LexicalConsistencyFallbackBackend:
    """Ultra-light CPU heuristic fallback used in offline CI unit tests or when RAM prohibits NLI weights."""

    model_name = "lexical-number-and-overlap-fallback-v1"

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        p_low = premise.lower()
        h_low = hypothesis.lower()
        p_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", p_low))
        h_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", h_low))

        # Flag direct numerical fabrication or negation flip
        neg_flip = (
            ("without " in h_low and "without " not in p_low)
            or ("no " in h_low and "no " not in p_low)
            or ("never " in h_low and "never " not in p_low)
        )
        if (h_nums and p_nums and not h_nums.issubset(p_nums)) or neg_flip:
            return {"entailment": 0.08, "contradiction": 0.82, "neutral": 0.10}

        stop = {"a", "an", "the", "with", "in", "on", "of", "for", "and", "or", "to", "using", "built"}
        p_toks = set(re.findall(r"[a-z0-9+.#]+", p_low)) - stop
        h_toks = set(re.findall(r"[a-z0-9+.#]+", h_low)) - stop
        overlap = len(p_toks & h_toks) / max(1, len(h_toks))
        if overlap >= 0.72 and not (h_nums - p_nums):
            return {"entailment": 0.85, "contradiction": 0.05, "neutral": 0.10}
        return {"entailment": 0.20, "contradiction": 0.12, "neutral": 0.68}


class EvidenceVerificationService:
    """
    Auxiliary evidence consistency evaluator distinguishing supported, contradicted,
    and insufficient_evidence outcomes with configurable probability thresholds.
    """

    def __init__(
        self,
        backend: NLIProbabilityBackend | None = None,
        *,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.60,
        use_pretrained_nli: bool = True,
    ) -> None:
        if backend is not None:
            self.backend = backend
        elif use_pretrained_nli:
            self.backend = CrossEncoderNLIBackend()
        else:
            self.backend = LexicalConsistencyFallbackBackend()

        self.entailment_threshold = entailment_threshold
        self.contradiction_threshold = contradiction_threshold

    def verify_claim(self, request: VerificationRequest) -> VerificationResult:
        logger.debug(
            "Verifying claim_id=%s preview=%s",
            request.claim_id,
            safe_log_preview(request.hypothesis_claim),
        )
        scores = self.backend.score_pair(request.premise_text, request.hypothesis_claim)
        ent = float(scores.get("entailment", 0.0))
        con = float(scores.get("contradiction", 0.0))
        neu = float(scores.get("neutral", max(0.0, 1.0 - ent - con)))

        if con >= self.contradiction_threshold and con > ent:
            verdict: VerdictLabel = "contradicted"
            reason = f"Auxiliary NLI flagged contradiction ({con:.2f} >= {self.contradiction_threshold:.2f}) relative to source evidence."
        elif ent >= self.entailment_threshold and con < self.contradiction_threshold:
            verdict = "supported"
            reason = f"Auxiliary NLI judged hypothesis entailed by evidence ({ent:.2f} >= {self.entailment_threshold:.2f})."
        else:
            verdict = "insufficient_evidence"
            reason = (
                f"Neither strong entailment ({ent:.2f}) nor clear contradiction ({con:.2f}) reached thresholds; manual verification recommended."
            )

        return VerificationResult(
            claim_id=request.claim_id,
            verdict=verdict,
            entailment_score=round(ent, 4),
            contradiction_score=round(con, 4),
            neutral_score=round(neu, 4),
            evidence_snippet=request.premise_text[:220],
            model_used=getattr(self.backend, "model_name", "custom_nli"),
            reason=reason,
        )
