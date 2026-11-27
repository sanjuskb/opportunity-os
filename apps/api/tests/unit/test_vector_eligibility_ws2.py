"""WS2 unit tests for deterministic EligibilityService & hybrid ranking explainability."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.entities import (
    CareerPassport,
    Opportunity,
    OpportunityEligibility,
    Resume,
    StudentProfile,
)
from app.services.eligibility import EligibilityService


def test_eligibility_evaluates_degree_equivalence_cgpa_backlogs_and_skills() -> None:
    uid = uuid4()
    opp_id = uuid4()
    opp = Opportunity(
        id=opp_id,
        title="Backend Platform Intern",
        organization="NexteRaS Labs",
        location="Bengaluru",
        type="internship",
        description="Build FastAPI + PostgreSQL services",
        source_url="https://example.com/backend",
        source_provider="manual",
        is_active=True,
        deadline=datetime.now(UTC) + timedelta(days=10),
        eligibility=OpportunityEligibility(
            opportunity_id=opp_id,
            eligible_batches=[2026, 2027],
            eligible_degrees=["B.Tech"],
            eligible_branches=["Computer Science"],
            min_cgpa=Decimal("7.50"),
            max_active_backlogs=0,
            required_skills=["Python", "FastAPI", "PostgreSQL"],
            preferred_skills=["Docker"],
            allowed_locations=["Bangalore"],
            remote_allowed=False,
        ),
    )
    student = StudentProfile(
        id=uuid4(),
        user_id=uid,
        college_name="RVCE Bengaluru",
        degree="B.E.",  # Must match B.Tech via equivalence
        branch="CSE",  # Must match Computer Science via normalization
        graduation_year=2027,
        cgpa=Decimal("8.40"),
        state="Karnataka",
        active_backlogs=0,
        skills=["Python"],
        preferred_locations=["Bengaluru"],
        open_to_relocate=False,
    )
    passport = CareerPassport(
        id=uuid4(),
        student_id=student.id,
        projects=[{"title": "Queue API", "skills": ["FastAPI", "Docker"]}],
        certifications=[],
        coursework=[],
        verified_achievements=[],
    )
    resume = Resume(
        id=uuid4(),
        user_id=uid,
        title="Resume",
        master_content={"normalized_skills": ["PostgreSQL"]},
    )

    res = EligibilityService.evaluate_loaded(
        user_id=uid,
        opportunity=opp,
        student=student,
        passport=passport,
        resumes=[resume],
        semantic_similarity=0.88,
    )
    assert res.is_eligible is True
    assert res.status == "eligible"
    assert res.score > 80.0
    assert set(res.skill_overlap.matched_skills) == {"Python", "FastAPI", "PostgreSQL"}
    assert res.skill_overlap.missing_skills == []
    assert res.deterministic_checks.degree_matched is True
    assert res.deterministic_checks.cgpa_matched is True

    # Student with active backlogs > max_active_backlogs is deterministically ineligible
    student.active_backlogs = 1
    bad = EligibilityService.evaluate_loaded(
        user_id=uid,
        opportunity=opp,
        student=student,
        passport=passport,
        resumes=[resume],
        semantic_similarity=0.88,
    )
    assert bad.is_eligible is False
    assert bad.status == "ineligible"
    assert bad.deterministic_checks.backlogs_matched is False
