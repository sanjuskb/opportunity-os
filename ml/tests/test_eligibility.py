"""Unit tests for Workstream D: Deterministic Eligibility Engine & JD Parser."""

from __future__ import annotations

from datetime import date

from ml.src.eligibility.engine import DeterministicEligibilityEngine
from ml.src.eligibility.parser import parse_opportunity_requirements
from ml.src.eligibility.schemas import StructuredOpportunityRequirements, StudentEligibilityInput
from ml.src.evaluation.eligibility_eval import evaluate_eligibility_benchmark


def test_eligibility_edge_cases_benchmark() -> None:
    engine = DeterministicEligibilityEngine()
    metrics = evaluate_eligibility_benchmark(engine)
    assert metrics["cases_evaluated"] == 8
    assert metrics["exact_outcome_accuracy"] == 1.0
    assert metrics["false_eligible_rate"] == 0.0
    assert metrics["false_ineligible_rate"] == 0.0
    assert metrics["unknown_and_unverified_handling_rate"] == 1.0
    assert metrics["explanation_traceability_rate"] == 1.0


def test_jd_parser_distinguishes_required_vs_preferred_and_flags_backlogs() -> None:
    jd = """
    Eligibility: Open for B.Tech / B.E. students in CSE or IT graduating batch 2026.
    Minimum CGPA 7.5 and no active backlogs allowed.
    Required: Python, FastAPI, PostgreSQL.
    Preferred (nice to have): Docker, Redis.
    """
    parsed = parse_opportunity_requirements(
        "opp-jd-1",
        "Backend Intern",
        jd,
        explicit_deadline=date(2026, 12, 31),
    )
    assert "B.Tech" in parsed.eligible_degrees
    assert parsed.min_cgpa == 7.5
    assert parsed.max_active_backlogs == 0
    assert 2026 in parsed.eligible_graduation_years
    assert "Python" in parsed.required_skills
    assert "Docker" in parsed.preferred_skills

    engine = DeterministicEligibilityEngine()
    stu_good = StudentEligibilityInput(
        student_id="st-ok",
        degree="B.E.",
        branch="Computer Science",
        graduation_year=2026,
        cgpa=8.1,
        active_backlogs=0,
        skills=["Python", "FastAPI", "PostgreSQL"],
    )
    dec_good = engine.evaluate(stu_good, parsed, reference_date=date(2026, 11, 25))
    assert dec_good.is_eligible is True
    assert dec_good.missing_preferred_skills == ["Docker", "Redis"]

    # Missing backlog field cannot be assumed 0!
    stu_unknown_backlog = stu_good.model_copy(update={"active_backlogs": None})
    dec_unk = engine.evaluate(stu_unknown_backlog, parsed, reference_date=date(2026, 11, 25))
    assert dec_unk.status == "needs_more_info"
    assert dec_unk.is_eligible is False


def test_first_year_study_restriction() -> None:
    reqs = StructuredOpportunityRequirements(
        opportunity_id="opp-1st",
        title="STEP Style Early Undergrad Intern",
        eligible_academic_years=[1, 2],
        required_skills=["Python"],
    )
    eng = DeterministicEligibilityEngine()
    second_yr = StudentEligibilityInput(student_id="s1", current_academic_year=2, skills=["Python"])
    fourth_yr = StudentEligibilityInput(student_id="s2", current_academic_year=4, skills=["Python"])
    assert eng.evaluate(second_yr, reqs).is_eligible is True
    assert eng.evaluate(fourth_yr, reqs).status == "ineligible"


def test_location_restrictions_and_experience_and_missing_fields() -> None:
    eng = DeterministicEligibilityEngine()
    jd = """
    Location: Bangalore (On-site only)
    Eligibility: Open for B.Tech students batch 2026 with minimum 6 months of internship experience.
    Minimum CGPA 7.0. Required: Python, SQL.
    """
    reqs = parse_opportunity_requirements("opp-loc-1", "On-Site Backend Intern", jd)
    assert "Bengaluru" in reqs.allowed_locations
    assert reqs.remote_allowed is False
    assert reqs.min_experience_months == 6

    base_stu = StudentEligibilityInput(
        student_id="st-loc",
        degree="B.Tech",
        graduation_year=2026,
        cgpa=8.0,
        experience_months=6,
        skills=["Python", "SQL"],
    )

    # Matching city alias (Bangalore <-> Bengaluru) -> eligible
    same_city = base_stu.model_copy(update={"preferred_locations": ["Bangalore"], "open_to_relocate": False})
    assert eng.evaluate(same_city, reqs).is_eligible is True

    # Different city + NOT open to relocate -> ineligible
    no_reloc = base_stu.model_copy(update={"preferred_locations": ["Hyderabad"], "open_to_relocate": False})
    dec_reject = eng.evaluate(no_reloc, reqs)
    assert dec_reject.status == "ineligible"
    assert any("location" in a.requirement.lower() for a in dec_reject.audit_trail)

    # Different city + open to relocate -> eligible
    yes_reloc = base_stu.model_copy(update={"preferred_locations": ["Hyderabad"], "open_to_relocate": True})
    assert eng.evaluate(yes_reloc, reqs).is_eligible is True

    # Unknown location and relocation flag -> needs_more_info (never assumed eligible)
    unk_loc = base_stu.model_copy(update={"preferred_locations": [], "open_to_relocate": None})
    assert eng.evaluate(unk_loc, reqs).status == "needs_more_info"

    # Insufficient experience -> ineligible
    low_exp = yes_reloc.model_copy(update={"experience_months": 2})
    assert eng.evaluate(low_exp, reqs).status == "ineligible"

    # Branch restriction mismatch -> ineligible
    reqs_br = reqs.model_copy(update={"eligible_branches": ["CSE"], "allowed_locations": []})
    mech_stu = yes_reloc.model_copy(update={"branch": "Mechanical Engineering"})
    assert eng.evaluate(mech_stu, reqs_br).status == "ineligible"
