"""Backend Resume Magic-Byte Security, Text Extraction (PDF/DOCX/TXT/MD/JSON), & Grounded Verification."""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".json"}
MAX_RESUME_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DOCX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024

_FALLBACK_SKILL_KEYWORDS = [
    ("python", "Python"),
    ("fastapi", "FastAPI"),
    ("django", "Django"),
    ("flask", "Flask"),
    ("typescript", "TypeScript"),
    ("javascript", "JavaScript"),
    ("react", "React"),
    ("next.js", "Next.js"),
    ("node.js", "Node.js"),
    ("postgresql", "PostgreSQL"),
    ("postgres", "PostgreSQL"),
    ("sql", "SQL"),
    ("docker", "Docker"),
    ("kubernetes", "Kubernetes"),
    ("pytorch", "PyTorch"),
    ("tensorflow", "TensorFlow"),
    ("scikit-learn", "scikit-learn"),
    ("machine learning", "Machine Learning"),
    ("deep learning", "Deep Learning"),
    ("nlp", "NLP"),
    ("java", "Java"),
    ("c++", "C++"),
    ("go", "Go"),
    ("aws", "AWS"),
    ("gcp", "GCP"),
    ("git", "Git"),
    ("redis", "Redis"),
    ("playwright", "Playwright"),
    ("tailwind", "Tailwind CSS"),
]

_DEGREE_RE = re.compile(
    r"\b(B\.?Tech|B\.?E\.?|M\.?Tech|BCA|MCA|B\.?Sc|M\.?Sc|MBA)\b", re.IGNORECASE
)
_YEAR_RE = re.compile(r"\b(?:batch|grad(?:uation)?|class of)?\s*(202\d|203\d)\b", re.IGNORECASE)
_CGPA_RE = re.compile(r"\bCGPA\s*[:\-]?\s*(\d(?:\.\d{1,2})?)\s*(?:/\s*10)?", re.IGNORECASE)


def compute_sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def validate_resume_upload(filename: str, raw_bytes: bytes) -> str:
    """Validate extension, file size ceiling, and binary magic bytes strictly."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported resume file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )
    if not raw_bytes:
        raise ValueError("Uploaded resume file is empty.")
    if len(raw_bytes) > MAX_RESUME_UPLOAD_BYTES:
        raise ValueError(
            f"Uploaded resume exceeds {MAX_RESUME_UPLOAD_BYTES // (1024 * 1024)} MB safety limit."
        )

    if ext == ".pdf":
        if not raw_bytes.lstrip().startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature: file header does not start with %PDF-.")
        return "application/pdf"

    if ext == ".docx":
        if not raw_bytes.startswith(b"PK\x03\x04"):
            raise ValueError("Invalid DOCX signature: file is not a valid OOXML ZIP container.")
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                names = set(zf.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise ValueError("Invalid DOCX archive: missing required OOXML parts.")
                uncompressed = sum(info.file_size for info in zf.infolist())
                if uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise ValueError("DOCX archive exceeds decompressed size limit.")
        except zipfile.BadZipFile as exc:
            raise ValueError("Corrupted DOCX archive.") from exc
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    if ext == ".json":
        if b"\x00" in raw_bytes:
            raise ValueError("Invalid JSON file containing binary null bytes.")
        return "application/json"

    if b"\x00" in raw_bytes:
        raise ValueError("Invalid text file containing binary null bytes.")
    return "text/markdown" if ext == ".md" else "text/plain"


def extract_text_from_bytes(filename: str, raw_bytes: bytes) -> str:
    """Decode text cleanly from PDF, DOCX, TXT, MD, or JSON resume files."""
    ext = Path(filename or "").suffix.lower()
    if ext in {".txt", ".md"}:
        return raw_bytes.decode("utf-8", errors="replace").strip()

    if ext == ".json":
        text = raw_bytes.decode("utf-8", errors="replace")
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            pass
        return text.strip()

    if ext == ".pdf":
        import pymupdf

        pdf_doc: Any = pymupdf.open(stream=raw_bytes, filetype="pdf")  # type: ignore[no-untyped-call]
        return "\n".join(str(page.get_text("text")) for page in pdf_doc).strip()

    if ext == ".docx":
        import docx

        docx_doc: Any = docx.Document(io.BytesIO(raw_bytes))
        lines: list[str] = [p.text.strip() for p in docx_doc.paragraphs if p.text.strip()]
        for table in docx_doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        return "\n".join(lines).strip()

    raise ValueError(f"Unsupported resume format: {ext}")


def parse_structured_resume(raw_text: str) -> dict[str, Any]:
    """Run ML ResumeExtractionService when available, else deterministic fallback parser."""
    try:
        from ml.src.extraction.extractor import ResumeExtractionService

        svc = ResumeExtractionService(llm_backend=None)
        res = svc.extract_from_text(raw_text)
        data = res.model_dump(mode="json")
        return {
            **data,
            "raw_excerpt": raw_text[:1500],
            "parser_backend": "nexteras_ml_extractor",
        }
    except Exception:  # noqa: BLE001
        pass

    lower = raw_text.lower()
    skills: list[str] = []
    for needle, label in _FALLBACK_SKILL_KEYWORDS:
        if label not in skills and re.search(
            rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", lower
        ):
            skills.append(label)

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    full_name = lines[0][:80] if lines and len(lines[0].split()) <= 5 else None
    deg_m = _DEGREE_RE.search(raw_text)
    yr_m = _YEAR_RE.search(raw_text)
    cgpa_m = _CGPA_RE.search(raw_text)

    return {
        "profile": {
            "full_name": full_name,
            "degree": deg_m.group(1) if deg_m else None,
            "branch_or_specialization": None,
            "graduation_year": int(yr_m.group(1)) if yr_m else None,
            "cgpa": float(cgpa_m.group(1)) if cgpa_m else None,
        },
        "normalized_skills": skills,
        "projects": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "achievements": [],
        "confidence": 0.72 if skills else 0.45,
        "extraction_mode": "deterministic_api_fallback",
        "validation_status": "valid",
        "warnings": [],
        "raw_excerpt": raw_text[:1500],
        "parser_backend": "api_fallback",
    }


def verify_claim_against_premise(claim_id: str, premise: str, hypothesis: str) -> dict[str, Any]:
    """Verify tailored resume claims strictly against grounded student evidence."""
    try:
        from ml.src.verification.schemas import VerificationRequest
        from ml.src.verification.verifier import (
            EvidenceVerificationService,
            LexicalConsistencyFallbackBackend,
        )

        verifier = EvidenceVerificationService(backend=LexicalConsistencyFallbackBackend())
        res = verifier.verify_claim(
            VerificationRequest(
                claim_id=claim_id,
                premise_text=premise,
                hypothesis_claim=hypothesis,
            )
        )
        data = dict(res.model_dump(mode="json"))
        data["is_grounded"] = data.get("verdict") in {"supported", "entailed"}
        return data
    except Exception:  # noqa: BLE001
        p_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", premise.lower()))
        h_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", hypothesis.lower()))
        if not h_nums.issubset(p_nums):
            return {
                "claim_id": claim_id,
                "verdict": "contradicted",
                "entailment_score": 0.05,
                "contradiction_score": 0.9,
                "is_grounded": False,
                "advisory_message": "Rejected ungrounded numeric claim absent from student evidence.",
            }
        p_tokens = {w for w in re.findall(r"[a-z0-9]+", premise.lower()) if len(w) > 2}
        h_tokens = {w for w in re.findall(r"[a-z0-9]+", hypothesis.lower()) if len(w) > 2}
        overlap = len(p_tokens & h_tokens) / max(1, len(h_tokens))
        is_supported = overlap >= 0.35
        return {
            "claim_id": claim_id,
            "verdict": "supported" if is_supported else "insufficient_evidence",
            "entailment_score": round(overlap, 4),
            "contradiction_score": 0.0,
            "is_grounded": is_supported,
            "advisory_message": "Grounded in student evidence."
            if is_supported
            else "Insufficient grounding in student Career Passport/Resume.",
        }
