"""Live PostgreSQL-backed Deterministic + Vector Eligibility Evaluation Service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.models.entities import (
    CareerPassport,
    Opportunity,
    OpportunityEligibility,
    OpportunityEmbedding,
    Resume,
    StudentEmbedding,
    StudentProfile,
)
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.opportunities import OpportunityRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    DeterministicChecksSummary,
    EligibilityCheckResponse,
    SkillOverlapSummary,
)

_DEGREE_ALIASES: dict[str, set[str]] = {
    "b.tech": {
        "b.tech",
        "btech",
        "bachelor of technology",
        "b.e.",
        "be",
        "bachelor of engineering",
    },
    "b.e.": {"b.tech", "btech", "bachelor of technology", "b.e.", "be", "bachelor of engineering"},
    "m.tech": {"m.tech", "mtech", "master of technology", "m.e.", "me", "dual degree"},
    "bca": {"bca", "bachelor of computer applications"},
    "mca": {"mca", "master of computer applications"},
    "bsc": {"bsc", "b.sc", "bachelor of science"},
    "msc": {"msc", "m.sc", "master of science"},
    "mba": {"mba", "pgdm", "master of business administration"},
}

_BRANCH_ALIASES: dict[str, str] = {
    "cse": "computer science",
    "cs": "computer science",
    "computer science": "computer science",
    "computer science and engineering": "computer science",
    "computer science & engineering": "computer science",
    "it": "information technology",
    "information technology": "information technology",
    "ece": "electronics and communication",
    "electronics": "electronics and communication",
    "eee": "electrical engineering",
    "ee": "electrical engineering",
    "ai": "ai & data science",
    "aids": "ai & data science",
    "ai & ds": "ai & data science",
    "data science": "ai & data science",
}

_LOCATION_ALIASES: dict[str, str] = {
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "bombay": "mumbai",
    "mumbai": "mumbai",
    "gurgaon": "gurugram",
    "gurugram": "gurugram",
    "madras": "chennai",
    "chennai": "chennai",
}


def _norm_degree(raw: str | None) -> str:
    val = (raw or "").strip().lower()
    for canon, aliases in _DEGREE_ALIASES.items():
        if val in aliases or val == canon:
            return canon
    return val


def _norm_branch(raw: str | None) -> str:
    val = (raw or "").strip().lower()
    return _BRANCH_ALIASES.get(val, val)


def _norm_loc(raw: str | None) -> str:
    val = (raw or "").strip().lower().split(",")[0].strip()
    return _LOCATION_ALIASES.get(val, val)


def _cosine_similarity(vec_a: list[float] | None, vec_b: list[float] | None) -> float | None:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return None
    dot = sum(float(a) * float(b) for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = sum(float(a) * float(a) for a in vec_a) ** 0.5
    norm_b = sum(float(b) * float(b) for b in vec_b) ** 0.5
    if norm_a <= 0 or norm_b <= 0:
        return None
    return float(max(0.0, min(1.0, dot / float(norm_a * norm_b))))


def _aggregate_student_skills(
    student: StudentProfile | None,
    passport: CareerPassport | None,
    resumes: list[Resume],
) -> list[str]:
    seen: dict[str, str] = {}

    def _add(skill: str) -> None:
        clean = skill.strip()
        if clean and clean.lower() not in seen:
            seen[clean.lower()] = clean

    if student and student.skills:
        for s in student.skills:
            _add(str(s))

    for res in resumes:
        mc = res.master_content or {}
        for key in ("normalized_skills", "skills"):
            val = mc.get(key)
            if isinstance(val, list):
                for s in val:
                    _add(str(s))

    if passport:
        for bucket in (passport.projects, passport.certifications, passport.coursework):
            if isinstance(bucket, list):
                for item in bucket:
                    if isinstance(item, dict):
                        skills_val = item.get("skills")
                        if isinstance(skills_val, list):
                            for s in skills_val:
                                _add(str(s))
    return list(seen.values())


class EligibilityService:
    """Combines live Postgres academic/passport data, deterministic rules, and vector similarity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._opp_repo = OpportunityRepository(session)
        self._student_repo = StudentProfileRepository(session)
        self._passport_repo = CareerPassportRepository(session)
        self._resume_repo = ResumeRepository(session)

    async def evaluate(self, user_id: UUID, opportunity_id: UUID) -> EligibilityCheckResponse:
        opp = await self._opp_repo.get_by_id(opportunity_id)
        if opp is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Opportunity Not Found",
                detail="Requested opportunity does not exist.",
            )

        student = await self._student_repo.get_by_user_id(user_id)
        passport = await self._passport_repo.get_by_user_id(user_id)
        resumes = await self._resume_repo.list_for_user(user_id, limit=3)

        stu_emb = (
            await self._session.execute(
                select(StudentEmbedding.embedding_minilm_384).where(
                    StudentEmbedding.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        opp_emb = (
            await self._session.execute(
                select(OpportunityEmbedding.embedding_minilm_384).where(
                    OpportunityEmbedding.opportunity_id == opportunity_id,
                    OpportunityEmbedding.embedding_status == "ready",
                )
            )
        ).scalar_one_or_none()
        semantic_sim = _cosine_similarity(
            list(stu_emb) if stu_emb is not None else None,
            list(opp_emb) if opp_emb is not None else None,
        )

        return self.evaluate_loaded(
            user_id=user_id,
            opportunity=opp,
            student=student,
            passport=passport,
            resumes=resumes,
            semantic_similarity=semantic_sim,
        )

    @staticmethod
    def evaluate_loaded(
        *,
        user_id: UUID,
        opportunity: Opportunity,
        student: StudentProfile | None,
        passport: CareerPassport | None,
        resumes: list[Resume],
        semantic_similarity: float | None = None,
    ) -> EligibilityCheckResponse:
        elig: OpportunityEligibility | None = opportunity.eligibility
        reasons: list[str] = []
        failed = False
        missing_info = False

        # 1. Active & deadline check
        deadline_active = bool(opportunity.is_active if opportunity.is_active is not None else True)
        if not deadline_active:
            failed = True
            reasons.append("Opportunity listing is currently inactive.")
        elif opportunity.deadline is not None:
            now_utc = datetime.now(UTC)
            dl = (
                opportunity.deadline
                if opportunity.deadline.tzinfo
                else opportunity.deadline.replace(tzinfo=UTC)
            )
            if now_utc > dl:
                deadline_active = False
                failed = True
                reasons.append(f"Application deadline ({dl.date().isoformat()}) has passed.")

        # 2. Student profile availability
        student_skills = _aggregate_student_skills(student, passport, resumes)
        owned_lower = {s.lower() for s in student_skills}

        batch_matched = True
        degree_matched = True
        cgpa_matched = True
        backlogs_matched = True
        location_matched = True

        if student is None:
            missing_info = True
            reasons.append(
                "Student academic profile is not yet complete; deterministic degree/CGPA checks require onboarding data."
            )
            if elig and (
                elig.eligible_batches or elig.eligible_degrees or elig.min_cgpa is not None
            ):
                batch_matched = not bool(elig.eligible_batches)
                degree_matched = not bool(elig.eligible_degrees)
                cgpa_matched = elig.min_cgpa is None
        elif elig is not None:
            # Degree check
            if elig.eligible_degrees:
                allowed_deg = {_norm_degree(d) for d in elig.eligible_degrees}
                stu_deg = _norm_degree(student.degree)
                if not stu_deg:
                    missing_info = True
                    degree_matched = False
                    reasons.append("Student degree is missing.")
                elif stu_deg not in allowed_deg:
                    failed = True
                    degree_matched = False
                    reasons.append(
                        f"Degree '{student.degree}' is not in eligible degrees ({', '.join(elig.eligible_degrees)})."
                    )
                else:
                    reasons.append(f"Degree '{student.degree}' matches requirement.")

            # Branch check
            if elig.eligible_branches:
                allowed_br = {_norm_branch(b) for b in elig.eligible_branches}
                stu_br = _norm_branch(student.branch)
                if stu_br and stu_br not in allowed_br:
                    failed = True
                    reasons.append(
                        f"Branch '{student.branch}' is outside listed branches ({', '.join(elig.eligible_branches)})."
                    )

            # Graduation batch check
            if elig.eligible_batches:
                if student.graduation_year not in elig.eligible_batches:
                    failed = True
                    batch_matched = False
                    reasons.append(
                        f"Graduation batch {student.graduation_year} is outside eligible batches {list(elig.eligible_batches)}."
                    )
                else:
                    reasons.append(f"Graduation batch {student.graduation_year} is eligible.")

            # Academic year check
            if (
                elig.eligible_academic_years
                and student.current_academic_year is not None
                and student.current_academic_year not in elig.eligible_academic_years
            ):
                failed = True
                reasons.append(
                    f"Academic year {student.current_academic_year} is outside {list(elig.eligible_academic_years)}."
                )

            # CGPA check
            if elig.min_cgpa is not None:
                if student.cgpa is None:
                    missing_info = True
                    cgpa_matched = False
                    reasons.append(f"Minimum CGPA {elig.min_cgpa} required; student CGPA not set.")
                elif float(student.cgpa) < float(elig.min_cgpa):
                    failed = True
                    cgpa_matched = False
                    reasons.append(f"CGPA {student.cgpa} is below minimum {elig.min_cgpa}.")
                else:
                    reasons.append(f"CGPA {student.cgpa} meets minimum {elig.min_cgpa}.")

            # Backlogs check
            if elig.max_active_backlogs is not None:
                backlogs = student.active_backlogs if student.active_backlogs is not None else 0
                if backlogs > elig.max_active_backlogs:
                    failed = True
                    backlogs_matched = False
                    reasons.append(
                        f"Active backlogs ({backlogs}) exceed maximum allowed ({elig.max_active_backlogs})."
                    )

            # Experience check
            if elig.min_experience_months and elig.min_experience_months > 0:
                exp = student.experience_months if student.experience_months is not None else 0
                if exp < elig.min_experience_months:
                    failed = True
                    reasons.append(
                        f"Experience ({exp} mo) is below minimum ({elig.min_experience_months} mo)."
                    )

            # Citizenship check
            if elig.required_citizenship:
                if not student.citizenship:
                    missing_info = True
                    reasons.append(
                        f"Citizenship '{elig.required_citizenship}' specified; student citizenship not set."
                    )
                elif (
                    student.citizenship.strip().lower() != elig.required_citizenship.strip().lower()
                ):
                    failed = True
                    reasons.append(
                        f"Citizenship '{student.citizenship}' does not match '{elig.required_citizenship}'."
                    )

            # Location / Remote / Relocation check
            if elig.allowed_locations and not bool(elig.remote_allowed):
                allowed_locs = {_norm_loc(loc) for loc in elig.allowed_locations}
                stu_locs = {_norm_loc(loc) for loc in (student.preferred_locations or [])}
                if student.state:
                    stu_locs.add(_norm_loc(student.state))
                reloc = True if student.open_to_relocate is None else bool(student.open_to_relocate)
                if not reloc and stu_locs and not (allowed_locs & stu_locs):
                    failed = True
                    location_matched = False
                    reasons.append(
                        f"Role requires on-site presence in {', '.join(elig.allowed_locations)} without relocation."
                    )

        # 3. Skill overlap (required + preferred)
        req_skills = list(elig.required_skills or []) if elig else []
        pref_skills = list(elig.preferred_skills or []) if elig else []
        matched_req = [s for s in req_skills if s.lower() in owned_lower]
        missing_req = [s for s in req_skills if s.lower() not in owned_lower]
        matched_pref = [s for s in pref_skills if s.lower() in owned_lower]

        if req_skills:
            if missing_req:
                reasons.append(f"Missing required skills: {', '.join(missing_req)}.")
            else:
                reasons.append("All listed required skills are present in your profile/resume.")

        status_val: Literal["eligible", "ineligible", "needs_more_info"]
        if failed:
            status_val = "ineligible"
            is_eligible = False
        elif missing_info:
            status_val = "needs_more_info"
            is_eligible = False
        else:
            status_val = "eligible"
            is_eligible = True

        # 4. Transparent composite score (0-100)
        rule_base = 55.0 if is_eligible else (30.0 if missing_info and not failed else 10.0)
        skill_ratio = len(matched_req) / len(req_skills) if req_skills else 1.0
        pref_ratio = len(matched_pref) / len(pref_skills) if pref_skills else 0.5
        sem_component = (semantic_similarity * 15.0) if semantic_similarity is not None else 7.5
        score = round(
            min(100.0, rule_base + skill_ratio * 25.0 + pref_ratio * 5.0 + sem_component), 2
        )

        explanation = (
            " ".join(reasons) if reasons else "All checked eligibility requirements satisfied."
        )

        return EligibilityCheckResponse(
            opportunity_id=str(opportunity.id),
            student_id=str(user_id),
            is_eligible=is_eligible,
            status=status_val,
            score=score,
            reasons=reasons,
            missing_skills=missing_req,
            explanation=explanation,
            semantic_similarity=round(semantic_similarity, 4)
            if semantic_similarity is not None
            else None,
            deterministic_checks=DeterministicChecksSummary(
                batch_matched=batch_matched,
                degree_matched=degree_matched,
                cgpa_matched=cgpa_matched,
                backlogs_matched=backlogs_matched,
                location_matched=location_matched,
                deadline_active=deadline_active,
            ),
            skill_overlap=SkillOverlapSummary(
                matched_skills=matched_req,
                missing_skills=missing_req,
                preferred_matched=matched_pref,
            ),
        )
