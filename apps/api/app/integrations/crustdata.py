"""Crustdata Company, Firmographic Enrichment & Active Hiring Job Search Client."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, settings

logger = logging.getLogger("opportunity_os.integrations.crustdata")

_PLACEHOLDER_MARKERS = ("placeholder-", "your-", "<your", "changeme", "dummy")


class CrustdataError(RuntimeError):
    """Typed Crustdata API failure."""

    def __init__(
        self, message: str, *, status_code: int | None = None, retryable: bool = False
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class NormalizedCompanyIntelligence(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    headcount_range: str | None = None
    funding_stage: str | None = None
    description: str | None = None
    hiring_velocity_score: float | None = None
    is_verified: bool = True
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class CrustdataClient:
    """Async Crustdata client supporting search, identify, enrich, job search & caching."""

    def __init__(
        self,
        app_settings: Settings | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = app_settings or settings
        self._transport = transport
        self._cache: dict[str, tuple[float, Any]] = {}
        self.usage_stats: dict[str, int] = {"requests": 0, "cache_hits": 0, "errors": 0}

    @property
    def is_configured(self) -> bool:
        key = self._settings.CRUSTDATA_API_KEY.strip()
        if len(key) < 12:
            return False
        low = key.lower()
        return not any(marker in low for marker in _PLACEHOLDER_MARKERS)

    def _base_url(self) -> str:
        return self._settings.CRUSTDATA_API_BASE_URL.strip().rstrip("/")

    def _cache_key(self, endpoint: str, payload: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps({"endpoint": endpoint, "payload": payload}, sort_keys=True).encode("utf-8")
        ).hexdigest()

    async def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        *,
        cache_ttl_seconds: int = 3600,
        max_retries: int = 2,
    ) -> Any:
        if not self.is_configured:
            raise CrustdataError(
                "CRUSTDATA_API_KEY is not configured.", status_code=503, retryable=False
            )

        key = self._cache_key(endpoint, payload) if cache_ttl_seconds > 0 else ""
        if key and key in self._cache:
            exp, cached_val = self._cache[key]
            if time.monotonic() < exp:
                self.usage_stats["cache_hits"] += 1
                return cached_val

        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self._settings.CRUSTDATA_API_KEY}",
            "Content-Type": "application/json",
            "x-api-version": self._settings.CRUSTDATA_API_VERSION,
        }

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=25.0, transport=self._transport) as client:
            for attempt in range(max_retries + 1):
                try:
                    self.usage_stats["requests"] += 1
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if resp.status_code >= 400:
                        self.usage_stats["errors"] += 1
                        raise CrustdataError(
                            f"Crustdata API returned HTTP {resp.status_code}",
                            status_code=resp.status_code,
                            retryable=resp.status_code in {429, 500, 502, 503, 504},
                        )
                    data = resp.json()
                    if key:
                        self._cache[key] = (time.monotonic() + cache_ttl_seconds, data)
                    return data
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    self.usage_stats["errors"] += 1
                    raise CrustdataError(
                        f"Crustdata transport error: {type(exc).__name__}",
                        status_code=502,
                        retryable=True,
                    ) from exc

        raise CrustdataError(
            f"Crustdata request failed: {last_exc}", status_code=502, retryable=True
        )

    async def identify_or_enrich_company(
        self,
        *,
        domain: str | None = None,
        company_name: str | None = None,
    ) -> NormalizedCompanyIntelligence | None:
        if not domain and not company_name:
            raise ValueError("Either domain or company_name is required.")

        if domain:
            raw = await self._post("/company/enrich", {"domains": [domain.strip().lower()]})
        else:
            raw = await self._post(
                "/company/search",
                {"search": {"query": company_name}, "limit": 5},
            )

        records: list[dict[str, Any]] = []
        if isinstance(raw, list):
            records = [r for r in raw if isinstance(r, dict)]
        elif isinstance(raw, dict):
            for k in ("companies", "data", "results"):
                val = raw.get(k)
                if isinstance(val, list):
                    records = [r for r in val if isinstance(r, dict)]
                    break
            if not records and (raw.get("company_name") or raw.get("name")):
                records = [raw]

        if not records:
            return None

        top = records[0]
        resolved_name = str(top.get("company_name") or top.get("name") or company_name or domain)
        resolved_domain = (
            str(top.get("company_website_domain") or top.get("domain") or domain or "").strip()
            or None
        )
        headcount = top.get("headcount_range") or (
            str(top.get("employee_count")) if top.get("employee_count") is not None else None
        )
        funding = top.get("funding_stage") or top.get("last_funding_round_type")
        industry = top.get("industry") or (
            ", ".join(top["industries"][:2]) if isinstance(top.get("industries"), list) else None
        )
        vel = top.get("hiring_velocity_score") or top.get("headcount_growth_6m_percent")

        return NormalizedCompanyIntelligence(
            name=resolved_name[:255],
            domain=resolved_domain[:255] if resolved_domain else None,
            industry=str(industry)[:200] if industry else None,
            headcount_range=str(headcount)[:100] if headcount else None,
            funding_stage=str(funding)[:120] if funding else None,
            description=str(top.get("description") or "")[:2000] or None,
            hiring_velocity_score=float(vel) if isinstance(vel, int | float) else None,
            is_verified=True,
            raw_payload=top,
        )

    async def search_jobs(self, keyword: str, *, limit: int = 10) -> list[dict[str, Any]]:
        raw = await self._post(
            "/job/search",
            {
                "filters": {
                    "op": "and",
                    "conditions": [{"field": "job_details.title", "type": "[.]", "value": keyword}],
                },
                "limit": max(1, min(limit, 50)),
            },
        )
        if isinstance(raw, list):
            return [r for r in raw if isinstance(r, dict)]
        if isinstance(raw, dict):
            for k in ("jobs", "data", "results"):
                val = raw.get(k)
                if isinstance(val, list):
                    return [r for r in val if isinstance(r, dict)]
        return []
