"""Unified dependency-injectable ML Orchestration Service decoupled from FastAPI routes."""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any, Sequence

from ml.src.eligibility.engine import DeterministicEligibilityEngine
from ml.src.eligibility.schemas import (
    EligibilityDecision,
    StructuredOpportunityRequirements,
    StudentEligibilityInput,
)
from ml.src.extraction.extractor import ResumeExtractionService, StructuredLLMBackend
from ml.src.extraction.schemas import ExtractionResponse
from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE, MLInferenceError, ResourceManagedModelCache
from ml.src.integration.contracts import EligibilityCheckAPIResponse, HealthReadinessPayload
from ml.src.matching.semantic_matcher import RankedMatch, SemanticMatcher
from ml.src.multilingual.service import (
    MultilingualUnderstandingResult,
    MultilingualUnderstandingService,
    TranslationFallbackBackend,
)
from ml.src.ranking.baseline_ranker import DeterministicOpportunityRanker
from ml.src.ranking.schemas import CandidateOpportunity, RankingResponse, StudentRankingPreferences
from ml.src.verification.schemas import VerificationRequest, VerificationResult
from ml.src.verification.verifier import EvidenceVerificationService, NLIProbabilityBackend

logger = logging.getLogger("nexteras.ml.gateway")


class NexteRaSMLService:
    """
    Single clean entrypoint for FastAPI endpoints and LangGraph workers.
    Maintains lazy model initialization, fallback-safe semantic matching, and single-model RAM protection.
    """

    def __init__(
        self,
        *,
        cache: ResourceManagedModelCache | None = None,
        registry: ModelRegistry | None = None,
        semantic_model_path: str | None = None,
        llm_extractor_backend: StructuredLLMBackend | None = None,
        translation_fallback: TranslationFallbackBackend | None = None,
        nli_backend: NLIProbabilityBackend | None = None,
        semantic_encoder_override: Any | None = None,
        multilingual_encoder_override: Any | None = None,
        use_pretrained_nli: bool = False,
    ) -> None:
        self.cache = cache or GLOBAL_MODEL_CACHE
        self.registry = registry or ModelRegistry()

        self.extractor = ResumeExtractionService(llm_backend=llm_extractor_backend)
        self.eligibility_engine = DeterministicEligibilityEngine()
        self.ranker = DeterministicOpportunityRanker()
        self.semantic_matcher = SemanticMatcher(
            model_name_or_path=semantic_model_path,
            cache=self.cache,
            registry=self.registry,
            encoder_override=semantic_encoder_override,
        )
        self.multilingual_service = MultilingualUnderstandingService(
            model_id=os.environ.get("ML_MULTILINGUAL_MODEL_ID") or self.registry.get("multilingual_encoder").model_id,
            cache=self.cache,
            fallback_backend=translation_fallback,
            encoder_override=multilingual_encoder_override,
        )
        self.evidence_verifier = EvidenceVerificationService(
            backend=nli_backend,
            use_pretrained_nli=use_pretrained_nli,
        )

    @classmethod
    def from_env(cls) -> "NexteRaSMLService":
        """Instantiate NexteRaSMLService configured safely from runtime environment variables."""
        from pathlib import Path
        from ml.src.integration.gemini_backends import (
            GeminiStructuredLLMBackend,
            GeminiTranslationFallbackBackend,
            is_real_credential,
        )

        max_models = int(os.environ.get("ML_MAX_LOADED_MODELS", "1"))
        cpu_threads = int(os.environ.get("TORCH_NUM_THREADS", "6"))
        cache = (
            GLOBAL_MODEL_CACHE
            if max_models == GLOBAL_MODEL_CACHE.max_loaded_models and cpu_threads == GLOBAL_MODEL_CACHE.cpu_threads
            else ResourceManagedModelCache(max_loaded_models=max_models, cpu_threads=cpu_threads)
        )
        env_model_path = os.environ.get("ML_MATCHING_MODEL_PATH", "").strip()
        resolved_model_path = env_model_path if env_model_path and Path(env_model_path).exists() else None
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        has_gemini = is_real_credential(gemini_key)
        enable_nli = os.environ.get("ENABLE_PRETRAINED_NLI", "false").strip().lower() in ("1", "true", "yes")

        return cls(
            cache=cache,
            semantic_model_path=resolved_model_path,
            llm_extractor_backend=GeminiStructuredLLMBackend(gemini_key) if has_gemini else None,
            translation_fallback=GeminiTranslationFallbackBackend(gemini_key) if has_gemini else None,
            use_pretrained_nli=enable_nli,
        )

    def health_and_readiness(self) -> HealthReadinessPayload:
        rt = self.cache.ensure_cpu_runtime()
        stats = self.cache.stats()
        return HealthReadinessPayload(
            status="healthy",
            readiness="ready_lazy",
            device=str(rt["device"]),
            cuda_available=bool(rt["cuda_available"]),
            loaded_models=list(stats["loaded_keys"]),
            registry_count=len(self.registry.models),
            details={
                "cpu_threads": rt["cpu_threads"],
                "semantic_model_active": self.semantic_matcher.model_identifier,
                "using_finetuned_semantic_checkpoint": self.semantic_matcher.using_finetuned_checkpoint,
            },
        )

    def extract_resume(self, resume_text: str) -> ExtractionResponse:
        return self.extractor.extract_from_text(resume_text)

    def assess_eligibility(
        self,
        student: StudentEligibilityInput,
        requirements: StructuredOpportunityRequirements,
        *,
        reference_date: date | None = None,
    ) -> EligibilityDecision:
        return self.eligibility_engine.evaluate(student, requirements, reference_date=reference_date)

    def evaluate_eligibility_for_api(
        self,
        student: StudentEligibilityInput,
        requirements: StructuredOpportunityRequirements,
        *,
        semantic_similarity: float | None = None,
        reference_date: date | None = None,
    ) -> EligibilityCheckAPIResponse:
        decision = self.assess_eligibility(student, requirements, reference_date=reference_date)
        checks_dict = {item.requirement: (item.comparison_result == "pass") for item in decision.audit_trail}
        reasons = [item.reason for item in decision.audit_trail if item.comparison_result != "pass"] or [
            decision.summary_reason
        ]

        # Deterministic gate zeroed out if ineligible/unverified
        score = 0.0
        if decision.is_eligible:
            req_tot = len(decision.matched_required_skills) + len(decision.missing_required_skills)
            skill_pct = (len(decision.matched_required_skills) / req_tot * 100.0) if req_tot else 80.0
            if semantic_similarity is not None:
                sem_pct = max(0.0, min(100.0, semantic_similarity * 100.0))
                score = round(0.55 * sem_pct + 0.45 * skill_pct, 2)
            else:
                score = round(skill_pct, 2)

        return EligibilityCheckAPIResponse(
            opportunity_id=decision.opportunity_id,
            status=decision.status,
            is_eligible=decision.is_eligible,
            score=score,
            deterministic_checks=checks_dict,
            matched_skills=decision.matched_required_skills,
            missing_skills=decision.missing_required_skills,
            reasons=reasons,
            model_version="deterministic-rule-engine-v1",
        )

    def match_semantic(
        self,
        student_query: str,
        opportunities: Sequence[dict[str, str]],
        top_k: int = 5,
    ) -> tuple[list[RankedMatch], str]:
        try:
            matches = self.semantic_matcher.rank_opportunities(student_query, opportunities, top_k=top_k)
            return matches, self.semantic_matcher.model_identifier
        except MLInferenceError as exc:
            logger.error("Semantic model unavailable (%s); returning empty safe fallback.", exc.code)
            return [], "fallback_unavailable"

    def rank_opportunities(
        self,
        candidates: list[CandidateOpportunity],
        preferences: StudentRankingPreferences,
        *,
        reference_date: date | None = None,
    ) -> RankingResponse:
        return self.ranker.rank(candidates, preferences, reference_date=reference_date)

    def analyze_multilingual(
        self,
        query_text: str,
        doc_texts: Sequence[str],
    ) -> tuple[list[tuple[int, float]], MultilingualUnderstandingResult]:
        return self.multilingual_service.match_query_to_documents(query_text, doc_texts)

    def verify_claim_evidence(self, request: VerificationRequest) -> VerificationResult:
        return self.evidence_verifier.verify_claim(request)
