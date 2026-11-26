"""Reproducible evaluation for auxiliary NLI / Evidence Consistency Verification."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ml.src.verification.schemas import VerificationRequest
from ml.src.verification.verifier import EvidenceVerificationService


def evaluate_verification_benchmark(
    service: EvidenceVerificationService,
    dataset_path: str | Path = "ml/datasets/synthetic/verification_claims_benchmark.json",
) -> dict[str, Any]:
    raw = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    cases = raw["cases"]

    correct = 0
    false_supported = 0
    per_class_total: dict[str, int] = {"supported": 0, "contradicted": 0, "insufficient_evidence": 0}
    per_class_hit: dict[str, int] = {"supported": 0, "contradicted": 0, "insufficient_evidence": 0}
    per_case: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    for case in cases:
        req = VerificationRequest(
            claim_id=case["claim_id"],
            premise_text=case["premise_text"],
            hypothesis_claim=case["hypothesis_claim"],
        )
        res = service.verify_claim(req)
        exp = case["expected_verdict"]
        per_class_total[exp] = per_class_total.get(exp, 0) + 1
        if res.verdict == exp:
            correct += 1
            per_class_hit[exp] = per_class_hit.get(exp, 0) + 1
        elif res.verdict == "supported" and exp != "supported":
            false_supported += 1

        per_case.append(
            {
                "claim_id": case["claim_id"],
                "expected": exp,
                "predicted": res.verdict,
                "entailment_score": res.entailment_score,
                "contradiction_score": res.contradiction_score,
                "correct": res.verdict == exp,
            }
        )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "dataset": raw["dataset_name"],
        "is_synthetic": raw["is_synthetic"],
        "model_used": getattr(service.backend, "model_name", "unknown"),
        "cases_evaluated": len(cases),
        "accuracy": round(correct / max(1, len(cases)), 4),
        "false_supported_rate": round(false_supported / max(1, len(cases)), 4),
        "class_accuracy": {
            cls: round(per_class_hit[cls] / max(1, per_class_total[cls]), 4)
            for cls in per_class_total
        },
        "total_latency_ms": elapsed_ms,
        "per_case": per_case,
    }
