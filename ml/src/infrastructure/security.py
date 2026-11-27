"""Privacy-conscious PII masking, upload safety validation, and safe text guards."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?91[\s\-]?)?\b[6-9]\d{9}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")
AADHAAR_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

ALLOWED_RESUME_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".json"}
MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB safety limit
MAX_DOCX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024  # Zip-bomb guard
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


def validate_file_magic_bytes(filename: str, raw_bytes: bytes) -> str:
    """Verify binary magic-byte signatures match the declared resume file extension."""
    validate_upload_metadata(filename, len(raw_bytes))
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        if not raw_bytes.lstrip().startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature: file header does not begin with %PDF-.")
        return "application/pdf"

    if ext == ".docx":
        if not raw_bytes.startswith(b"PK\x03\x04"):
            raise ValueError("Invalid DOCX signature: file is not a valid OOXML ZIP container.")
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                names = set(zf.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise ValueError("Invalid DOCX structure: missing OOXML document parts.")
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise ValueError("DOCX archive exceeds safe decompressed size limit.")
        except zipfile.BadZipFile as exc:
            raise ValueError("Corrupted DOCX archive.") from exc
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    if ext == ".json":
        if b"\x00" in raw_bytes:
            raise ValueError("Binary null bytes detected in JSON resume upload.")
        return "application/json"

    if b"\x00" in raw_bytes:
        raise ValueError("Binary null bytes detected in text resume upload.")
    return "text/markdown" if ext == ".md" else "text/plain"


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
