"""
FastAPI ML & Eligibility endpoints for NexteRaS.

Degrades gracefully with RFC 7807 `503 Service Unavailable` when deployed in an API-only
container without heavy ML dependencies (`is_ml_subsystem_available() == False`), while
invoking real `NexteRaSMLService` inference in full-stack / ML worker runtimes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.security import require_supabase_role
from app.core.security_middleware import rate_limit
from app.ml.adapter import MLSubsystemUnavailableError, get_ml_service, is_ml_subsystem_available
from app.schemas.ml import (
    EvaluateEligibilityRequest,
    MLHealthResponse,
    MultilingualUnderstandRequest,
    PipelineRecommendRequest,
    RankOpportunitiesRequest,
    ResumeExtractRequest,
    SemanticMatchRequest,
    VerifyEvidenceRequestDTO,
)

ml_router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
    dependencies=[
        Depends(require_supabase_role("authenticated")),
        Depends(rate_limit("ml", window_seconds=60)),
    ],
)
eligibility_router = APIRouter(
    prefix="/ml/eligibility",
    tags=["ML Eligibility"],
    dependencies=[
        Depends(require_supabase_role("authenticated")),
        Depends(rate_limit("ml_eligibility", window_seconds=60)),
    ],
)


def _require_ml_service(request: Request) -> Any:
    """Resolve app-injected ML service override (testing/worker) or singleton default."""
    override = getattr(request.app.state, "ml_service", None)
    if override is not None:
        return override
    try:
        svc = get_ml_service()
        request.app.state.ml_service = svc
        return svc
    except MLSubsystemUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "urn:problem:ml_subsystem_unavailable",
                "title": "ML Subsystem Unavailable",
                "status": 503,
                "detail": str(exc),
            },
        ) from exc


@ml_router.get("/health", response_model=MLHealthResponse)
async def ml_health(request: Request) -> MLHealthResponse:
    """Non-blocking ML readiness and loaded-model memory telemetry."""
    if getattr(request.app.state, "ml_service", None) is None and not is_ml_subsystem_available():
        return MLHealthResponse(
            status="degraded_api_only",
            readiness="ml_package_not_installed",
            device="cpu",
            cuda_available=False,
            loaded_models=[],
            registry_count=0,
            ml_available=False,
            details={"note": "Running in slim API-only environment without ml.src installed."},
        )
    svc = _require_ml_service(request)
    payload = svc.health_and_readiness()
    return MLHealthResponse(**payload.model_dump(), ml_available=True)


@ml_router.post("/extract-resume")
async def extract_resume(body: ResumeExtractRequest, request: Request) -> dict[str, Any]:
    """Extract normalized skills, academics, missing fields, and evidence spans from resume text."""
    svc = _require_ml_service(request)
    try:
        res = svc.extract_resume(body.resume_text)
        return dict(res.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@ml_router.post("/multilingual/understand")
async def understand_multilingual_query(
    body: MultilingualUnderstandRequest, request: Request
) -> dict[str, Any]:
    """Normalize multilingual/Hinglish student query and rank document matches safely."""
    svc = _require_ml_service(request)
    try:
        ranked, meta = svc.analyze_multilingual(body.query_text, body.document_texts)
        return {
            "ranked_indices": [{"doc_index": idx, "score": sc} for idx, sc in ranked],
            "metadata": meta.model_dump(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@ml_router.post("/semantic-match")
async def semantic_match(body: SemanticMatchRequest, request: Request) -> dict[str, Any]:
    """Compute dense cosine matches using fine-tuned or baseline all-MiniLM-L6-v2."""
    svc = _require_ml_service(request)
    try:
        opp_dicts = [
            {"doc_id": o.doc_id, "title": o.title or o.doc_id, "doc_text": o.doc_text}
            for o in body.opportunities
        ]
        matches, model_used = svc.match_semantic(body.student_query, opp_dicts, top_k=body.top_k)
        return {
            "model_used": model_used,
            "using_finetuned_checkpoint": svc.semantic_matcher.using_finetuned_checkpoint,
            "matches": [{"doc_id": m.doc_id, "title": m.title, "score": m.score} for m in matches],
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@eligibility_router.post("/evaluate")
async def evaluate_eligibility(
    body: EvaluateEligibilityRequest, request: Request
) -> dict[str, Any]:
    """Deterministic rule evaluation paired with traceable audit explanations."""
    svc = _require_ml_service(request)
    from ml.src.eligibility.parser import parse_opportunity_requirements
    from ml.src.eligibility.schemas import (
        StructuredOpportunityRequirements,
        StudentEligibilityInput,
    )

    stu = StudentEligibilityInput.model_validate(body.student.model_dump())
    opp_data = body.opportunity
    if opp_data.description and not any(
        [
            opp_data.eligible_degrees,
            opp_data.eligible_branches,
            opp_data.eligible_graduation_years,
            opp_data.min_cgpa is not None,
            opp_data.required_skills,
            opp_data.allowed_locations,
        ]
    ):
        reqs = parse_opportunity_requirements(
            opp_data.opportunity_id,
            opp_data.title,
            opp_data.description,
            explicit_deadline=opp_data.deadline,
        )
    else:
        reqs = StructuredOpportunityRequirements.model_validate(
            opp_data.model_dump(exclude={"description"})
        )

    resp = svc.evaluate_eligibility_for_api(
        stu,
        reqs,
        semantic_similarity=body.semantic_similarity,
        reference_date=body.reference_date,
    )
    decision = svc.assess_eligibility(stu, reqs, reference_date=body.reference_date)
    return {
        **resp.model_dump(),
        "audit_trail": [item.model_dump() for item in decision.audit_trail],
        "summary_reason": decision.summary_reason,
    }


@ml_router.post("/rank-opportunities")
async def rank_opportunities(body: RankOpportunitiesRequest, request: Request) -> dict[str, Any]:
    """Hard-gate eligibility first, score semantically, and return explainable ranked list."""
    svc = _require_ml_service(request)
    from ml.src.eligibility.parser import parse_opportunity_requirements
    from ml.src.eligibility.schemas import (
        StructuredOpportunityRequirements,
        StudentEligibilityInput,
    )
    from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences

    stu = StudentEligibilityInput.model_validate(body.student.model_dump())
    prefs = StudentRankingPreferences.model_validate(body.preferences.model_dump())

    opp_docs = [
        {
            "doc_id": c.opportunity.opportunity_id,
            "title": c.opportunity.title,
            "doc_text": f"{c.opportunity.title} at {c.organization}. Required skills: {', '.join(c.opportunity.required_skills)}. {c.opportunity.description}",
        }
        for c in body.candidates
    ]
    matches, sem_model = svc.match_semantic(
        body.student_query_text, opp_docs, top_k=max(1, len(opp_docs))
    )
    sim_by_id = {m.doc_id: m.score for m in matches}

    rank_inputs: list[CandidateOpportunity] = []
    for c in body.candidates:
        opp = c.opportunity
        if opp.description and not any(
            [
                opp.eligible_degrees,
                opp.eligible_branches,
                opp.eligible_graduation_years,
                opp.min_cgpa is not None,
                opp.required_skills,
                opp.allowed_locations,
            ]
        ):
            reqs = parse_opportunity_requirements(
                opp.opportunity_id, opp.title, opp.description, explicit_deadline=opp.deadline
            )
        else:
            reqs = StructuredOpportunityRequirements.model_validate(
                opp.model_dump(exclude={"description"})
            )
        elig_dec = svc.assess_eligibility(stu, reqs, reference_date=body.reference_date)
        rank_inputs.append(
            CandidateOpportunity(
                opportunity_id=opp.opportunity_id,
                title=opp.title,
                organization=c.organization,
                opportunity_type=c.opportunity_type,
                location=c.location,
                is_remote=c.is_remote,
                source_url=c.source_url,
                is_verified_source=c.is_verified_source,
                has_compensation=c.has_compensation,
                monthly_compensation_inr=c.monthly_compensation_inr,
                deadline=opp.deadline,
                is_active=c.is_active,
                semantic_similarity=sim_by_id.get(opp.opportunity_id),
                eligibility=elig_dec,
            )
        )

    ranking_resp = svc.rank_opportunities(rank_inputs, prefs, reference_date=body.reference_date)
    return {"semantic_model_used": sem_model, **ranking_resp.model_dump(mode="json")}


@ml_router.post("/verify-evidence")
async def verify_evidence(body: VerifyEvidenceRequestDTO, request: Request) -> dict[str, Any]:
    """Advisory NLI evidence consistency check (never approves autonomous submission)."""
    svc = _require_ml_service(request)
    from ml.src.verification.schemas import VerificationRequest

    try:
        res = svc.verify_claim_evidence(
            VerificationRequest(
                claim_id=body.claim_id,
                premise_text=body.premise_text,
                hypothesis_claim=body.hypothesis_claim,
            )
        )
        return dict(res.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@ml_router.post("/recommend-pipeline")
async def recommend_pipeline(body: PipelineRecommendRequest, request: Request) -> dict[str, Any]:
    """
    End-to-end orchestration pipeline:
    Resume Extract -> Multilingual Query -> Eligibility Check -> Semantic Match -> Rank -> NLI Guard -> M11 Approval Gate.
    """
    svc = _require_ml_service(request)
    from ml.src.eligibility.parser import parse_opportunity_requirements
    from ml.src.eligibility.schemas import (
        StructuredOpportunityRequirements,
        StudentEligibilityInput,
    )
    from ml.src.multilingual.preprocessing import preprocess_multilingual_query
    from ml.src.multilingual.service import MultilingualUnderstandingResult
    from ml.src.ranking.schemas import CandidateOpportunity, StudentRankingPreferences
    from ml.src.verification.schemas import VerificationRequest

    ext = svc.extract_resume(body.resume_text)
    prof = ext.profile
    stu = StudentEligibilityInput(
        student_id=str(body.student_overrides.get("student_id") or body.preferences.student_id),
        degree=body.student_overrides.get("degree") or prof.degree,
        branch=body.student_overrides.get("branch") or prof.branch_or_specialization,
        graduation_year=body.student_overrides.get("graduation_year") or prof.graduation_year,
        cgpa=body.student_overrides.get("cgpa") if "cgpa" in body.student_overrides else prof.cgpa,
        percentage=body.student_overrides.get("percentage")
        if "percentage" in body.student_overrides
        else prof.percentage,
        active_backlogs=body.student_overrides.get("active_backlogs"),
        skills=list({*ext.normalized_skills, *body.student_overrides.get("skills", [])}),
        experience_months=body.student_overrides.get("experience_months"),
        preferred_locations=body.student_overrides.get(
            "preferred_locations", body.preferences.preferred_locations
        ),
        open_to_relocate=body.student_overrides.get("open_to_relocate"),
        citizenship=body.student_overrides.get("citizenship"),
    )

    prep = preprocess_multilingual_query(body.query_text)
    if prep.predicted_locale == "en":
        multi_meta = MultilingualUnderstandingResult(
            preprocessed=prep,
            model_id=svc.semantic_matcher.model_identifier,
            embedding_dimension=svc.semantic_matcher.embedding_dimension,
            top_similarity_score=None,
            fallback_triggered=False,
            fallback_query_text=None,
            warnings=[],
        )
        retrieval_query = prep.normalized_text
    else:
        opp_texts = [f"{c.opportunity.title} {c.opportunity.description}" for c in body.candidates]
        _, multi_meta = svc.analyze_multilingual(body.query_text, opp_texts)
        retrieval_query = multi_meta.fallback_query_text or multi_meta.preprocessed.normalized_text

    opp_docs = [
        {
            "doc_id": c.opportunity.opportunity_id,
            "title": c.opportunity.title,
            "doc_text": f"{c.opportunity.title} at {c.organization}. Skills: {', '.join(c.opportunity.required_skills)}. {c.opportunity.description}",
        }
        for c in body.candidates
    ]
    matches, sem_model = svc.match_semantic(retrieval_query, opp_docs, top_k=max(1, len(opp_docs)))
    sim_by_id = {m.doc_id: m.score for m in matches}

    prefs = StudentRankingPreferences.model_validate(body.preferences.model_dump())
    rank_inputs: list[CandidateOpportunity] = []
    eligibility_map: dict[str, Any] = {}
    for c in body.candidates:
        opp = c.opportunity
        if opp.description and not any(
            [
                opp.eligible_degrees,
                opp.eligible_branches,
                opp.eligible_graduation_years,
                opp.min_cgpa is not None,
                opp.required_skills,
                opp.allowed_locations,
            ]
        ):
            reqs = parse_opportunity_requirements(
                opp.opportunity_id, opp.title, opp.description, explicit_deadline=opp.deadline
            )
        else:
            reqs = StructuredOpportunityRequirements.model_validate(
                opp.model_dump(exclude={"description"})
            )
        elig_dec = svc.assess_eligibility(stu, reqs, reference_date=body.reference_date)
        eligibility_map[opp.opportunity_id] = elig_dec.model_dump(mode="json")
        rank_inputs.append(
            CandidateOpportunity(
                opportunity_id=opp.opportunity_id,
                title=opp.title,
                organization=c.organization,
                opportunity_type=c.opportunity_type,
                location=c.location,
                is_remote=c.is_remote,
                source_url=c.source_url,
                is_verified_source=c.is_verified_source,
                has_compensation=c.has_compensation,
                monthly_compensation_inr=c.monthly_compensation_inr,
                deadline=opp.deadline,
                is_active=c.is_active,
                semantic_similarity=sim_by_id.get(opp.opportunity_id),
                eligibility=elig_dec,
            )
        )

    ranking_resp = svc.rank_opportunities(rank_inputs, prefs, reference_date=body.reference_date)

    premise = body.career_passport_premise or body.resume_text
    evidence_checks = [
        svc.verify_claim_evidence(
            VerificationRequest(
                claim_id=f"claim-{i + 1}", premise_text=premise, hypothesis_claim=claim
            )
        ).model_dump()
        for i, claim in enumerate(body.synthesized_resume_claims)
    ]

    return {
        "extracted_profile": ext.model_dump(mode="json"),
        "multilingual_metadata": multi_meta.model_dump(mode="json"),
        "semantic_model_used": sem_model,
        "eligibility_decisions": eligibility_map,
        "ranking": ranking_resp.model_dump(mode="json"),
        "evidence_verifications": evidence_checks,
        "requires_human_approval": True,  # Mandatory M11 Human-in-the-Loop Gate
        "approval_status": "pending",
    }
