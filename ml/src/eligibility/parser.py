"""Parse unstructured opportunity descriptions into candidate StructuredOpportunityRequirements."""

from __future__ import annotations

import re
from datetime import date

from ml.src.eligibility.schemas import RequirementEvidence, StructuredOpportunityRequirements
from ml.src.extraction.taxonomy import (
    BRANCH_ALIASES,
    DEGREE_ALIASES,
    deduplicate_skills,
    find_skills_with_evidence,
    normalize_branch,
    normalize_degree,
)


def parse_opportunity_requirements(
    opportunity_id: str,
    title: str,
    description: str,
    *,
    explicit_required_skills: list[str] | None = None,
    explicit_preferred_skills: list[str] | None = None,
    explicit_batches: list[int] | None = None,
    explicit_degrees: list[str] | None = None,
    explicit_min_cgpa: float | None = None,
    explicit_deadline: date | None = None,
) -> StructuredOpportunityRequirements:
    """
    Extract explicit requirements with source snippets from raw descriptions.
    Explicitly separates structured metadata from text-extracted prerequisites and flags
    ambiguous manual verification clauses instead of guessing.
    """
    evidence: list[RequirementEvidence] = []
    lines = [ln.strip() for ln in description.splitlines() if ln.strip()]

    degrees: list[str] = [d for d in (normalize_degree(x) for x in (explicit_degrees or [])) if d]
    branches: list[str] = []
    batches: list[int] = list(explicit_batches or [])
    acad_years: list[int] = []
    min_cgpa = explicit_min_cgpa
    max_backlogs: int | None = None
    min_exp_months: int | None = None
    citizenship: str | None = None
    ambiguous: list[str] = []

    if explicit_min_cgpa is not None:
        evidence.append(
            RequirementEvidence(
                field="min_cgpa",
                is_explicit=True,
                source_snippet=f"Structured posting metadata: min_cgpa={explicit_min_cgpa}",
            )
        )
    if explicit_batches:
        evidence.append(
            RequirementEvidence(
                field="eligible_graduation_years",
                is_explicit=True,
                source_snippet=f"Structured posting metadata: batches={explicit_batches}",
            )
        )

    for ln in lines:
        low = ln.lower()

        # Degrees in text
        for alias in sorted(DEGREE_ALIASES, key=len, reverse=True):
            if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low):
                d = normalize_degree(alias)
                if d and d not in degrees:
                    degrees.append(d)
                    evidence.append(RequirementEvidence(field="eligible_degrees", is_explicit=True, source_snippet=ln[:160]))

        # Branches in text
        for alias in sorted(BRANCH_ALIASES, key=len, reverse=True):
            if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low):
                br = normalize_branch(alias)
                if br and br not in branches:
                    branches.append(br)
                    evidence.append(RequirementEvidence(field="eligible_branches", is_explicit=True, source_snippet=ln[:160]))

        # Graduation batches in text (e.g., 2025/2026/2027)
        if re.search(r"\b(batch|graduating|graduation|class of|passout)\b", low):
            found_yrs = [int(y) for y in re.findall(r"\b(20[2-3]\d)\b", ln)]
            for y in found_yrs:
                if y not in batches:
                    batches.append(y)
            if found_yrs:
                evidence.append(
                    RequirementEvidence(field="eligible_graduation_years", is_explicit=True, source_snippet=ln[:160])
                )

        # Academic years (e.g., 1st year, 2nd year, 3rd year)
        for yr_tok, yr_num in [("1st year", 1), ("first year", 1), ("2nd year", 2), ("second year", 2), ("3rd year", 3), ("third year", 3), ("4th year", 4), ("final year", 4)]:
            if yr_tok in low and yr_num not in acad_years:
                acad_years.append(yr_num)
                evidence.append(RequirementEvidence(field="eligible_academic_years", is_explicit=True, source_snippet=ln[:160]))

        # Min CGPA
        if min_cgpa is None:
            m_cg = re.search(r"(?:min(?:imum)?\s*cgpa|cgpa\s*(?:>=|at least|of)?)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)", low)
            if m_cg:
                val = float(m_cg.group(1))
                if 0.0 <= val <= 10.0:
                    min_cgpa = val
                    evidence.append(RequirementEvidence(field="min_cgpa", is_explicit=True, source_snippet=ln[:160]))

        # Active backlogs policy
        if max_backlogs is None:
            if re.search(r"\bno\s+(?:active|standing|current)?\s*backlogs?\b|\b0\s*backlogs?\b", low):
                max_backlogs = 0
                evidence.append(RequirementEvidence(field="max_active_backlogs", is_explicit=True, source_snippet=ln[:160]))
            elif m_bl := re.search(r"(?:max|at\s*most|up\s*to)\s*(\d+)\s*backlogs?", low):
                max_backlogs = int(m_bl.group(1))
                evidence.append(RequirementEvidence(field="max_active_backlogs", is_explicit=True, source_snippet=ln[:160]))

        # Prior experience months
        if min_exp_months is None:
            if m_exp := re.search(r"(?:at\s*least|minimum)\s*(\d+)\s*(?:\+\s*)?(months?|years?)\s*(?:of\s*)?(?:experience|internship)", low):
                cnt = int(m_exp.group(1))
                min_exp_months = cnt * 12 if m_exp.group(2).startswith("year") else cnt
                evidence.append(RequirementEvidence(field="min_experience_months", is_explicit=True, source_snippet=ln[:160]))

        # Explicit legal citizenship clause (e.g., government/defense labs like DRDO/ISRO)
        if citizenship is None and re.search(r"\bindian\s+citizens?\s+only\b|\bcitizenship\s*:\s*indian\b", low):
            citizenship = "India"
            evidence.append(RequirementEvidence(field="required_citizenship", is_explicit=True, source_snippet=ln[:160]))

        # Flag vague subjective prerequisites that cannot be verified automatically
        if re.search(r"\b(subject to department chair approval|equivalent industry distinction|special institutional clearance)\b", low):
            ambiguous.append(ln[:160])
            evidence.append(RequirementEvidence(field="ambiguous_clauses", is_explicit=True, source_snippet=ln[:160]))

    # Distinguish required vs preferred skills
    req_skills = deduplicate_skills(explicit_required_skills or [])
    pref_skills = deduplicate_skills(explicit_preferred_skills or [])
    if not req_skills:
        skill_hits = find_skills_with_evidence(description)
        for cname, _, snip in skill_hits:
            low_snip = snip.lower()
            if "nice to have" in low_snip or "preferred" in low_snip or "bonus" in low_snip:
                if cname not in pref_skills:
                    pref_skills.append(cname)
            else:
                if cname not in req_skills:
                    req_skills.append(cname)
            evidence.append(RequirementEvidence(field="skills", is_explicit=True, source_snippet=snip))

    return StructuredOpportunityRequirements(
        opportunity_id=opportunity_id,
        title=title,
        eligible_degrees=degrees,
        eligible_branches=branches,
        eligible_graduation_years=sorted(set(batches)),
        eligible_academic_years=sorted(set(acad_years)),
        min_cgpa=min_cgpa,
        max_active_backlogs=max_backlogs,
        required_skills=req_skills,
        preferred_skills=[s for s in pref_skills if s not in set(req_skills)],
        min_experience_months=min_exp_months,
        required_citizenship=citizenship,
        deadline=explicit_deadline,
        ambiguous_clauses=ambiguous,
        evidence=evidence,
    )
