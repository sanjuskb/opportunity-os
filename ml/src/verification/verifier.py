"""Replaceable Evidence Verification Service supporting NLI DeBERTa-v3-small and mock/heuristic backends."""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Protocol

from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, MLInferenceError, ResourceManagedModelCache
from ml.src.infrastructure.security import safe_log_preview, validate_text_input
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

        p_clean = validate_text_input(premise, "premise_text")
        h_clean = validate_text_input(hypothesis, "hypothesis_claim")

        def _load():
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            model.eval()
            model.to(torch.device("cpu"))
            return tokenizer, model

        def _infer(bundle):
            tokenizer, model = bundle
            encoded = tokenizer(p_clean, h_clean, truncation=True, max_length=256, return_tensors="pt")
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

        if "_get_bundle" in self.__dict__ or type(self)._get_bundle is not CrossEncoderNLIBackend._get_bundle:
            return _infer(self._get_bundle())
        return self.cache.execute_with_model(f"nli::{self.model_name}", _load, _infer)


class LexicalConsistencyFallbackBackend:
    """Ultra-light CPU heuristic fallback used in offline CI unit tests or when RAM prohibits NLI weights."""

    model_name = "lexical-number-and-overlap-fallback-v1"

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        p_low = validate_text_input(premise, "premise_text").lower()
        h_low = validate_text_input(hypothesis, "hypothesis_claim").lower()
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
    and insufficient_evidence outcomes with configurable probability thresholds,
    timeout guarding, and non-crashing lexical fallback.
    """

    def __init__(
        self,
        backend: NLIProbabilityBackend | None = None,
        *,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.60,
        use_pretrained_nli: bool = True,
        timeout_seconds: float | None = 15.0,
        fallback_on_error: bool = True,
    ) -> None:
        if backend is not None:
            self.backend = backend
        elif use_pretrained_nli:
            self.backend = CrossEncoderNLIBackend()
        else:
            self.backend = LexicalConsistencyFallbackBackend()

        self.entailment_threshold = entailment_threshold
        self.contradiction_threshold = contradiction_threshold
        self.timeout_seconds = timeout_seconds
        self.fallback_on_error = fallback_on_error
        self._fallback_backend = LexicalConsistencyFallbackBackend()

    def _run_score_with_timeout(self, premise: str, hypothesis: str) -> dict[str, float]:
        if self.timeout_seconds is None or self.timeout_seconds <= 0:
            return self.backend.score_pair(premise, hypothesis)
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(self.backend.score_pair, premise, hypothesis)
            try:
                return fut.result(timeout=self.timeout_seconds)
            except FuturesTimeoutError as exc:
                raise TimeoutError(
                    f"NLI scoring exceeded timeout ({self.timeout_seconds:.1f}s)."
                ) from exc

    def verify_claim(self, request: VerificationRequest) -> VerificationResult:
        p_clean = validate_text_input(request.premise_text, "premise_text")
        h_clean = validate_text_input(request.hypothesis_claim, "hypothesis_claim")
        logger.debug(
            "Verifying claim_id=%s preview=%s",
            request.claim_id,
            safe_log_preview(h_clean),
        )

        active_model = getattr(self.backend, "model_name", "custom_nli")
        fallback_note = ""
        try:
            scores = self._run_score_with_timeout(p_clean, h_clean)
        except (MLInferenceError, TimeoutError, OSError, RuntimeError) as exc:
            if not self.fallback_on_error or isinstance(self.backend, LexicalConsistencyFallbackBackend):
                raise
            logger.warning(
                "Primary NLI backend failed (%s); falling back cleanly to lexical heuristic.",
                type(exc).__name__,
            )
            scores = self._fallback_backend.score_pair(p_clean, h_clean)
            active_model = f"{self._fallback_backend.model_name} (fallback_after_{type(exc).__name__})"
            fallback_note = f" [Degraded cleanly from primary NLI after {type(exc).__name__}]"

        ent = float(scores.get("entailment", 0.0))
        con = float(scores.get("contradiction", 0.0))
        neu = float(scores.get("neutral", max(0.0, 1.0 - ent - con)))

        if con >= self.contradiction_threshold and con > ent:
            verdict: VerdictLabel = "contradicted"
            reason = f"Auxiliary NLI flagged contradiction ({con:.2f} >= {self.contradiction_threshold:.2f}) relative to source evidence.{fallback_note}"
        elif ent >= self.entailment_threshold and con < self.contradiction_threshold:
            verdict = "supported"
            reason = f"Auxiliary NLI judged hypothesis entailed by evidence ({ent:.2f} >= {self.entailment_threshold:.2f}).{fallback_note}"
        else:
            verdict = "insufficient_evidence"
            reason = (
                f"Neither strong entailment ({ent:.2f}) nor clear contradiction ({con:.2f}) reached thresholds; manual verification recommended.{fallback_note}"
            )

        return VerificationResult(
            claim_id=request.claim_id,
            verdict=verdict,
            entailment_score=round(ent, 4),
            contradiction_score=round(con, 4),
            neutral_score=round(neu, 4),
            evidence_snippet=p_clean[:220],
            model_used=active_model,
            reason=reason,
        )
