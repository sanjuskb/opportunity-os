"""Deterministic, explainable baseline opportunity ranker for NexteRaS."""

from __future__ import annotations

import math
from datetime import date

from ml.src.ranking.schemas import (
    CandidateOpportunity,
    ExcludedCandidate,
    RankedOpportunity,
    RankingResponse,
    ScoreContribution,
    StudentRankingPreferences,
)

# Transparent calibrated weights summing to 1.00 across explicit signals
RANKING_WEIGHTS: dict[str, float] = {
    "semantic_relevance": 0.35,
    "skill_alignment": 0.25,
    "preference_fit": 0.15,
    "deadline_urgency": 0.10,
    "source_verification": 0.10,
    "compensation_clarity": 0.05,
}


class DeterministicOpportunityRanker:
    """
    Orders candidate opportunities cleanly by separating:
      Stage 1: Deduplication & expiry/active status validation
      Stage 2: Hard deterministic eligibility gate
      Stage 3: Transparent multi-factor weighted scoring without missing-data inflation
      Stage 4: Deterministic tie-broken sorting
    """

    def rank(
        self,
        candidates: list[CandidateOpportunity],
        preferences: StudentRankingPreferences,
        *,
        reference_date: date | None = None,
    ) -> RankingResponse:
        today = reference_date or date.today()
        seen_ids: set[str] = set()
        seen_signatures: set[tuple[str, str, str]] = set()

        eligible_pool: list[CandidateOpportunity] = []
        excluded: list[ExcludedCandidate] = []
        dup_count = 0
        exp_count = 0

        for cand in candidates:
            sig = (
                " ".join(cand.title.lower().split()),
                " ".join(cand.organization.lower().split()),
                (cand.source_url or "").strip().lower(),
            )
            if cand.opportunity_id in seen_ids or (cand.source_url and sig in seen_signatures):
                dup_count += 1
                excluded.append(
                    ExcludedCandidate(
                        opportunity_id=cand.opportunity_id,
                        title=cand.title,
                        category="duplicate",
                        reason="Duplicate opportunity listing filtered out.",
                    )
                )
                continue
            seen_ids.add(cand.opportunity_id)
            if cand.source_url:
                seen_signatures.add(sig)

            if not cand.is_active:
                excluded.append(
                    ExcludedCandidate(
                        opportunity_id=cand.opportunity_id,
                        title=cand.title,
                        category="inactive",
                        reason="Opportunity is marked inactive.",
                    )
                )
                continue

            if cand.deadline is not None and today > cand.deadline:
                exp_count += 1
                excluded.append(
                    ExcludedCandidate(
                        opportunity_id=cand.opportunity_id,
                        title=cand.title,
                        category="expired",
                        reason=f"Deadline {cand.deadline.isoformat()} expired relative to {today.isoformat()}.",
                    )
                )
                continue

            if not cand.eligibility.is_eligible:
                cat = cand.eligibility.status
                excluded.append(
                    ExcludedCandidate(
                        opportunity_id=cand.opportunity_id,
                        title=cand.title,
                        category=cat,  # type: ignore[arg-type]
                        reason=cand.eligibility.summary_reason,
                    )
                )
                continue

            eligible_pool.append(cand)

        scored_items: list[tuple[float, date, str, RankedOpportunity]] = []
        for cand in eligible_pool:
            contribs = self._score_candidate(cand, preferences, today)
            total_pts = round(sum(c.weighted_points for c in contribs), 2)
            # Sort key: highest score -> earliest known deadline (missing deadlines last) -> id
            sort_deadline = cand.deadline or date(2099, 12, 31)
            top_driver = max(contribs, key=lambda c: c.weighted_points)
            explanation = (
                f"Ranked at {total_pts:.1f}/100 (eligible). Primary driver: {top_driver.factor} — {top_driver.explanation}"
            )
            scored_items.append(
                (
                    -total_pts,
                    sort_deadline,
                    cand.opportunity_id,
                    RankedOpportunity(
                        rank=1,  # updated after sort
                        opportunity_id=cand.opportunity_id,
                        title=cand.title,
                        organization=cand.organization,
                        final_score=total_pts,
                        eligibility_status=cand.eligibility.status,
                        contributions=contribs,
                        ranking_explanation=explanation,
                    ),
                )
            )

        scored_items.sort(key=lambda row: (row[0], row[1], row[2]))
        ranked: list[RankedOpportunity] = []
        for pos, (_, _, _, item) in enumerate(scored_items, start=1):
            ranked.append(item.model_copy(update={"rank": pos}))

        return RankingResponse(
            ranked=ranked,
            excluded=excluded,
            total_input=len(candidates),
            duplicates_removed=dup_count,
            expired_removed=exp_count,
        )

    @staticmethod
    def _score_candidate(
        cand: CandidateOpportunity,
        prefs: StudentRankingPreferences,
        today: date,
    ) -> list[ScoreContribution]:
        # 1. Semantic relevance (missing score contributes 0.0 - never inflated)
        raw_sim = 0.0 if cand.semantic_similarity is None else max(0.0, min(1.0, (cand.semantic_similarity + 1.0) / 2.0 if cand.semantic_similarity < 0 else cand.semantic_similarity))
        sem_note = (
            f"Semantic similarity {cand.semantic_similarity:.3f}"
            if cand.semantic_similarity is not None
            else "Semantic similarity unavailable (0.0 assigned)"
        )

        # 2. Skill alignment (required 75% weight + preferred 25% bonus if present)
        req_total = len(cand.eligibility.matched_required_skills) + len(cand.eligibility.missing_required_skills)
        req_ratio = (len(cand.eligibility.matched_required_skills) / req_total) if req_total > 0 else 0.5
        pref_total = len(cand.eligibility.matched_preferred_skills) + len(cand.eligibility.missing_preferred_skills)
        pref_ratio = (len(cand.eligibility.matched_preferred_skills) / pref_total) if pref_total > 0 else 0.0
        raw_skill = round(min(1.0, 0.8 * req_ratio + 0.2 * pref_ratio) if pref_total > 0 else req_ratio, 4)
        skill_note = f"{len(cand.eligibility.matched_required_skills)}/{req_total} required skills matched"

        # 3. Preferences: location/remote + type + interest
        pref_parts: list[float] = []
        pref_reasons: list[str] = []
        if prefs.preferred_types:
            t_hit = 1.0 if cand.opportunity_type.lower() in {t.lower() for t in prefs.preferred_types} else 0.0
            pref_parts.append(t_hit)
            if t_hit:
                pref_reasons.append(f"matches type '{cand.opportunity_type}'")
        if prefs.preferred_locations or prefs.remote_preferred:
            loc_low = cand.location.lower()
            loc_hit = 1.0 if (
                (prefs.remote_preferred and cand.is_remote)
                or any(p.lower() in loc_low for p in prefs.preferred_locations)
            ) else 0.0
            pref_parts.append(loc_hit)
            if loc_hit:
                pref_reasons.append("matches location/remote preference")
        if cand.interest_overlap_score is not None:
            pref_parts.append(cand.interest_overlap_score)
        raw_pref = round(sum(pref_parts) / len(pref_parts), 4) if pref_parts else 0.0

        # 4. Deadline urgency (only active future deadlines get exponential score; missing gets 0.0)
        if cand.deadline is not None and cand.deadline >= today:
            days_left = (cand.deadline - today).days
            raw_urgency = round(math.exp(-days_left / 21.0), 4)
            urg_note = f"{days_left} days until deadline"
        else:
            raw_urgency = 0.0
            urg_note = "Deadline missing (0.0 urgency points)"

        # 5. Verified official source check
        raw_verif = 1.0 if cand.is_verified_source else 0.25
        verif_note = "Official/verified source provenance" if cand.is_verified_source else "Unverified third-party source"

        # 6. Compensation transparency & threshold fit (missing stipend gets 0.0, never rewarded)
        if cand.monthly_compensation_inr is not None and cand.monthly_compensation_inr > 0:
            if prefs.min_compensation_inr and cand.monthly_compensation_inr < prefs.min_compensation_inr:
                raw_comp = 0.25
                comp_note = f"INR {cand.monthly_compensation_inr}/mo below preferred INR {prefs.min_compensation_inr}"
            else:
                raw_comp = 1.0
                comp_note = f"Transparent compensation (INR {cand.monthly_compensation_inr}/mo)"
        elif cand.has_compensation:
            raw_comp = 0.6
            comp_note = "Paid compensation disclosed"
        else:
            raw_comp = 0.0
            comp_note = "Compensation undisclosed (0.0 assigned)"

        entries = [
            ("semantic_relevance", raw_sim, sem_note),
            ("skill_alignment", raw_skill, skill_note),
            ("preference_fit", raw_pref, ", ".join(pref_reasons) or "No explicit preference match"),
            ("deadline_urgency", raw_urgency, urg_note),
            ("source_verification", raw_verif, verif_note),
            ("compensation_clarity", raw_comp, comp_note),
        ]

        return [
            ScoreContribution(
                factor=name,
                weight=RANKING_WEIGHTS[name],
                raw_score=raw_val,
                weighted_points=round(RANKING_WEIGHTS[name] * raw_val * 100.0, 2),
                explanation=note,
            )
            for name, raw_val, note in entries
        ]
