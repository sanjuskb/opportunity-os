"""Reproducible evaluation for Deterministic Opportunity Ranking Baseline."""

from __future__ import annotations

import json
import math
import time
from datetime import date
from pathlib import Path
from typing import Any

from ml.src.eligibility.schemas import EligibilityDecision
from ml.src.ranking.baseline_ranker import DeterministicOpportunityRanker
from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences


def evaluate_ranking_benchmark(
    ranker: DeterministicOpportunityRanker,
    dataset_path: str | Path = "ml/datasets/synthetic/ranking_benchmark.json",
) -> dict[str, Any]:
    raw = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    ref_date = date.fromisoformat(raw["reference_date"])
    prefs = StudentRankingPreferences.model_validate(raw["student_preferences"])

    candidates: list[CandidateOpportunity] = []
    expected_grades: dict[str, int] = {}
    for row in raw["candidates"]:
        is_elig = bool(row.get("is_eligible", True))
        elig_dec = EligibilityDecision(
            opportunity_id=row["opportunity_id"],
            status=row.get("eligibility_status", "eligible" if is_elig else "ineligible"),
            is_eligible=is_elig,
            matched_required_skills=row.get("matched_required_skills", []),
            missing_required_skills=row.get("missing_required_skills", []),
            summary_reason=row.get("summary_reason", "Deterministic pre-check passed."),
        )
        cand = CandidateOpportunity(
            opportunity_id=row["opportunity_id"],
            title=row["title"],
            organization=row["organization"],
            opportunity_type=row.get("opportunity_type", "internship"),
            location=row.get("location", ""),
            is_remote=row.get("is_remote", False),
            source_url=row.get("source_url"),
            is_verified_source=row.get("is_verified_source", False),
            has_compensation=row.get("has_compensation", False),
            monthly_compensation_inr=row.get("monthly_compensation_inr"),
            deadline=date.fromisoformat(row["deadline"]) if row.get("deadline") else None,
            semantic_similarity=row.get("semantic_similarity"),
            eligibility=elig_dec,
        )
        candidates.append(cand)
        if "ideal_grade" in row:
            expected_grades[row["opportunity_id"]] = int(row["ideal_grade"])

    t0 = time.perf_counter()
    res1 = ranker.rank(candidates, prefs, reference_date=ref_date)
    res2 = ranker.rank(candidates, prefs, reference_date=ref_date)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    ranked_ids = [r.opportunity_id for r in res1.ranked]
    deterministic_identical = (ranked_ids == [r.opportunity_id for r in res2.ranked])
    eligibility_violations = sum(1 for r in res1.ranked if r.eligibility_status != "eligible")

    dcg = sum((2 ** expected_grades.get(oid, 0) - 1) / math.log2(rank + 1) for rank, oid in enumerate(ranked_ids[:3], start=1))
    ideal = sorted(expected_grades.values(), reverse=True)[:3]
    idcg = sum((2 ** g - 1) / math.log2(rank + 1) for rank, g in enumerate(ideal, start=1)) or 1.0
    ndcg_at_3 = round(dcg / idcg, 4)
    top_1_correct = 1.0 if (ranked_ids and ranked_ids[0] == "rk-top-01") else 0.0

    return {
        "dataset": raw["dataset_name"],
        "is_synthetic": raw["is_synthetic"],
        "total_candidates": res1.total_input,
        "ranked_count": len(res1.ranked),
        "excluded_count": len(res1.excluded),
        "duplicates_removed": res1.duplicates_removed,
        "expired_removed": res1.expired_removed,
        "precision_at_1": top_1_correct,
        "ndcg_at_3": ndcg_at_3,
        "eligibility_violations_in_ranked": eligibility_violations,
        "deterministic_repeat_consistency": deterministic_identical,
        "ranked_order": [{"rank": r.rank, "id": r.opportunity_id, "score": r.final_score} for r in res1.ranked],
        "latency_ms": elapsed_ms,
    }
