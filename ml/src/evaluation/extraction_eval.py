"""Reproducible evaluation for Resume Skill & Profile Extraction."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ml.src.extraction.extractor import ResumeExtractionService


def evaluate_extraction_benchmark(
    service: ResumeExtractionService,
    dataset_path: str | Path = "ml/datasets/synthetic/resume_extraction_benchmark.json",
) -> dict[str, Any]:
    path = Path(dataset_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = raw["cases"]

    scalar_hits = 0
    scalar_total = 0
    skill_tp = 0
    skill_fp = 0
    skill_fn = 0
    unsupported_count = 0
    schema_valid = 0
    missing_handled_correctly = 0
    per_case: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    for case in cases:
        exp = case["expected"]
        resp = service.extract_from_text(case["resume_text"])
        prof = resp.profile
        if resp.validation_status in {"valid", "recovered_partial_json", "fallback_after_llm_error"}:
            schema_valid += 1

        for fld, p_val in [
            ("full_name", prof.full_name),
            ("degree", prof.degree),
            ("branch", prof.branch_or_specialization),
            ("graduation_year", prof.graduation_year),
        ]:
            scalar_total += 1
            if p_val == exp[fld]:
                scalar_hits += 1

        if "cgpa" in exp:
            scalar_total += 1
            if exp["cgpa"] is None:
                if prof.cgpa is None and "academic_score" in prof.missing_fields:
                    scalar_hits += 1
                    missing_handled_correctly += 1
            elif prof.cgpa == exp["cgpa"]:
                scalar_hits += 1
        elif "percentage" in exp:
            scalar_total += 1
            if prof.percentage == exp["percentage"]:
                scalar_hits += 1

        if exp.get("full_name") is None and "full_name" in prof.missing_fields:
            missing_handled_correctly += 1

        pred_skills = {s.lower() for s in resp.normalized_skills}
        req_skills = {s.lower() for s in exp["required_skills"]}
        forb_skills = {s.lower() for s in exp.get("forbidden_skills", [])}

        tp = len(pred_skills & req_skills)
        fn = len(req_skills - pred_skills)
        fp = len(pred_skills & forb_skills)
        skill_tp += tp
        skill_fn += fn
        skill_fp += fp
        unsupported_count += fp

        per_case.append(
            {
                "case_id": case["case_id"],
                "skill_recall": round(tp / max(1, len(req_skills)), 4),
                "forbidden_hallucinated": sorted(pred_skills & forb_skills),
                "missing_fields_detected": prof.missing_fields,
            }
        )

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    precision = skill_tp / max(1, skill_tp + skill_fp)
    recall = skill_tp / max(1, skill_tp + skill_fn)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "dataset": raw["dataset_name"],
        "is_synthetic": raw["is_synthetic"],
        "cases_evaluated": len(cases),
        "schema_validity_rate": round(schema_valid / len(cases), 4),
        "scalar_exact_match_accuracy": round(scalar_hits / max(1, scalar_total), 4),
        "skill_precision": round(precision, 4),
        "skill_recall": round(recall, 4),
        "skill_f1": round(f1, 4),
        "unsupported_extraction_count": unsupported_count,
        "missing_field_checks_passed": missing_handled_correctly,
        "total_latency_ms": elapsed_ms,
        "per_case": per_case,
    }
