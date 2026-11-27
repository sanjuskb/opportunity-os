"""WS4 & WS5 unit tests for Olostep, Crustdata, SSRF protection, sanitization, retries & caching."""

from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import Settings
from app.integrations.crustdata import CrustdataClient, CrustdataError
from app.integrations.olostep import (
    OlostepClient,
    sanitize_scraped_text,
    validate_public_http_url,
)


def test_ssrf_and_html_sanitization_guards() -> None:
    for bad_url in (
        "file:///etc/passwd",
        "javascript:alert(1)",
        "http://127.0.0.1:8000/admin",
        "http://localhost:54322",
        "http://169.254.169.254/latest/meta-data/",
        "https://10.0.0.5/internal",
        "https://192.168.1.10/router",
        "https://metadata.google.internal/computeMetadata/v1/",
    ):
        with pytest.raises(ValueError):
            validate_public_http_url(bad_url)

    assert (
        validate_public_http_url("https://careers.google.com/jobs")
        == "https://careers.google.com/jobs"
    )

    dirty = '<div onclick="steal()">Hello</div><script>fetch("http://evil")</script><style>body{}</style> World'
    cleaned = sanitize_scraped_text(dirty)
    assert "<script>" not in cleaned
    assert "<style>" not in cleaned
    assert "onclick" not in cleaned
    assert "Hello" in cleaned and "World" in cleaned


@pytest.mark.asyncio
async def test_olostep_client_search_scrape_retry_and_cache() -> None:
    calls = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.headers["Authorization"] == "Bearer olo_live_test_key_123456"
        if request.url.path.endswith("/searches") and calls == 1:
            return httpx.Response(429, json={"error": "rate_limited"})
        if request.url.path.endswith("/searches"):
            return httpx.Response(
                200,
                json={
                    "id": "search-1",
                    "result": {
                        "links": [
                            {
                                "title": "Backend Intern at AcmeTech",
                                "url": "https://acmetech.com/careers/intern",
                                "snippet": "Python FastAPI Bengaluru internship",
                            },
                            {
                                "title": "Bad Internal Target",
                                "url": "http://127.0.0.1:9000/secret",
                                "snippet": "Should be filtered by SSRF check",
                            },
                        ]
                    },
                },
            )
        if request.url.path.endswith("/scrapes"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "title": "ML Fellow at OpenLab",
                        "markdown_content": "<script>alert(1)</script>Work on Python NLP models.",
                    }
                },
            )
        if request.url.path.endswith("/answers"):
            return httpx.Response(
                200,
                json={
                    "result": {
                        "answer": "Verified internship portal.",
                        "sources": ["https://openlab.org"],
                    }
                },
            )
        return httpx.Response(200, json={"id": "ok-1"})

    client = OlostepClient(
        Settings(OLOSTEP_API_KEY="olo_live_test_key_123456"),
        transport=httpx.MockTransport(_handler),
    )

    # First search retries 429 cleanly -> succeeds on attempt 2; SSRF internal link filtered out
    res1 = await client.search("python backend internship")
    assert res1.cached is False
    assert len(res1.items) == 1
    assert res1.items[0].url == "https://acmetech.com/careers/intern"

    # Identical search hits in-memory cache (zero extra HTTP call)
    calls_before_cache = calls
    res2 = await client.search("python backend internship")
    assert res2.cached is True
    assert calls == calls_before_cache

    scrape_res = await client.scrape("https://openlab.org/fellowship")
    assert "<script>" not in scrape_res.markdown
    assert "Python NLP models" in scrape_res.markdown

    ans = await client.answer("Verify OpenLab fellowship")
    assert "Verified" in ans.answer

    crawl_res = await client.crawl("https://openlab.org", max_pages=3)
    assert crawl_res["id"] == "ok-1"
    map_res = await client.map_site("https://openlab.org", search_query="intern")
    assert map_res["id"] == "ok-1"
    batch_res = await client.batch_scrape([{"url": "https://openlab.org/a"}])
    assert batch_res["id"] == "ok-1"
    mon_res = await client.create_monitor("https://openlab.org/careers", frequency="daily")
    assert mon_res["id"] == "ok-1"


@pytest.mark.asyncio
async def test_crustdata_client_enrich_job_search_cache_and_unconfigured_guard() -> None:
    unconf = CrustdataClient(Settings(CRUSTDATA_API_KEY="placeholder-crustdata-api-key"))
    assert unconf.is_configured is False
    with pytest.raises(CrustdataError, match="not configured"):
        await unconf.identify_or_enrich_company(domain="postman.com")

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer crust_live_test_key_12345"
        assert request.headers["x-api-version"] == "2025-11-01"
        body = json.loads(request.content.decode("utf-8"))
        if request.url.path.endswith("/company/enrich"):
            assert body["domains"] == ["postman.com"]
            return httpx.Response(
                200,
                json=[
                    {
                        "company_name": "Postman",
                        "company_website_domain": "postman.com",
                        "industry": "Software Development",
                        "headcount_range": "1001-5000",
                        "funding_stage": "Series D",
                        "headcount_growth_6m_percent": 14.5,
                    }
                ],
            )
        if request.url.path.endswith("/job/search"):
            return httpx.Response(
                200,
                json={"jobs": [{"title": "Software Engineering Intern", "company": "Postman"}]},
            )
        return httpx.Response(404, json={"error": "not found"})

    client = CrustdataClient(
        Settings(CRUSTDATA_API_KEY="crust_live_test_key_12345"),
        transport=httpx.MockTransport(_handler),
    )
    org = await client.identify_or_enrich_company(domain="postman.com")
    assert org is not None
    assert org.name == "Postman"
    assert org.funding_stage == "Series D"
    assert org.hiring_velocity_score == 14.5

    # Repeat call uses cache
    org_cached = await client.identify_or_enrich_company(domain="postman.com")
    assert org_cached is not None
    assert client.usage_stats["cache_hits"] == 1

    jobs = await client.search_jobs("Software Engineering Intern", limit=5)
    assert len(jobs) == 1
