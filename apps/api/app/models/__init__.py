"""ORM models package."""

from app.models.base import Base
from app.models.entities import (
    Application,
    ApprovalRequest,
    CareerPassport,
    Education,
    Notification,
    Opportunity,
    OpportunityEligibility,
    OpportunityEmbedding,
    Profile,
    Resume,
    SavedOpportunity,
    StudentProfile,
)

__all__ = [
    "Application",
    "ApprovalRequest",
    "Base",
    "CareerPassport",
    "Education",
    "Notification",
    "Opportunity",
    "OpportunityEligibility",
    "OpportunityEmbedding",
    "Profile",
    "Resume",
    "SavedOpportunity",
    "StudentProfile",
]
