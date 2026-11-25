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
