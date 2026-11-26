"""Deterministic canonical opportunity text builder and SHA-256 content hasher."""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.models.entities import Opportunity


@dataclass(frozen=True)
class CanonicalOpportunityInput:
    """Immutable snapshot of meaningful opportunity fields used for embedding."""

    title: str
    organization: str
    opp_type: str
    location: str
    description: str
    stipend_or_salary: str | None = None
    required_skills: Sequence[str] | None = None
    eligible_degrees: Sequence[str] | None = None
    eligible_branches: Sequence[str] | None = None
    eligible_batches: Sequence[int] | None = None
    min_cgpa: Decimal | float | str | None = None


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    nfc = unicodedata.normalize("NFC", value)
    return " ".join(nfc.split())


def _normalize_str_list(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    deduped: dict[str, str] = {}
    for raw in values:
        norm = _normalize_text(raw)
        if norm:
            key = norm.lower()
            deduped.setdefault(key, norm)
    return [deduped[k] for k in sorted(deduped)]


def _normalize_int_list(values: Sequence[int] | None) -> list[str]:
    if not values:
        return []
    return [str(v) for v in sorted(set(values))]


def _normalize_cgpa(value: Decimal | float | str | None) -> str:
    if value is None:
        return ""
    dec = Decimal(str(value)).normalize()
    return format(dec, "f")


def build_canonical_opportunity_text_from_fields(fields: CanonicalOpportunityInput) -> str:
    """Build deterministic, labeled, NFC-normalized canonical text from opportunity fields.

    Excludes mutable operational metadata (IDs, URLs, providers, timestamps, active flags,
    saved/view counts, or user-specific data).
    """
    lines: list[str] = [
        f"Title: {_normalize_text(fields.title)}",
        f"Organization: {_normalize_text(fields.organization)}",
        f"Type: {_normalize_text(fields.opp_type)}",
        f"Location: {_normalize_text(fields.location)}",
    ]

    compensation = _normalize_text(fields.stipend_or_salary)
    if compensation:
        lines.append(f"Compensation: {compensation}")

    skills = _normalize_str_list(fields.required_skills)
    if skills:
        lines.append(f"Required Skills: {', '.join(skills)}")

    degrees = _normalize_str_list(fields.eligible_degrees)
    if degrees:
        lines.append(f"Eligible Degrees: {', '.join(degrees)}")

    branches = _normalize_str_list(fields.eligible_branches)
    if branches:
        lines.append(f"Eligible Branches: {', '.join(branches)}")

    batches = _normalize_int_list(fields.eligible_batches)
    if batches:
        lines.append(f"Eligible Batches: {', '.join(batches)}")

    min_cgpa = _normalize_cgpa(fields.min_cgpa)
    if min_cgpa:
        lines.append(f"Minimum CGPA: {min_cgpa}")

    description = _normalize_text(fields.description)
    lines.append(f"Description: {description}")
    return "\n".join(lines)


def build_canonical_opportunity_text(opportunity: Opportunity) -> str:
    """Build canonical embedding passage from an Opportunity ORM instance (+ eligibility)."""
    elig = opportunity.eligibility
    fields = CanonicalOpportunityInput(
        title=opportunity.title,
        organization=opportunity.organization,
        opp_type=opportunity.type,
        location=opportunity.location,
        description=opportunity.description,
        stipend_or_salary=opportunity.stipend_or_salary,
        required_skills=elig.required_skills if elig is not None else None,
        eligible_degrees=elig.eligible_degrees if elig is not None else None,
        eligible_branches=elig.eligible_branches if elig is not None else None,
        eligible_batches=elig.eligible_batches if elig is not None else None,
        min_cgpa=elig.min_cgpa if elig is not None else None,
    )
    return build_canonical_opportunity_text_from_fields(fields)


def compute_content_hash(canonical_text: str) -> str:
    """Compute deterministic UTF-8 SHA-256 hex digest over normalized canonical text."""
    if not isinstance(canonical_text, str) or not canonical_text.strip():
        raise ValueError("canonical_text must be a non-empty string.")
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def build_opportunity_embedding_payload(opportunity: Opportunity) -> tuple[str, str]:
    """Return (canonical_text, sha256_content_hash) for an Opportunity ORM object."""
    canonical_text = build_canonical_opportunity_text(opportunity)
    return canonical_text, compute_content_hash(canonical_text)
