"""Domain services package."""

from app.services.applications import ApplicationService
from app.services.approvals import ApprovalService
from app.services.career_passports import CareerPassportService
from app.services.eligibility import EligibilityService
from app.services.intelligence import IntelligenceService
from app.services.notifications import NotificationService
from app.services.opportunities import OpportunityService
from app.services.opportunity_text import (
    CanonicalOpportunityInput,
    build_canonical_opportunity_text,
    build_canonical_opportunity_text_from_fields,
    build_opportunity_embedding_payload,
    compute_content_hash,
)
from app.services.profiles import ProfileService, StudentProfileService
from app.services.resumes import ResumeService
from app.services.voice_sessions import VoiceSessionService

__all__ = [
    "ApplicationService",
    "ApprovalService",
    "CanonicalOpportunityInput",
    "CareerPassportService",
    "EligibilityService",
    "IntelligenceService",
    "NotificationService",
    "OpportunityService",
    "ProfileService",
    "ResumeService",
    "StudentProfileService",
    "VoiceSessionService",
    "build_canonical_opportunity_text",
    "build_canonical_opportunity_text_from_fields",
    "build_opportunity_embedding_payload",
    "compute_content_hash",
]
