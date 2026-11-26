"""Privacy-conscious PII masking, upload safety validation, and safe text guards."""

from __future__ import annotations

import re
from pathlib import Path

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?91[\s\-]?)?\b[6-9]\d{9}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")
AADHAAR_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

ALLOWED_RESUME_EXTENSIONS = {".txt", ".md", ".pdf", ".json"}
MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB safety limit
MAX_TEXT_CHARS = 100_000


def redact_pii(text: str) -> str:
    """Scrub emails, Indian mobile numbers, and Aadhaar-like 12-digit IDs from logs."""
    cleaned = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    cleaned = AADHAAR_RE.sub("[REDACTED_ID]", cleaned)
    cleaned = PHONE_RE.sub("[REDACTED_PHONE]", cleaned)
    return cleaned


def safe_log_preview(text: str, max_chars: int = 120) -> str:
    """Create a truncated, PII-scrubbed single-line preview for telemetry logs."""
    scrubbed = redact_pii(text).replace("\r", " ").replace("\n", " ").strip()
    if len(scrubbed) <= max_chars:
        return scrubbed
    return scrubbed[:max_chars] + "..."


def validate_upload_metadata(filename: str, size_bytes: int) -> None:
    """Validate uploaded resume filename extension and size safely before parsing."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise ValueError(
            f"Unsupported resume file extension '{ext}'. Allowed: {sorted(ALLOWED_RESUME_EXTENSIONS)}"
        )
    if size_bytes <= 0:
        raise ValueError("Uploaded resume file is empty.")
    if size_bytes > MAX_RESUME_BYTES:
        raise ValueError(
            f"Uploaded file exceeds {MAX_RESUME_BYTES // (1024 * 1024)} MB safety limit ({size_bytes} bytes)."
        )


def validate_text_input(text: str, field_name: str = "text") -> str:
    """Normalize and length-guard text inputs safely against memory spikes."""
    if not isinstance(text, str):
        raise TypeError(f"{field_name} must be a string.")
    stripped = text.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty.")
    if len(stripped) > MAX_TEXT_CHARS:
        raise ValueError(f"{field_name} exceeds maximum safe length of {MAX_TEXT_CHARS} characters.")
    return stripped
