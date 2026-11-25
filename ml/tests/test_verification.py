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
