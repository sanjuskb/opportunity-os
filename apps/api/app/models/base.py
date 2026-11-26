"""Declarative base for Opportunity OS SQLAlchemy ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all Opportunity OS ORM entities (schema owned by Supabase migrations)."""
