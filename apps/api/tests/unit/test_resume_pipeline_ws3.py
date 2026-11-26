"""WS3 unit tests covering magic-byte checks, real PDF/DOCX extraction, grounded tailoring, & PDF export."""

from __future__ import annotations

import io
from pathlib import Path
from uuid import uuid4

import pymupdf
import pytest
from docx import Document

from app.core.config import Settings
from app.integrations.supabase_storage import ResumeStorageClient, build_resume_storage_path
from app.services.resume_parser import (
    extract_text_from_bytes,
    parse_structured_resume,
    validate_resume_upload,
    verify_claim_against_premise,
)
from app.services.resume_pdf import render_resume_pdf


def _make_pdf_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    raw = doc.tobytes()
    doc.close()
    return raw


def _make_docx_bytes(lines: list[str]) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_magic_byte_validation_and_docx_pdf_extraction() -> None:
    pdf_bytes = _make_pdf_bytes(
        "Aarav Mehta\nB.Tech CSE Batch 2027 CGPA: 8.8/10\nTechnical Skills\nPython, FastAPI, PostgreSQL"
    )
    assert validate_resume_upload("aarav.pdf", pdf_bytes) == "application/pdf"
    pdf_text = extract_text_from_bytes("aarav.pdf", pdf_bytes)
    assert "Aarav Mehta" in pdf_text
    parsed_pdf = parse_structured_resume(pdf_text)
    assert "Python" in parsed_pdf["normalized_skills"]

    docx_bytes = _make_docx_bytes(
        [
            "Neha Sharma",
            "Education: NIT Trichy | B.Tech ECE | Batch 2026 | CGPA: 8.5/10",
            "Technical Skills: Python, Docker, SQL, React",
            "Projects: Hostel Queue Optimizer - Built FastAPI API with PostgreSQL locks.",
        ]
    )
    assert (
        validate_resume_upload("neha.docx", docx_bytes)
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    docx_text = extract_text_from_bytes("neha.docx", docx_bytes)
    assert "NIT Trichy" in docx_text
    parsed_docx = parse_structured_resume(docx_text)
    assert parsed_docx["profile"]["graduation_year"] == 2026
    assert {"Python", "Docker", "SQL", "React"}.issubset(set(parsed_docx["normalized_skills"]))

    # Forged magic bytes must fail with ValueError
    with pytest.raises(ValueError, match="Invalid PDF signature"):
        validate_resume_upload("spoof.pdf", b"not-a-pdf-header-at-all")
    with pytest.raises(ValueError, match="Invalid DOCX signature"):
        validate_resume_upload("spoof.docx", b"plain text pretending to be docx")
    with pytest.raises(ValueError, match="empty"):
        validate_resume_upload("empty.txt", b"")


def test_grounded_claim_verification_blocks_fabrication() -> None:
    premise = (
        "Built Hostel Queue Optimizer using FastAPI and PostgreSQL handling 100 student requests."
    )
    ok = verify_claim_against_premise(
        "c1",
        premise,
        "Built Hostel Queue Optimizer in FastAPI with PostgreSQL for 100 student requests.",
    )
    assert ok["is_grounded"] is True

    fabricated = verify_claim_against_premise(
        "c2",
        premise,
        "Led a 12-person robotics division at NASA for 5 years.",
    )
    assert fabricated["is_grounded"] is False


@pytest.mark.asyncio
async def test_local_sandbox_storage_and_ats_pdf_rendering(tmp_path: Path) -> None:
    uid = uuid4()
    rid = uuid4()
    path = build_resume_storage_path(uid, rid, "../../weird name/resume?.pdf")
    assert path.startswith(f"{uid}/{rid}/")
    assert ".." not in path

    storage = ResumeStorageClient(
        Settings(
            ENVIRONMENT="development",
            SUPABASE_URL="",
            SUPABASE_SERVICE_ROLE_KEY="",
            LOCAL_RESUME_STORAGE_DIR=str(tmp_path),
        )
    )
    mode = await storage.upload_bytes(
        storage_path=path,
        raw_bytes=_make_pdf_bytes("Test Resume Content"),
        content_type="application/pdf",
    )
    assert mode == "local_sandbox"
    assert (tmp_path / path).exists()

    pdf_out = render_resume_pdf(
        "Backend Engineer Resume",
        {
            "profile": {
                "full_name": "Neha Sharma",
                "degree": "B.Tech",
                "branch": "CSE",
                "graduation_year": 2026,
                "cgpa": 8.9,
            },
            "normalized_skills": ["Python", "FastAPI", "PostgreSQL"],
            "tailored_bullets": [
                "Built atomic Postgres booking endpoints — handled ₹0 budget hackathon scale."
            ],
        },
    )
    assert pdf_out.startswith(b"%PDF-")
    assert len(pdf_out) > 600
