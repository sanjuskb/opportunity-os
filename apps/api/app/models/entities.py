"""SQLAlchemy 2.0 ORM models matching Supabase PostgreSQL migrations.

Schema DDL is owned exclusively by `supabase/migrations/*.sql`.
Relationships use `passive_deletes=True` to defer cascading deletes to PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(
        String(10), nullable=True, server_default="en"
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student_profiles: Mapped[list[StudentProfile]] = relationship(
        back_populates="profile", passive_deletes=True
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    college_name: Mapped[str] = mapped_column(Text, nullable=False)
    degree: Mapped[str] = mapped_column(Text, nullable=False)
    branch: Mapped[str] = mapped_column(Text, nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped[Profile] = relationship(back_populates="student_profiles")
    education_records: Mapped[list[Education]] = relationship(
        back_populates="student_profile", passive_deletes=True
    )
    career_passport: Mapped[CareerPassport | None] = relationship(
        back_populates="student_profile", uselist=False, passive_deletes=True
    )


class Education(Base):
    __tablename__ = "education"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution: Mapped[str] = mapped_column(Text, nullable=False)
    degree: Mapped[str] = mapped_column(Text, nullable=False)
    field_of_study: Mapped[str] = mapped_column(Text, nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student_profile: Mapped[StudentProfile] = relationship(back_populates="education_records")


class CareerPassport(Base):
    __tablename__ = "career_passports"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    verified_achievements: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=True, server_default="[]"
    )
    coursework: Mapped[list[Any]] = mapped_column(JSONB, nullable=True, server_default="[]")
    certifications: Mapped[list[Any]] = mapped_column(JSONB, nullable=True, server_default="[]")
    projects: Mapped[list[Any]] = mapped_column(JSONB, nullable=True, server_default="[]")
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    student_profile: Mapped[StudentProfile] = relationship(back_populates="career_passport")


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    stipend_or_salary: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    retrieval_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True, server_default="true")
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True, server_default="{}")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    eligibility: Mapped[OpportunityEligibility | None] = relationship(
        back_populates="opportunity", uselist=False, passive_deletes=True
    )
    embedding_record: Mapped[OpportunityEmbedding | None] = relationship(
        back_populates="opportunity", uselist=False, passive_deletes=True
    )


class OpportunityEligibility(Base):
    __tablename__ = "opportunity_eligibility"
    __table_args__ = (
        UniqueConstraint("opportunity_id", name="uq_opportunity_eligibility_opportunity_id"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    eligible_batches: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=True, server_default="{}"
    )
    eligible_degrees: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=True, server_default="{}"
    )
    eligible_branches: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=True, server_default="{}"
    )
    min_cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=True, server_default="{}"
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="eligibility")


class OpportunityEmbedding(Base):
    __tablename__ = "opportunity_embeddings"
    __table_args__ = (
        CheckConstraint(
            "embedding_status IN ('pending', 'ready', 'failed')",
            name="chk_opportunity_embeddings_status",
        ),
        CheckConstraint(
            "retry_count >= 0",
            name="chk_opportunity_embeddings_retry_count_non_negative",
        ),
        CheckConstraint(
            "embedding_status <> 'ready' OR embedding_minilm_384 IS NOT NULL",
            name="chk_opportunity_embeddings_ready_requires_vector",
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.opportunities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    embedding_minilm_384: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    embedding_model_id: Mapped[str | None] = mapped_column(
        Text, nullable=True, server_default="sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_model_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    opportunity: Mapped[Opportunity] = relationship(back_populates="embedding_record")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("user_id", "opportunity_id", name="uq_applications_user_opportunity"),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, server_default="drafting")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default="manual"
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True, server_default="pending")
    user_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default="opportunity_match"
    )
    is_read: Mapped[bool | None] = mapped_column(Boolean, nullable=True, server_default="false")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    master_content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "opportunity_id", name="saved_opportunities_user_id_opportunity_id_key"
        ),
        {"schema": "public"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    saved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class VoiceSession(Base):
    __tablename__ = "voice_sessions"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    detected_language: Mapped[str | None] = mapped_column(String(10), server_default="en")
    audio_duration_seconds: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), server_default="0"
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), server_default="completed")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
