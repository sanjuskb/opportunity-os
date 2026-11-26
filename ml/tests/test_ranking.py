"""Unit tests for Workstream C: Transparent Opportunity Ranking & Supervised Readiness."""

from __future__ import annotations

from datetime import date

from ml.src.eligibility.schemas import EligibilityDecision
from ml.src.evaluation.ranking_eval import evaluate_ranking_benchmark
from ml.src.ranking.baseline_ranker import DeterministicOpportunityRanker
from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences
from ml.src.ranking.supervised_pipeline import check_supervised_training_readiness, extract_ranking_feature_vector


def test_ranking_benchmark_separation_dedup_expiry() -> None:
    ranker = DeterministicOpportunityRanker()
    metrics = evaluate_ranking_benchmark(ranker)
    assert metrics["duplicates_removed"] == 1
    assert metrics["expired_removed"] == 1
    assert metrics["eligibility_violations_in_ranked"] == 0
    assert metrics["precision_at_1"] == 1.0
    assert metrics["ndcg_at_3"] == 1.0
    assert metrics["deterministic_repeat_consistency"] is True


def test_missing_data_does_not_inflate_score() -> None:
    ranker = DeterministicOpportunityRanker()
    prefs = StudentRankingPreferences(student_id="s1", preferred_types=["internship"])
    elig = EligibilityDecision(opportunity_id="o", status="eligible", is_eligible=True, summary_reason="ok")

    transparent = CandidateOpportunity(
        opportunity_id="o-clear",
        title="Clear Intern",
        organization="Corp A",
        opportunity_type="internship",
        is_verified_source=True,
        has_compensation=True,
        monthly_compensation_inr=40000,
        deadline=date(2026, 12, 10),
        semantic_similarity=0.80,
        eligibility=elig.model_copy(update={"opportunity_id": "o-clear"}),
    )
    missing_info = CandidateOpportunity(
        opportunity_id="o-missing",
        title="Opaque Intern",
        organization="Corp B",
        opportunity_type="internship",
        is_verified_source=False,
        has_compensation=False,
        deadline=None,
        semantic_similarity=None,
        eligibility=elig.model_copy(update={"opportunity_id": "o-missing"}),
    )
    res = ranker.rank([missing_info, transparent], prefs, reference_date=date(2026, 11, 25))
    assert res.ranked[0].opportunity_id == "o-clear"
    assert res.ranked[0].final_score > res.ranked[1].final_score

    vec = extract_ranking_feature_vector(transparent, prefs, days_until_deadline=15)
    assert len(vec) == 8
    readiness = check_supervised_training_readiness(25)
    assert readiness["supervised_training_status"] == "pending_user_interaction_data"
