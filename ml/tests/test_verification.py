"""Unit tests for Workstream E: Auxiliary Evidence Verification (NLI + Thresholds)."""

from __future__ import annotations

from ml.src.evaluation.verification_eval import evaluate_verification_benchmark
from ml.src.verification.schemas import VerificationRequest
from ml.src.verification.verifier import EvidenceVerificationService


class _MockNLIBackend:
    model_name = "mock-nli-cross-encoder"

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        if "contradicted" in hypothesis.lower():
            return {"entailment": 0.05, "contradiction": 0.88, "neutral": 0.07}
        if "supported" in hypothesis.lower():
            return {"entailment": 0.91, "contradiction": 0.02, "neutral": 0.07}
        return {"entailment": 0.30, "contradiction": 0.15, "neutral": 0.55}


def test_verification_thresholds_and_advisory_flags() -> None:
    svc = EvidenceVerificationService(backend=_MockNLIBackend())

    sup = svc.verify_claim(VerificationRequest(claim_id="1", premise_text="Verified source.", hypothesis_claim="Supported fact."))
    assert sup.verdict == "supported"
    assert sup.is_advisory_only is True
    assert sup.never_auto_approves_actions is True

    con = svc.verify_claim(VerificationRequest(claim_id="2", premise_text="Verified source.", hypothesis_claim="Contradicted claim."))
    assert con.verdict == "contradicted"

    amb = svc.verify_claim(VerificationRequest(claim_id="3", premise_text="Verified source.", hypothesis_claim="Ambiguous metric."))
    assert amb.verdict == "insufficient_evidence"


def test_verification_lexical_fallback_benchmark() -> None:
    svc = EvidenceVerificationService(use_pretrained_nli=False)
    metrics = evaluate_verification_benchmark(svc)
    assert metrics["cases_evaluated"] == 9
    assert metrics["false_supported_rate"] == 0.0
    assert metrics["accuracy"] >= 0.75


class _TimeoutNLIBackend:
    model_name = "slow-nli-mock"

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        import time

        time.sleep(0.3)
        return {"entailment": 0.99, "contradiction": 0.0, "neutral": 0.01}


class _BrokenLoadNLIBackend:
    model_name = "broken-nli-mock"

    def score_pair(self, premise: str, hypothesis: str) -> dict[str, float]:
        from ml.src.infrastructure.runtime import MLInferenceError

        raise MLInferenceError("MODEL_LOAD_FAILED", "Simulated offline weights failure")


def test_verification_invalid_inputs_timeout_and_load_failure_fallback() -> None:
    import pytest

    svc_timeout = EvidenceVerificationService(
        backend=_TimeoutNLIBackend(), timeout_seconds=0.05, fallback_on_error=True
    )
    res_t = svc_timeout.verify_claim(
        VerificationRequest(
            claim_id="t1",
            premise_text="Built FastAPI REST APIs with PostgreSQL in 2025.",
            hypothesis_claim="Built FastAPI REST APIs with PostgreSQL in 2025.",
        )
    )
    assert "fallback_after_TimeoutError" in res_t.model_used
    assert res_t.is_advisory_only is True
    assert res_t.never_auto_approves_actions is True

    svc_err = EvidenceVerificationService(backend=_BrokenLoadNLIBackend(), fallback_on_error=True)
    res_e = svc_err.verify_claim(
        VerificationRequest(
            claim_id="e1",
            premise_text="GPA 7.4 in B.Tech ECE.",
            hypothesis_claim="GPA 9.8 in B.Tech CSE.",
        )
    )
    assert res_e.verdict == "contradicted"
    assert "fallback_after_MLInferenceError" in res_e.model_used

    with pytest.raises(ValueError):
        svc_err.verify_claim(
            VerificationRequest(claim_id="bad", premise_text="   ", hypothesis_claim="Built API")
        )
