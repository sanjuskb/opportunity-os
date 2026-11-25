"""Strict deterministic eligibility evaluator with traceable explanations."""

from __future__ import annotations

from datetime import date

from ml.src.eligibility.schemas import (
    EligibilityDecision,
    EligibilityOutcome,
    RuleAuditItem,
    StructuredOpportunityRequirements,
    StudentEligibilityInput,
)
from ml.src.extraction.taxonomy import (
    EQUIVALENT_DEGREES,
    deduplicate_skills,
    normalize_branch,
    normalize_degree,
    normalize_location,
)


class DeterministicEligibilityEngine:
    """
    Evaluates student eligibility purely deterministically against structured rules.
    Never guesses or marks missing student fields as satisfied.
    """

    def evaluate(
        self,
        student: StudentEligibilityInput,
        requirements: StructuredOpportunityRequirements,
        *,
        reference_date: date | None = None,
    ) -> EligibilityDecision:
        today = reference_date or date.today()
        audit: list[RuleAuditItem] = []

        def _evidence_for(field: str, default: str) -> str:
            for ev in requirements.evidence:
                if ev.field == field:
                    return ev.source_snippet
            return default

        # 1. Opportunity Deadline
        if requirements.deadline is not None:
            if today > requirements.deadline:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Deadline on or before {requirements.deadline.isoformat()}",
                        student_value=today.isoformat(),
                        comparison_result="fail",
                        evidence_source=_evidence_for("deadline", f"Posting deadline: {requirements.deadline.isoformat()}"),
                        reason=f"Opportunity deadline ({requirements.deadline.isoformat()}) has already passed.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Deadline on or before {requirements.deadline.isoformat()}",
                        student_value=today.isoformat(),
                        comparison_result="pass",
                        evidence_source=_evidence_for("deadline", f"Posting deadline: {requirements.deadline.isoformat()}"),
                        reason="Application window is still active.",
                    )
                )

        # 2. Degree Requirement (with explicit B.Tech / B.E. / Dual Degree equivalence)
        if requirements.eligible_degrees:
            allowed_norm = {d.lower() for d in (normalize_degree(x) or x for x in requirements.eligible_degrees)}
            stu_deg = normalize_degree(student.degree)
            if stu_deg is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible degrees: {', '.join(requirements.eligible_degrees)}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("eligible_degrees", f"Degrees: {requirements.eligible_degrees}"),
                        reason="Student degree is missing; cannot verify degree constraint.",
                    )
                )
            else:
                stu_equiv = EQUIVALENT_DEGREES.get(stu_deg.lower(), {stu_deg.lower()})
                if allowed_norm & stu_equiv:
                    audit.append(
                        RuleAuditItem(
                            requirement=f"Eligible degrees: {', '.join(requirements.eligible_degrees)}",
                            student_value=stu_deg,
                            comparison_result="pass",
                            evidence_source=_evidence_for("eligible_degrees", f"Degrees: {requirements.eligible_degrees}"),
                            reason=f"Student degree '{stu_deg}' matches required degree set.",
                        )
                    )
                else:
                    audit.append(
                        RuleAuditItem(
                            requirement=f"Eligible degrees: {', '.join(requirements.eligible_degrees)}",
                            student_value=stu_deg,
                            comparison_result="fail",
                            evidence_source=_evidence_for("eligible_degrees", f"Degrees: {requirements.eligible_degrees}"),
                            reason=f"Degree '{stu_deg}' is outside eligible list ({', '.join(requirements.eligible_degrees)}).",
                        )
                    )

        # 3. Branch Requirement
        if requirements.eligible_branches:
            allowed_br = {normalize_branch(b) or b for b in requirements.eligible_branches}
            stu_br = normalize_branch(student.branch)
            if stu_br is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible branches: {', '.join(requirements.eligible_branches)}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("eligible_branches", f"Branches: {requirements.eligible_branches}"),
                        reason="Student branch/specialization is missing.",
                    )
                )
            elif stu_br in allowed_br:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible branches: {', '.join(requirements.eligible_branches)}",
                        student_value=stu_br,
                        comparison_result="pass",
                        evidence_source=_evidence_for("eligible_branches", f"Branches: {requirements.eligible_branches}"),
                        reason=f"Branch '{stu_br}' is eligible.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible branches: {', '.join(requirements.eligible_branches)}",
                        student_value=stu_br,
                        comparison_result="fail",
                        evidence_source=_evidence_for("eligible_branches", f"Branches: {requirements.eligible_branches}"),
                        reason=f"Branch '{stu_br}' is not in eligible branches.",
                    )
                )

        # 4. Graduation Year / Batch
        if requirements.eligible_graduation_years:
            batches_str = ", ".join(str(y) for y in requirements.eligible_graduation_years)
            if student.graduation_year is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible batches: {batches_str}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("eligible_graduation_years", f"Batches: {batches_str}"),
                        reason="Graduation year missing from student profile.",
                    )
                )
            elif student.graduation_year in requirements.eligible_graduation_years:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible batches: {batches_str}",
                        student_value=str(student.graduation_year),
                        comparison_result="pass",
                        evidence_source=_evidence_for("eligible_graduation_years", f"Batches: {batches_str}"),
                        reason=f"Graduation year {student.graduation_year} matches eligible batches.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Eligible batches: {batches_str}",
                        student_value=str(student.graduation_year),
                        comparison_result="fail",
                        evidence_source=_evidence_for("eligible_graduation_years", f"Batches: {batches_str}"),
                        reason=f"Graduation year {student.graduation_year} does not match eligible batches ({batches_str}).",
                    )
                )

        # 5. Current Academic Year (e.g. 1st/2nd year restriction)
        if requirements.eligible_academic_years:
            yrs_str = ", ".join(str(y) for y in requirements.eligible_academic_years)
            if student.current_academic_year is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Academic study year in [{yrs_str}]",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("eligible_academic_years", f"Academic years: {yrs_str}"),
                        reason="Current year of study is missing.",
                    )
                )
            elif student.current_academic_year in requirements.eligible_academic_years:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Academic study year in [{yrs_str}]",
                        student_value=str(student.current_academic_year),
                        comparison_result="pass",
                        evidence_source=_evidence_for("eligible_academic_years", f"Academic years: {yrs_str}"),
                        reason=f"Academic year {student.current_academic_year} is allowed.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Academic study year in [{yrs_str}]",
                        student_value=str(student.current_academic_year),
                        comparison_result="fail",
                        evidence_source=_evidence_for("eligible_academic_years", f"Academic years: {yrs_str}"),
                        reason=f"Academic year {student.current_academic_year} is outside eligible study years ({yrs_str}).",
                    )
                )

        # 6. Minimum CGPA (transparent normalization if student provided percentage only)
        if requirements.min_cgpa is not None:
            effective_cgpa = student.cgpa
            cgpa_note = str(student.cgpa) if student.cgpa is not None else None
            if effective_cgpa is None and student.percentage is not None:
                # Documented standard Indian AICTE approximation (percentage / 10) flagged transparently
                effective_cgpa = round(student.percentage / 10.0, 2)
                cgpa_note = f"{effective_cgpa} (converted from {student.percentage}% via /10 rule)"

            if effective_cgpa is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Minimum CGPA >= {requirements.min_cgpa}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("min_cgpa", f"Min CGPA: {requirements.min_cgpa}"),
                        reason="Both CGPA and percentage are missing; cannot confirm threshold.",
                    )
                )
            elif effective_cgpa >= requirements.min_cgpa:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Minimum CGPA >= {requirements.min_cgpa}",
                        student_value=cgpa_note,
                        comparison_result="pass",
                        evidence_source=_evidence_for("min_cgpa", f"Min CGPA: {requirements.min_cgpa}"),
                        reason=f"CGPA {cgpa_note} meets minimum {requirements.min_cgpa}.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Minimum CGPA >= {requirements.min_cgpa}",
                        student_value=cgpa_note,
                        comparison_result="fail",
                        evidence_source=_evidence_for("min_cgpa", f"Min CGPA: {requirements.min_cgpa}"),
                        reason=f"CGPA {cgpa_note} is below required minimum {requirements.min_cgpa}.",
                    )
                )

        # 7. Active Backlogs Constraint
        if requirements.max_active_backlogs is not None:
            if student.active_backlogs is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Active backlogs <= {requirements.max_active_backlogs}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("max_active_backlogs", f"Max backlogs: {requirements.max_active_backlogs}"),
                        reason="Active backlog count missing from profile.",
                    )
                )
            elif student.active_backlogs <= requirements.max_active_backlogs:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Active backlogs <= {requirements.max_active_backlogs}",
                        student_value=str(student.active_backlogs),
                        comparison_result="pass",
                        evidence_source=_evidence_for("max_active_backlogs", f"Max backlogs: {requirements.max_active_backlogs}"),
                        reason=f"Active backlogs ({student.active_backlogs}) within limit.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Active backlogs <= {requirements.max_active_backlogs}",
                        student_value=str(student.active_backlogs),
                        comparison_result="fail",
                        evidence_source=_evidence_for("max_active_backlogs", f"Max backlogs: {requirements.max_active_backlogs}"),
                        reason=f"Active backlogs ({student.active_backlogs}) exceed limit ({requirements.max_active_backlogs}).",
                    )
                )

        # 8. Prior Experience (Months)
        if requirements.min_experience_months is not None:
            if student.experience_months is None:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Experience >= {requirements.min_experience_months} months",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("min_experience_months", f"Min exp: {requirements.min_experience_months} months"),
                        reason="Prior experience duration not specified.",
                    )
                )
            elif student.experience_months >= requirements.min_experience_months:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Experience >= {requirements.min_experience_months} months",
                        student_value=f"{student.experience_months} months",
                        comparison_result="pass",
                        evidence_source=_evidence_for("min_experience_months", f"Min exp: {requirements.min_experience_months} months"),
                        reason="Experience meets minimum duration.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Experience >= {requirements.min_experience_months} months",
                        student_value=f"{student.experience_months} months",
                        comparison_result="fail",
                        evidence_source=_evidence_for("min_experience_months", f"Min exp: {requirements.min_experience_months} months"),
                        reason=f"Experience ({student.experience_months}m) below required {requirements.min_experience_months}m.",
                    )
                )

        # 9. Citizenship (only where explicitly & legally mandated in posting)
        if requirements.required_citizenship is not None:
            if not student.citizenship:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Citizenship: {requirements.required_citizenship}",
                        student_value=None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("required_citizenship", f"Citizenship: {requirements.required_citizenship}"),
                        reason="Posting explicitly specifies citizenship eligibility; student value missing.",
                    )
                )
            elif student.citizenship.strip().lower() == requirements.required_citizenship.strip().lower():
                audit.append(
                    RuleAuditItem(
                        requirement=f"Citizenship: {requirements.required_citizenship}",
                        student_value=student.citizenship,
                        comparison_result="pass",
                        evidence_source=_evidence_for("required_citizenship", f"Citizenship: {requirements.required_citizenship}"),
                        reason="Explicit citizenship requirement satisfied.",
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"Citizenship: {requirements.required_citizenship}",
                        student_value=student.citizenship,
                        comparison_result="fail",
                        evidence_source=_evidence_for("required_citizenship", f"Citizenship: {requirements.required_citizenship}"),
                        reason=f"Posting restricts applicants to '{requirements.required_citizenship}'.",
                    )
                )

        # 9b. Location & Remote Restrictions
        norm_req_locs = [
            loc for loc in (normalize_location(x) for x in requirements.allowed_locations) if loc
        ]
        if requirements.remote_allowed is True or "Remote" in norm_req_locs:
            audit.append(
                RuleAuditItem(
                    requirement="Location: Remote or hybrid remote allowed",
                    student_value="Remote compatible",
                    comparison_result="pass",
                    evidence_source=_evidence_for("allowed_locations", f"Allowed: {requirements.allowed_locations}"),
                    reason="Opportunity explicitly permits remote participation.",
                )
            )
        elif norm_req_locs:
            stu_locs = {
                loc for loc in (normalize_location(x) for x in student.preferred_locations) if loc
            }
            matched_locs = sorted(set(norm_req_locs) & stu_locs)
            if matched_locs:
                audit.append(
                    RuleAuditItem(
                        requirement=f"On-site location in [{', '.join(norm_req_locs)}]",
                        student_value=", ".join(matched_locs),
                        comparison_result="pass",
                        evidence_source=_evidence_for("allowed_locations", f"Allowed: {norm_req_locs}"),
                        reason=f"Student preferred location matches '{matched_locs[0]}'.",
                    )
                )
            elif student.open_to_relocate is True:
                audit.append(
                    RuleAuditItem(
                        requirement=f"On-site location in [{', '.join(norm_req_locs)}]",
                        student_value="Open to relocate",
                        comparison_result="pass",
                        evidence_source=_evidence_for("allowed_locations", f"Allowed: {norm_req_locs}"),
                        reason="Student explicitly indicated willingness to relocate.",
                    )
                )
            elif student.open_to_relocate is False:
                audit.append(
                    RuleAuditItem(
                        requirement=f"On-site location in [{', '.join(norm_req_locs)}]",
                        student_value=", ".join(sorted(stu_locs)) or "Not relocating",
                        comparison_result="fail",
                        evidence_source=_evidence_for("allowed_locations", f"Allowed: {norm_req_locs}"),
                        reason=(
                            f"Posting requires on-site presence in {', '.join(norm_req_locs)}, "
                            "and student is not open to relocation or location does not match."
                        ),
                    )
                )
            else:
                audit.append(
                    RuleAuditItem(
                        requirement=f"On-site location in [{', '.join(norm_req_locs)}]",
                        student_value=", ".join(sorted(stu_locs)) or None,
                        comparison_result="missing_student_info",
                        evidence_source=_evidence_for("allowed_locations", f"Allowed: {norm_req_locs}"),
                        reason="Student location match and relocation willingness are unconfirmed.",
                    )
                )

        # 10. Ambiguous / Non-automatable clauses
        for clause in requirements.ambiguous_clauses:
            audit.append(
                RuleAuditItem(
                    requirement="Manual institutional/special clause",
                    student_value="Unverified",
                    comparison_result="unable_to_verify",
                    evidence_source=clause,
                    reason="Clause requires manual verification against official guidelines.",
                )
            )

        # 11. Normalized Skill Breakdown (Required vs Preferred)
        stu_skills_norm = deduplicate_skills(student.skills)
        stu_skills_low = {s.lower() for s in stu_skills_norm}

        req_norm = deduplicate_skills(requirements.required_skills)
        pref_norm = deduplicate_skills(requirements.preferred_skills)

        matched_req = [s for s in req_norm if s.lower() in stu_skills_low]
        missing_req = [s for s in req_norm if s.lower() not in stu_skills_low]
        matched_pref = [s for s in pref_norm if s.lower() in stu_skills_low]
        missing_pref = [s for s in pref_norm if s.lower() not in stu_skills_low]

        # Decide final deterministic outcome
        results = [item.comparison_result for item in audit]
        if "fail" in results:
            outcome: EligibilityOutcome = "ineligible"
            summary = next(item.reason for item in audit if item.comparison_result == "fail")
        elif "unable_to_verify" in results:
            outcome = "unable_to_verify"
            summary = next(item.reason for item in audit if item.comparison_result == "unable_to_verify")
        elif "missing_student_info" in results:
            outcome = "needs_more_info"
            missing_names = [item.requirement for item in audit if item.comparison_result == "missing_student_info"]
            summary = f"Needs more student info to verify: {'; '.join(missing_names)}"
        elif missing_req and len(matched_req) == 0:
            # Explicit required technical stack completely absent
            outcome = "ineligible"
            summary = f"Missing all required technical skills: {', '.join(missing_req)}"
        else:
            outcome = "eligible"
            summary = "All verified hard constraints passed."

        return EligibilityDecision(
            opportunity_id=requirements.opportunity_id,
            status=outcome,
            is_eligible=(outcome == "eligible"),
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            audit_trail=audit,
            summary_reason=summary,
        )
