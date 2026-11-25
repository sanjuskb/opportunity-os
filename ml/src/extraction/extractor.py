"""Hybrid Resume & Profile Extraction Service (Deterministic + Pluggable LLM JSON)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from ml.src.extraction.schemas import (
    EducationEntry,
    EvidenceSpan,
    ExtractedResumeProfile,
    ExtractionResponse,
    ProjectOrExperienceEntry,
)
from ml.src.extraction.taxonomy import (
    BRANCH_ALIASES,
    DEGREE_ALIASES,
    deduplicate_skills,
    find_skills_with_evidence,
    normalize_branch,
    normalize_degree,
)
from ml.src.infrastructure.security import safe_log_preview, validate_text_input, validate_upload_metadata

logger = logging.getLogger("nexteras.ml.extraction")


class StructuredLLMBackend(Protocol):
    """Replaceable interface for cloud/local structured JSON extraction (no hardcoded API keys)."""

    def extract_json(self, resume_text: str) -> str:
        ...


SECTION_ALIASES = {
    "education": {"education", "academics", "academic background", "qualification"},
    "skills": {"skills", "technical skills", "tech stack", "core competencies"},
    "projects": {"projects", "key projects", "academic projects"},
    "experience": {"experience", "work experience", "employment"},
    "internships": {"internships", "internship experience"},
    "certifications": {"certifications", "certificates", "courses"},
    "achievements": {"achievements", "awards", "honors", "accomplishments"},
    "interests": {"interests", "relevant interests", "career interests", "areas of interest"},
}


def parse_llm_json_payload(raw_text: str) -> tuple[dict[str, Any], list[str]]:
    """
    Safely recover JSON from LLM outputs (strips markdown code fences / leading prose).
    Raises ValueError if no valid JSON object can be parsed.
    """
    warnings: list[str] = []
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1)
        warnings.append("Stripped markdown fence around structured JSON response.")
    elif not cleaned.startswith("{"):
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            cleaned = cleaned[brace_start : brace_end + 1]
            warnings.append("Trimmed non-JSON wrapper text from LLM output.")

    # Remove trailing commas before } or ] (common malformed LLM JSON issue)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Top-level parsed JSON must be an object.")
    return parsed, warnings


class ResumeExtractionService:
    """
    Extracts structured career profile data from raw resumes with zero fabricated claims.
    Uses deterministic parsing by default and optionally refines via StructuredLLMBackend.
    """

    def __init__(self, llm_backend: StructuredLLMBackend | None = None) -> None:
        self.llm_backend = llm_backend

    def extract_from_file(self, file_path: str | Path) -> ExtractionResponse:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {path}")
        raw_bytes = path.read_bytes()
        validate_upload_metadata(path.name, len(raw_bytes))

        ext = path.suffix.lower()
        if ext in {".txt", ".md", ".json"}:
            text = raw_bytes.decode("utf-8", errors="replace")
        elif ext == ".pdf":
            text = self._extract_pdf_bytes(raw_bytes)
        else:
            raise ValueError(f"Unsupported extension: {ext}")
        return self.extract_from_text(text)

    @staticmethod
    def _extract_pdf_bytes(raw_bytes: bytes) -> str:
        try:
            import pymupdf  # type: ignore[import-untyped]

            doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
            return "\n".join(page.get_text("text") for page in doc)
        except ImportError as exc:
            raise RuntimeError(
                "PDF extraction requires pymupdf installed in ml/.venv, or supply decoded resume text."
            ) from exc

    def extract_from_text(self, resume_text: str) -> ExtractionResponse:
        text = validate_text_input(resume_text, "resume_text")
        logger.debug("Running resume extraction preview=%s", safe_log_preview(text))

        det_profile = self._deterministic_extract(text)
        if self.llm_backend is None:
            return self._finalize(
                det_profile,
                mode="deterministic_rules",
                status="valid",
                confidence=self._estimate_confidence(det_profile),
                warnings=[],
            )

        try:
            raw_json = self.llm_backend.extract_json(text)
            payload, parse_warnings = parse_llm_json_payload(raw_json)
            merged, val_warnings = self._merge_llm_payload_safely(det_profile, payload, text)
            all_warnings = parse_warnings + val_warnings
            status = "recovered_partial_json" if parse_warnings or val_warnings else "valid"
            return self._finalize(
                merged,
                mode="hybrid_llm_validated",
                status=status,
                confidence=min(0.95, self._estimate_confidence(merged) + 0.08),
                warnings=all_warnings,
            )
        except Exception as exc:
            logger.warning("LLM extraction fallback triggered: %s", exc)
            return self._finalize(
                det_profile,
                mode="deterministic_rules",
                status="fallback_after_llm_error",
                confidence=self._estimate_confidence(det_profile),
                warnings=[f"LLM JSON recovery failed cleanly ({type(exc).__name__}); used deterministic rules."],
            )

    def _deterministic_extract(self, text: str) -> ExtractedResumeProfile:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        evidence: list[EvidenceSpan] = []

        full_name = self._extract_name(lines, evidence)
        sections = self._split_sections(lines)

        edu_text = "\n".join(sections.get("education", [])) or text
        degree = self._extract_degree(edu_text, evidence)
        branch = self._extract_branch(edu_text, evidence)
        grad_year = self._extract_graduation_year(edu_text, evidence)
        cgpa, pct = self._extract_scores(edu_text, evidence)

        edu_entries: list[EducationEntry] = []
        if any(v is not None for v in (degree, branch, grad_year, cgpa, pct)):
            inst = self._extract_institution(sections.get("education", lines[:8]))
            edu_entries.append(
                EducationEntry(
                    institution=inst,
                    degree=degree,
                    branch=branch,
                    graduation_year=grad_year,
                    cgpa=cgpa,
                    percentage=pct,
                )
            )

        skill_hits = find_skills_with_evidence(text)
        langs = deduplicate_skills([c for c, grp, _ in skill_hits if grp == "programming_languages"])
        fws = deduplicate_skills([c for c, grp, _ in skill_hits if grp == "frameworks"])
        tools = deduplicate_skills([c for c, grp, _ in skill_hits if grp == "tools"])
        all_tech = deduplicate_skills([c for c, _, _ in skill_hits])
        for c, _, snip in skill_hits:
            evidence.append(EvidenceSpan(field="technical_skills", value=c, source_snippet=snip))

        projects = self._extract_entries(sections.get("projects", []), "projects", evidence)
        experience = self._extract_entries(sections.get("experience", []), "experience", evidence)
        internships = self._extract_entries(sections.get("internships", []), "internships", evidence)

        # If an entry inside experience explicitly says "intern", also surface in internships
        for exp in experience:
            if re.search(r"\bintern(ship)?\b", f"{exp.title} {exp.summary or ''}", re.IGNORECASE):
                if exp not in internships:
                    internships.append(exp)

        certs = self._extract_bullet_list(sections.get("certifications", []), "certifications", evidence)
        achievements = self._extract_bullet_list(sections.get("achievements", []), "achievements", evidence)
        interests = self._extract_interests(sections.get("interests", []), evidence)

        profile = ExtractedResumeProfile(
            full_name=full_name,
            education=edu_entries,
            degree=degree,
            branch_or_specialization=branch,
            graduation_year=grad_year,
            cgpa=cgpa,
            percentage=pct,
            programming_languages=langs,
            frameworks=fws,
            tools=tools,
            technical_skills=all_tech,
            projects=projects,
            experience=experience,
            internships=internships,
            certifications=certs,
            achievements=achievements,
            relevant_interests=interests,
            evidence=evidence,
        )
        profile.missing_fields = self._compute_missing_fields(profile)
        return profile

    @staticmethod
    def _split_sections(lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current = "header"
        for ln in lines:
            cleaned = re.sub(r"[:\-_=]+$", "", ln).strip().lower()
            matched_section = None
            if len(cleaned.split()) <= 4:
                for sec_name, aliases in SECTION_ALIASES.items():
                    if cleaned in aliases:
                        matched_section = sec_name
                        break
            if matched_section:
                current = matched_section
                sections.setdefault(current, [])
            else:
                sections.setdefault(current, []).append(ln)
        return sections

    @staticmethod
    def _extract_name(lines: list[str], evidence: list[EvidenceSpan]) -> str | None:
        all_section_headers = {h for group in SECTION_ALIASES.values() for h in group} | {
            "resume",
            "curriculum vitae",
            "cv",
            "profile",
            "summary",
        }
        for ln in lines[:4]:
            if m := re.match(r"^(?:name|candidate)\s*:\s*(.+)$", ln, re.IGNORECASE):
                val = m.group(1).strip()
                evidence.append(EvidenceSpan(field="full_name", value=val, source_snippet=ln))
                return val
            cleaned_hdr = re.sub(r"[:\-_=]+$", "", ln).strip().lower()
            if cleaned_hdr in all_section_headers:
                continue
            if (
                2 <= len(ln.split()) <= 4
                and not re.search(r"[@\d|:/]", ln)
                and all(w[0].isupper() for w in ln.split() if w.isalpha())
            ):
                evidence.append(EvidenceSpan(field="full_name", value=ln, source_snippet=ln))
                return ln
        return None

    @staticmethod
    def _extract_institution(lines: list[str]) -> str | None:
        for ln in lines:
            if re.search(r"\b(institute|university|college|iit|nit|iiit|bits|vit)\b", ln, re.IGNORECASE):
                return re.split(r"\||CGPA|GPA|Batch|Graduation", ln, maxsplit=1, flags=re.IGNORECASE)[0].strip(" ,-|")
        return None

    @staticmethod
    def _extract_degree(text: str, evidence: list[EvidenceSpan]) -> str | None:
        for ln in text.splitlines():
            low = ln.lower()
            for alias in sorted(DEGREE_ALIASES, key=len, reverse=True):
                if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low):
                    deg = normalize_degree(alias)
                    if deg:
                        evidence.append(EvidenceSpan(field="degree", value=deg, source_snippet=ln.strip()[:160]))
                        return deg
        return None

    @staticmethod
    def _extract_branch(text: str, evidence: list[EvidenceSpan]) -> str | None:
        for ln in text.splitlines():
            low = ln.lower()
            for alias in sorted(BRANCH_ALIASES, key=len, reverse=True):
                if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low):
                    br = normalize_branch(alias)
                    if br:
                        evidence.append(
                            EvidenceSpan(field="branch_or_specialization", value=br, source_snippet=ln.strip()[:160])
                        )
                        return br
        return None

    @staticmethod
    def _extract_graduation_year(text: str, evidence: list[EvidenceSpan]) -> int | None:
        patterns = [
            r"(?:graduation|graduating|batch|class of|expected)\s*(?:year)?\s*[:\-]?\s*(20[2-3]\d)",
            r"20\d{2}\s*[-–to]+\s*(20[2-3]\d)",
        ]
        for ln in text.splitlines():
            for pat in patterns:
                if m := re.search(pat, ln, re.IGNORECASE):
                    yr = int(m.group(1))
                    evidence.append(EvidenceSpan(field="graduation_year", value=str(yr), source_snippet=ln.strip()[:160]))
                    return yr
        return None

    @staticmethod
    def _extract_scores(text: str, evidence: list[EvidenceSpan]) -> tuple[float | None, float | None]:
        cgpa: float | None = None
        pct: float | None = None
        for ln in text.splitlines():
            if cgpa is None:
                m_cg = re.search(r"(?:CGPA|GPA)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)\s*(?:/\s*10(?:\.0)?)?", ln, re.IGNORECASE)
                if m_cg:
                    val = float(m_cg.group(1))
                    if 0.0 <= val <= 10.0:
                        cgpa = round(val, 2)
                        evidence.append(EvidenceSpan(field="cgpa", value=str(cgpa), source_snippet=ln.strip()[:160]))
            if pct is None:
                m_pct = re.search(r"\b(\d{2}(?:\.\d{1,2})?)\s*%", ln)
                if m_pct:
                    pval = float(m_pct.group(1))
                    if 0.0 <= pval <= 100.0:
                        pct = round(pval, 2)
                        evidence.append(EvidenceSpan(field="percentage", value=str(pct), source_snippet=ln.strip()[:160]))
        return cgpa, pct

    @staticmethod
    def _extract_entries(
        lines: list[str],
        field_name: str,
        evidence: list[EvidenceSpan],
    ) -> list[ProjectOrExperienceEntry]:
        entries: list[ProjectOrExperienceEntry] = []
        for ln in lines:
            clean = ln.lstrip("-•* ").strip()
            if not clean:
                continue
            parts = [p.strip() for p in re.split(r"\s[-–:]\s", clean, maxsplit=1)]
            title = parts[0][:120]
            summary = parts[1] if len(parts) > 1 else None
            techs = [c for c, _, _ in find_skills_with_evidence(clean)]
            entries.append(
                ProjectOrExperienceEntry(
                    title=title,
                    summary=summary,
                    technologies=techs,
                    evidence_snippet=clean[:180],
                )
            )
            evidence.append(EvidenceSpan(field=field_name, value=title, source_snippet=clean[:160]))
        return entries

    @staticmethod
    def _extract_bullet_list(lines: list[str], field_name: str, evidence: list[EvidenceSpan]) -> list[str]:
        out: list[str] = []
        for ln in lines:
            clean = ln.lstrip("-•* ").strip()
            if clean:
                out.append(clean)
                evidence.append(EvidenceSpan(field=field_name, value=clean, source_snippet=clean[:160]))
        return out

    @staticmethod
    def _extract_interests(lines: list[str], evidence: list[EvidenceSpan]) -> list[str]:
        out: list[str] = []
        for ln in lines:
            clean = re.sub(r"^(?:interests|areas of interest)\s*:\s*", "", ln, flags=re.IGNORECASE)
            for item in re.split(r"[,;•]", clean):
                tok = item.strip(" -")
                if tok:
                    out.append(tok)
                    evidence.append(EvidenceSpan(field="relevant_interests", value=tok, source_snippet=ln[:160]))
        return deduplicate_skills(out)

    @staticmethod
    def _compute_missing_fields(profile: ExtractedResumeProfile) -> list[str]:
        checks = [
            ("full_name", profile.full_name is not None),
            ("degree", profile.degree is not None),
            ("branch_or_specialization", profile.branch_or_specialization is not None),
            ("graduation_year", profile.graduation_year is not None),
            ("academic_score", profile.cgpa is not None or profile.percentage is not None),
            ("technical_skills", len(profile.technical_skills) > 0),
            ("projects", len(profile.projects) > 0),
            ("experience_or_internships", len(profile.experience) > 0 or len(profile.internships) > 0),
        ]
        return [name for name, ok in checks if not ok]

    def _merge_llm_payload_safely(
        self,
        det: ExtractedResumeProfile,
        payload: dict[str, Any],
        source_text: str,
    ) -> tuple[ExtractedResumeProfile, list[str]]:
        """Validate LLM fields strictly; prevent hallucinated skills absent from source text."""
        warnings: list[str] = []
        data = det.model_dump()

        for scalar_key in ("full_name",):
            if not data[scalar_key] and isinstance(payload.get(scalar_key), str):
                val = payload[scalar_key].strip()
                if val and val.lower() in source_text.lower():
                    data[scalar_key] = val

        if data["degree"] is None and isinstance(payload.get("degree"), str):
            data["degree"] = normalize_degree(payload["degree"])
        if data["branch_or_specialization"] is None and isinstance(payload.get("branch_or_specialization"), str):
            data["branch_or_specialization"] = normalize_branch(payload["branch_or_specialization"])
        if data["graduation_year"] is None and isinstance(payload.get("graduation_year"), int):
            yr = payload["graduation_year"]
            if str(yr) in source_text and 1990 <= yr <= 2035:
                data["graduation_year"] = yr

        # Guardrail against LLM inventing skills not grounded in source_text
        llm_skills = payload.get("technical_skills") or []
        if isinstance(llm_skills, list):
            source_low = source_text.lower()
            grounded_extra: list[str] = []
            for s in llm_skills:
                if not isinstance(s, str):
                    continue
                if s.strip().lower() in source_low:
                    grounded_extra.append(s)
                else:
                    warnings.append(f"Dropped ungrounded LLM skill '{s}' not verified in resume text.")
            data["technical_skills"] = deduplicate_skills(list(data["technical_skills"]) + grounded_extra)

        try:
            merged = ExtractedResumeProfile.model_validate(data)
        except ValidationError as exc:
            warnings.append(f"Partial Pydantic validation fallback applied: {exc.error_count()} errors.")
            merged = det
        merged.missing_fields = self._compute_missing_fields(merged)
        return merged, warnings

    @staticmethod
    def _estimate_confidence(profile: ExtractedResumeProfile) -> float:
        present = 8 - len(profile.missing_fields)
        return round(min(0.95, 0.25 + (present / 8.0) * 0.65), 3)

    @staticmethod
    def _finalize(
        profile: ExtractedResumeProfile,
        mode: str,
        status: str,
        confidence: float,
        warnings: list[str],
    ) -> ExtractionResponse:
        return ExtractionResponse(
            profile=profile,
            normalized_skills=deduplicate_skills(profile.technical_skills),
            extraction_mode=mode,  # type: ignore[arg-type]
            validation_status=status,  # type: ignore[arg-type]
            confidence=confidence,
            warnings=warnings,
        )
