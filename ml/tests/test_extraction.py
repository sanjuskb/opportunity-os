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
