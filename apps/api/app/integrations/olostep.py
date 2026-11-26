"""Olostep REST v1 Web Intelligence Client (Search, Scrape, Answers, Crawl, Maps, Batch, Monitors)."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import logging
import re
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, settings

logger = logging.getLogger("opportunity_os.integrations.olostep")

_PLACEHOLDER_MARKERS = ("placeholder-", "your-", "<your", "changeme", "dummy")
_BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "metadata"}
_SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript)\b[^>]*>.*?</\1>", re.I | re.S)
_EVENT_ATTR_RE = re.compile(r"\son[a-z]+\s*=\s*(['\"]).*?\1", re.I)


class OlostepError(RuntimeError):
    """Typed integration failure classified cleanly without leaking credentials."""

    def __init__(
        self, message: str, *, status_code: int | None = None, retryable: bool = False
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def sanitize_scraped_text(raw: str, *, max_chars: int = 25_000) -> str:
    """Strip active script/style blocks and inline HTML event attributes."""
    cleaned = _SCRIPT_STYLE_RE.sub(" ", raw or "")
    cleaned = _EVENT_ATTR_RE.sub("", cleaned)
    return cleaned.strip()[:max_chars]


def _is_disallowed_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def validate_public_http_url(url: str, *, resolve_dns: bool = False) -> str:
    """Block SSRF schemes, private/loopback IP ranges, and cloud metadata endpoints."""
    raw = (url or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Disallowed URL scheme or missing host: {raw!r}")

    host = (parsed.hostname or "").strip().lower()
    if (
        not host
        or host in _BLOCKED_HOSTNAMES
        or host.endswith(".local")
        or host.endswith(".internal")
    ):
        raise ValueError(f"Blocked internal/metadata hostname: {host!r}")

    try:
        ip_literal = ipaddress.ip_address(host)
    except ValueError:
        ip_literal = None

    if ip_literal is not None and _is_disallowed_ip(ip_literal):
        raise ValueError(f"Blocked private or loopback IP target: {host!r}")

    if resolve_dns and ip_literal is None:
        try:
            infos = socket.getaddrinfo(
                host, parsed.port or (443 if parsed.scheme == "https" else 80)
            )
            for _fam, _sock, _proto, _canon, sockaddr in infos:
                addr_ip = ipaddress.ip_address(sockaddr[0])
                if _is_disallowed_ip(addr_ip):
                    raise ValueError(f"Hostname resolved to disallowed internal IP: {addr_ip}")
        except socket.gaierror as exc:
            raise ValueError(f"Unable to resolve target host {host!r}") from exc

    return raw


class OlostepSearchItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    markdown: str = ""


class OlostepSearchResponse(BaseModel):
    query: str
    items: list[OlostepSearchItem] = Field(default_factory=list)
    cached: bool = False
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class OlostepScrapeResponse(BaseModel):
    url: str
    markdown: str = ""
    title: str = ""
    json_data: dict[str, Any] = Field(default_factory=dict)
    cached: bool = False


class OlostepAnswerResponse(BaseModel):
    task: str
    answer: str = ""
    sources: list[str] = Field(default_factory=list)
    structured_json: dict[str, Any] = Field(default_factory=dict)


class OlostepClient:
    """Async Olostep API v1 client supporting caching, retries, rate telemetry & SSRF checks."""

    def __init__(
        self,
        app_settings: Settings | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = app_settings or settings
        self._transport = transport
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self.usage_stats: dict[str, int] = {"requests": 0, "cache_hits": 0, "errors": 0}

    @property
    def is_configured(self) -> bool:
        key = self._settings.OLOSTEP_API_KEY.strip()
        if len(key) < 12:
            return False
        low = key.lower()
        return not any(marker in low for marker in _PLACEHOLDER_MARKERS)

    def _base_url(self) -> str:
        base = self._settings.OLOSTEP_API_BASE_URL.strip().rstrip("/")
        if base.endswith("/v1"):
            return base
        return f"{base}/v1"

    def _cache_key(self, endpoint: str, payload: dict[str, Any]) -> str:
        raw = json.dumps({"endpoint": endpoint, "payload": payload}, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        payload: dict[str, Any] | None = None,
        cache_ttl_seconds: int = 900,
        max_retries: int = 2,
    ) -> tuple[dict[str, Any], bool]:
        if not self.is_configured:
            raise OlostepError(
                "OLOSTEP_API_KEY is not configured.", status_code=503, retryable=False
            )

        key = (
            self._cache_key(endpoint, payload or {})
            if method.upper() == "POST" and cache_ttl_seconds > 0
            else ""
        )
        if key and key in self._cache:
            exp, cached_data = self._cache[key]
            if time.monotonic() < exp:
                self.usage_stats["cache_hits"] += 1
                return cached_data, True

        url = f"{self._base_url()}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self._settings.OLOSTEP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=30.0, transport=self._transport) as client:
            for attempt in range(max_retries + 1):
                try:
                    self.usage_stats["requests"] += 1
                    resp = await client.request(method, url, headers=headers, json=payload)
                    if resp.status_code in {429, 500, 502, 503, 504} and attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if resp.status_code >= 400:
                        self.usage_stats["errors"] += 1
                        raise OlostepError(
                            f"Olostep API returned HTTP {resp.status_code}",
                            status_code=resp.status_code,
                            retryable=resp.status_code in {429, 500, 502, 503, 504},
                        )
                    data = resp.json()
                    parsed: dict[str, Any] = data if isinstance(data, dict) else {"data": data}
                    if key:
                        self._cache[key] = (time.monotonic() + cache_ttl_seconds, parsed)
                    return parsed, False
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    self.usage_stats["errors"] += 1
                    raise OlostepError(
                        f"Olostep transport error: {type(exc).__name__}",
                        status_code=502,
                        retryable=True,
                    ) from exc

        raise OlostepError(f"Olostep request failed: {last_exc}", status_code=502, retryable=True)

    async def search(
        self, query: str, *, include_urls: list[str] | None = None
    ) -> OlostepSearchResponse:
        body: dict[str, Any] = {"query": query}
        if include_urls:
            for u in include_urls:
                validate_public_http_url(u)
            body["urls"] = include_urls

        data, cached = await self._request("POST", "/searches", payload=body)
        raw_res = data.get("result")
        raw_result: dict[str, Any] = raw_res if isinstance(raw_res, dict) else data
        candidates = (
            raw_result.get("links")
            or raw_result.get("results")
            or data.get("results")
            or data.get("organic")
            or []
        )
        items: list[OlostepSearchItem] = []
        if isinstance(candidates, list):
            for entry in candidates:
                if not isinstance(entry, dict):
                    continue
                target_url = str(entry.get("url") or entry.get("link") or "").strip()
                if not target_url:
                    continue
                try:
                    validate_public_http_url(target_url)
                except ValueError:
                    continue
                items.append(
                    OlostepSearchItem(
                        title=sanitize_scraped_text(
                            str(entry.get("title") or target_url), max_chars=240
                        ),
                        url=target_url,
                        snippet=sanitize_scraped_text(
                            str(entry.get("snippet") or entry.get("description") or ""),
                            max_chars=1000,
                        ),
                        markdown=sanitize_scraped_text(
                            str(entry.get("markdown") or ""), max_chars=4000
                        ),
                    )
                )

        return OlostepSearchResponse(
            query=query,
            items=items,
            cached=cached,
            raw_metadata={"id": data.get("id"), "status": data.get("status")},
        )

    async def scrape(
        self, target_url: str, *, formats: list[str] | None = None
    ) -> OlostepScrapeResponse:
        safe_url = validate_public_http_url(target_url)
        body = {"url_to_scrape": safe_url, "formats": formats or ["markdown"]}
        data, cached = await self._request("POST", "/scrapes", payload=body)
        raw_res = data.get("result")
        res: dict[str, Any] = raw_res if isinstance(raw_res, dict) else data
        markdown = sanitize_scraped_text(
            str(res.get("markdown_content") or res.get("markdown") or "")
        )
        return OlostepScrapeResponse(
            url=safe_url,
            markdown=markdown,
            title=sanitize_scraped_text(str(res.get("title") or ""), max_chars=250),
            json_data=raw_json if isinstance((raw_json := res.get("json_content")), dict) else {},
            cached=cached,
        )

    async def answer(
        self, task: str, *, json_format: dict[str, Any] | None = None
    ) -> OlostepAnswerResponse:
        body: dict[str, Any] = {"task": task}
        if json_format is not None:
            body["json_format"] = json_format
        data, _ = await self._request("POST", "/answers", payload=body)
        raw_res = data.get("result")
        res: dict[str, Any] = raw_res if isinstance(raw_res, dict) else data
        raw_sources = res.get("sources") or []
        sources = [str(s) for s in raw_sources if isinstance(s, str)]
        raw_json = res.get("json_content")
        return OlostepAnswerResponse(
            task=task,
            answer=sanitize_scraped_text(str(res.get("answer") or res.get("result") or "")),
            sources=sources,
            structured_json=raw_json if isinstance(raw_json, dict) else {},
        )

    async def crawl(self, start_url: str, *, max_pages: int = 10) -> dict[str, Any]:
        safe_url = validate_public_http_url(start_url)
        data, _ = await self._request(
            "POST",
            "/crawls",
            payload={"start_url": safe_url, "max_pages": max(1, min(max_pages, 50))},
        )
        return data

    async def map_site(self, url: str, *, search_query: str | None = None) -> dict[str, Any]:
        safe_url = validate_public_http_url(url)
        body: dict[str, Any] = {"url": safe_url}
        if search_query:
            body["search_query"] = search_query
        data, _ = await self._request("POST", "/maps", payload=body)
        return data

    async def batch_scrape(self, items: list[dict[str, str]]) -> dict[str, Any]:
        clean_items: list[dict[str, str]] = []
        for idx, item in enumerate(items[:100]):
            safe_url = validate_public_http_url(item["url"])
            clean_items.append(
                {"custom_id": str(item.get("custom_id") or f"item-{idx}"), "url": safe_url}
            )
        data, _ = await self._request("POST", "/batches", payload={"items": clean_items})
        return data

    async def create_monitor(self, url: str, *, frequency: str = "daily") -> dict[str, Any]:
        safe_url = validate_public_http_url(url)
        data, _ = await self._request(
            "POST", "/monitors", payload={"url": safe_url, "frequency": frequency}
        )
        return data
