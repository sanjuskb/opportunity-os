"""Unit tests for Workstream A: Resume Skill & Profile Extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from ml.src.evaluation.extraction_eval import evaluate_extraction_benchmark
from ml.src.extraction.extractor import ResumeExtractionService, parse_llm_json_payload
from ml.src.infrastructure.security import redact_pii, validate_upload_metadata


class _MockValidLLM:
    def extract_json(self, resume_text: str) -> str:
        return """Here is the structured output:
```json
{
  "full_name": "Priya Sharma",
  "degree": "Bachelor of Technology",
  "branch_or_specialization": "CSE",
  "graduation_year": 2026,
  "technical_skills": ["Python", "Docker", "NonExistentQuantumTool"],
}
```"""


class _MockBrokenLLM:
    def extract_json(self, resume_text: str) -> str:
        return "not valid json {{{"


def test_extraction_benchmark_zero_hallucinations() -> None:
    svc = ResumeExtractionService()
    metrics = evaluate_extraction_benchmark(svc)
    assert metrics["cases_evaluated"] == 4
    assert metrics["schema_validity_rate"] == 1.0
    assert metrics["unsupported_extraction_count"] == 0
    assert metrics["skill_recall"] >= 0.9
    assert metrics["scalar_exact_match_accuracy"] >= 0.9


def test_llm_json_recovery_and_ungrounded_skill_drop() -> None:
    payload, warns = parse_llm_json_payload('```json\n{"a": 1,}\n```')
    assert payload == {"a": 1}
    assert warns

    svc = ResumeExtractionService(llm_backend=_MockValidLLM())
    resp = svc.extract_from_text("Priya Sharma\nB.Tech CSE Batch 2026\nSkills: Python, Docker")
    assert resp.validation_status == "recovered_partial_json"
    assert "Python" in resp.normalized_skills
    assert "NonExistentQuantumTool" not in resp.normalized_skills
    assert any("NonExistentQuantumTool" in w for w in resp.warnings)


def test_llm_broken_json_falls_back_cleanly() -> None:
    svc = ResumeExtractionService(llm_backend=_MockBrokenLLM())
    resp = svc.extract_from_text("B.Tech IT Batch 2027 CGPA: 8.1/10\nSkills: TypeScript, React")
    assert resp.validation_status == "fallback_after_llm_error"
    assert resp.extraction_mode == "deterministic_rules"
    assert "TypeScript" in resp.normalized_skills
    assert "React" in resp.normalized_skills


def test_file_validation_and_pii_redaction(tmp_path: Path) -> None:
    sample = tmp_path / "cv.txt"
    sample.write_text("Ravi Kumar\nEmail: ravi@example.com\nPhone: +91 9876543210\nSkills: Python, SQL", encoding="utf-8")
    resp = ResumeExtractionService().extract_from_file(sample)
    assert "Python" in resp.normalized_skills

    scrubbed = redact_pii("Contact ravi@example.com or 9876543210")
    assert "ravi@example.com" not in scrubbed
    assert "9876543210" not in scrubbed

    with pytest.raises(ValueError):
        validate_upload_metadata("resume.exe", 1024)
    with pytest.raises(ValueError):
        validate_upload_metadata("huge.txt", 10 * 1024 * 1024)


def test_extract_from_json_md_and_real_pdf(tmp_path: Path) -> None:
    svc = ResumeExtractionService()

    # Markdown resume
    md_path = tmp_path / "resume.md"
    md_path.write_text(
        "# Sneha Kulkarni\n## Education\nB.Tech CSE Batch 2026 CGPA: 8.9/10\n## Technical Skills\nPython, FastAPI, Docker\n",
        encoding="utf-8",
    )
    md_res = svc.extract_from_file(md_path)
    assert md_res.profile.graduation_year == 2026
    assert "FastAPI" in md_res.normalized_skills

    # JSON resume
    json_path = tmp_path / "resume.json"
    json_path.write_text(
        '{"full_name": "Arjun Verma", "degree": "B.E.", "branch": "ECE", "graduation_year": 2027, "cgpa": 8.3, "skills": ["C++", "STM32", "RTOS"]}',
        encoding="utf-8",
    )
    json_res = svc.extract_from_file(json_path)
    assert json_res.profile.full_name == "Arjun Verma"
    assert json_res.profile.degree == "B.E."
    assert "STM32" in json_res.normalized_skills

    # Real PDF binary generated with PyMuPDF
    import pymupdf

    pdf_path = tmp_path / "student_cv.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Name: Kavya Reddy\nEducation\nNIT Warangal | B.Tech CSE | Batch 2026 | CGPA: 8.6/10\nSkills\nPython, PostgreSQL, PyTorch",
    )
    doc.save(str(pdf_path))
    doc.close()

    pdf_res = svc.extract_from_file(pdf_path)
    assert pdf_res.profile.full_name == "Kavya Reddy"
    assert pdf_res.profile.cgpa == 8.6
    assert {"Python", "PostgreSQL", "PyTorch"}.issubset(set(pdf_res.normalized_skills))


def test_gemini_backend_blocks_missing_credentials_and_rejects_placeholders() -> None:
    from ml.src.integration.gemini_backends import (
        GeminiCredentialsMissingError,
        GeminiStructuredLLMBackend,
        get_external_service_status,
    )

    backend = GeminiStructuredLLMBackend(api_key="placeholder-google-gemini-api-key")
    assert backend.is_configured is False
    with pytest.raises(GeminiCredentialsMissingError):
        backend.extract_json("Sample resume")

    status = get_external_service_status({"GEMINI_API_KEY": "placeholder-key"})
    assert status["gemini_api"]["status"] == "CREDENTIALS_REQUIRED"
