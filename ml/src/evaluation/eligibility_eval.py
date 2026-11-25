"""Reproducible evaluation for Deterministic Eligibility Engine."""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from typing import Any

from ml.src.eligibility.engine import DeterministicEligibilityEngine
from ml.src.eligibility.schemas import StructuredOpportunityRequirements, StudentEligibilityInput


def evaluate_eligibility_benchmark(
    engine: DeterministicEligibilityEngine,
    dataset_path: str | Path = "ml/datasets/synthetic/eligibility_edge_cases.json",
) -> dict[str, Any]:
    raw = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    ref_date = date.fromisoformat(raw["reference_date"])
    cases = raw["cases"]

    correct = 0
    false_eligible = 0
    false_ineligible = 0
    traceable_count = 0
    unknown_handled = 0
    unknown_total = 0
    per_case: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    for case in cases:
        stu = StudentEligibilityInput.model_validate(case["student"])
        req = StructuredOpportunityRequirements.model_validate(case["requirements"])
        dec = engine.evaluate(stu, req, reference_date=ref_date)
        exp = case["expected_status"]

        if dec.status == exp:
            correct += 1
        elif dec.status == "eligible" and exp != "eligible":
            false_eligible += 1
        elif dec.status == "ineligible" and exp == "eligible":
            false_ineligible += 1

        if dec.audit_trail and all(item.evidence_source and item.reason for item in dec.audit_trail):
            traceable_count += 1

        if exp in {"needs_more_info", "unable_to_verify"}:
            unknown_total += 1
            if dec.status == exp:
                unknown_handled += 1

        per_case.append(
            {
                "case_id": case["case_id"],
                "expected": exp,
                "predicted": dec.status,
                "correct": dec.status == exp,
                "audit_rules_checked": len(dec.audit_trail),
            }
        )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "dataset": raw["dataset_name"],
        "is_synthetic": raw["is_synthetic"],
        "cases_evaluated": len(cases),
        "exact_outcome_accuracy": round(correct / max(1, len(cases)), 4),
        "false_eligible_rate": round(false_eligible / max(1, len(cases)), 4),
        "false_ineligible_rate": round(false_ineligible / max(1, len(cases)), 4),
        "unknown_and_unverified_handling_rate": round(unknown_handled / max(1, unknown_total), 4),
        "explanation_traceability_rate": round(traceable_count / max(1, len(cases)), 4),
        "total_latency_ms": elapsed_ms,
        "per_case": per_case,
    }
