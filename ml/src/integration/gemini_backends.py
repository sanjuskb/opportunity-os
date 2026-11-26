"""
Optional Google Gemini & external API integration helpers for NexteRaS ML.

Enforces zero hardcoded secrets, rejects placeholder environment values,
and cleanly degrades or reports CREDENTIALS_REQUIRED when unconfigured.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from ml.src.extraction.extractor import StructuredLLMBackend
from ml.src.multilingual.service import TranslationFallbackBackend

logger = logging.getLogger("nexteras.ml.external")

PLACEHOLDER_MARKERS = ("placeholder-", "your-", "changeme", "<your", "dummy")


def is_real_credential(value: str | None) -> bool:
    """Return True only when an env var looks populated and non-placeholder."""
    if not value:
        return False
    stripped = value.strip()
    if len(stripped) < 12:
        return False
    low = stripped.lower()
    return not any(marker in low for marker in PLACEHOLDER_MARKERS)


def get_external_service_status(env: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """
    Audit configured external credentials strictly without ever logging secret values.
    """
    source = env if env is not None else os.environ
    checks = [
        ("gemini_api", "GEMINI_API_KEY", True, "Gemini Flash JSON extraction / translation fallback / Live voice"),
        ("olostep_api", "OLOSTEP_API_KEY", True, "Live opportunity discovery & scraping (backend teammate domain)"),
        ("crustdata_api", "CRUSTDATA_API_KEY", True, "Company firmographics enrichment (backend teammate domain)"),
        ("supabase_url", "NEXT_PUBLIC_SUPABASE_URL", True, "Supabase project REST/Auth host"),
        ("supabase_service_key", "SUPABASE_SERVICE_ROLE_KEY", True, "Server-side Supabase/pgvector writes"),
        ("database_url", "DATABASE_URL", True, "PostgreSQL + pgvector persistence"),
        ("redis_url", "REDIS_URL", False, "Redis / ARQ background ML queue"),
        ("huggingface_hub_token", "HF_TOKEN", False, "Optional higher Hub download rate limits (public models work without it)"),
    ]
    report: dict[str, dict[str, Any]] = {}
    for service_key, var_name, required_for_prod, purpose in checks:
        raw_val = source.get(var_name)
        configured = (
            bool(raw_val and ("postgresql" in raw_val or "redis://" in raw_val))
            if var_name in {"DATABASE_URL", "REDIS_URL"}
            else is_real_credential(raw_val)
        )
        if var_name == "NEXT_PUBLIC_SUPABASE_URL" and raw_val:
            configured = raw_val.startswith("https://") and "your-project-ref" not in raw_val
        report[service_key] = {
            "env_var": var_name,
            "configured": configured,
            "status": "CONFIGURED" if configured else "CREDENTIALS_REQUIRED",
            "required_for_cloud_production": required_for_prod,
            "purpose": purpose,
        }
    return report


class GeminiCredentialsMissingError(RuntimeError):
    """Raised cleanly when live Gemini API calls are attempted without GEMINI_API_KEY."""


class GeminiStructuredLLMBackend(StructuredLLMBackend):
    """Pluggable Gemini JSON extractor backend via REST API (zero SDK lock-in, no hardcoded key)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        resolved = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")
        self.api_key = resolved.strip() if is_real_credential(resolved) else ""
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def extract_json(self, resume_text: str) -> str:
        if not self.is_configured:
            raise GeminiCredentialsMissingError(
                "BLOCKED — CREDENTIALS REQUIRED: GEMINI_API_KEY is unset or still a placeholder."
            )
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        prompt = (
            "Extract strictly facts present in the resume text below into JSON with keys "
            "full_name, degree, branch_or_specialization, graduation_year, technical_skills. "
            "Never invent unmentioned skills.\n\nResume:\n" + resume_text[:12000]
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0},
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return str(data["candidates"][0]["content"]["parts"][0]["text"])


class GeminiTranslationFallbackBackend(TranslationFallbackBackend):
    """Pluggable Gemini translation normalizer preserving technical terms verbatim."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_seconds: float = 12.0,
    ) -> None:
        resolved = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")
        self.api_key = resolved.strip() if is_real_credential(resolved) else ""
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def normalize_to_english(self, text: str, source_locale: str, preserved_terms: list[str]) -> str:
        if not self.is_configured:
            raise GeminiCredentialsMissingError(
                "BLOCKED — CREDENTIALS REQUIRED: GEMINI_API_KEY is unset or still a placeholder."
            )
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        prompt = (
            f"Translate this student career query from '{source_locale}' to concise English for job search retrieval. "
            f"Keep these technical terms verbatim: {', '.join(preserved_terms) or 'none'}.\n\nQuery: {text[:2000]}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.0}}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
