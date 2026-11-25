"""Supervised ML ranking readiness: feature builder, label schema & minimum data guard."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences

MIN_LABELED_SESSIONS_FOR_GBDT = 500

RANKING_FEATURE_NAMES = [
    "is_eligible_flag",
    "semantic_similarity",
    "required_skill_match_ratio",
    "preferred_skill_match_ratio",
    "preference_fit_score",
    "deadline_urgency_norm",
    "is_verified_source",
    "has_transparent_compensation",
]


class InteractionTrainingRecord(BaseModel):
    """Canonical schema for real logged student interaction feedback (NEVER fabricate)."""

    session_id: str
    student_id: str
    opportunity_id: str
    label: Literal["relevant", "not_relevant", "clicked", "saved", "applied", "dismissed"]
    relevance_grade: int = Field(ge=0, le=3, description="0=dismissed/not_relevant, 1=clicked, 2=saved/relevant, 3=applied")
    features: list[float] = Field(min_length=len(RANKING_FEATURE_NAMES), max_length=len(RANKING_FEATURE_NAMES))


def extract_ranking_feature_vector(
    candidate: CandidateOpportunity,
    preferences: StudentRankingPreferences,
    *,
    days_until_deadline: int | None = None,
) -> list[float]:
    """Extract fixed-order numeric feature vector suitable for future LightGBM / XGBoost ranker."""
    req_tot = len(candidate.eligibility.matched_required_skills) + len(candidate.eligibility.missing_required_skills)
    req_ratio = len(candidate.eligibility.matched_required_skills) / req_tot if req_tot else 0.0

    pref_tot = len(candidate.eligibility.matched_preferred_skills) + len(candidate.eligibility.missing_preferred_skills)
    pref_ratio = len(candidate.eligibility.matched_preferred_skills) / pref_tot if pref_tot else 0.0

    loc_match = 1.0 if (
        (preferences.remote_preferred and candidate.is_remote)
        or any(p.lower() in candidate.location.lower() for p in preferences.preferred_locations)
    ) else 0.0

    urg = 0.0 if days_until_deadline is None or days_until_deadline < 0 else round(1.0 / (1.0 + days_until_deadline / 14.0), 4)
    return [
        1.0 if candidate.eligibility.is_eligible else 0.0,
        float(candidate.semantic_similarity or 0.0),
        round(req_ratio, 4),
        round(pref_ratio, 4),
        loc_match,
        urg,
        1.0 if candidate.is_verified_source else 0.0,
        1.0 if (candidate.monthly_compensation_inr or 0) > 0 or candidate.has_compensation else 0.0,
    ]


def check_supervised_training_readiness(num_sessions: int) -> dict[str, object]:
    """Report truthfully whether supervised LightGBM/XGBoost ranking is justified yet."""
    ready = num_sessions >= MIN_LABELED_SESSIONS_FOR_GBDT
    return {
        "supervised_training_status": "ready_for_experiment" if ready else "pending_user_interaction_data",
        "observed_labeled_sessions": num_sessions,
        "minimum_required_sessions": MIN_LABELED_SESSIONS_FOR_GBDT,
        "active_production_ranker": "deterministic-weighted-ranker-v1",
        "note": (
            "Sufficient interaction telemetry present for LambdaMART/LightGBM cross-validation."
            if ready
            else "Insufficient real student interaction data; deterministic rule-gated baseline remains active."
        ),
    }
