"""Async SQLAlchemy repositories package."""

from app.repositories.applications import ApplicationRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.embeddings import (
    CANONICAL_MODEL_ID,
    CANONICAL_VECTOR_DIM,
    EmbeddingRepository,
)
from app.repositories.notifications import NotificationRepository
from app.repositories.opportunities import (
    OpportunityPage,
    OpportunityRepository,
    decode_opportunity_cursor,
    encode_opportunity_cursor,
)
from app.repositories.profiles import ProfileRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.repositories.voice_sessions import VoiceSessionRepository

__all__ = [
    "ApplicationRepository",
    "ApprovalRepository",
    "CANONICAL_MODEL_ID",
    "CANONICAL_VECTOR_DIM",
    "CareerPassportRepository",
    "EmbeddingRepository",
    "NotificationRepository",
    "OpportunityPage",
    "OpportunityRepository",
    "ProfileRepository",
    "ResumeRepository",
    "StudentProfileRepository",
    "VoiceSessionRepository",
    "decode_opportunity_cursor",
    "encode_opportunity_cursor",
]
