# Opportunity OS — Olostep & Crustdata Integration Specifications

## 1. Provider Roles & Responsibilities

- **Olostep:** Real-time web data infrastructure layer. Executes searches, scrapes, crawls, and automated monitors across university career sites, company portals, and scholarship databases.
- **Crustdata:** B2B company, firmographics, and professional people intelligence. Validates company legitimacy, funding status, headcount growth, tech stacks, and recruiter details.

---

## 2. Olostep Integration Specification

### 2.1 Authentication & Configuration
- **Base URL:** `https://api.olostep.com`
- **Headers:** `Authorization: Bearer <OLOSTEP_API_KEY>`, `Content-Type: application/json`

### 2.2 Documented Endpoints Utilized
1. **Semantic Searches (`POST /v1/searches`):**
   - *Purpose:* Discover fresh, newly published internships across Indian company careers domains.
   - *Payload:* `{"query": "software engineering intern Bengaluru 2026", "max_results": 20}`
2. **Page Scrapes (`POST /v1/scrapes`):**
   - *Purpose:* Extract clean markdown and structured JSON from target job posting URLs.
   - *Payload:* `{"url_to_scrape": "https://example.com/jobs/123", "formats": ["markdown", "structured_json"]}`
3. **Target Crawls (`POST /v1/crawls`):**
   - *Purpose:* Crawl university placement portals or company careers subdomains within strict bounds (`max_pages: 15`).
4. **Scheduled Monitors (`POST /v1/schedules`):**
   - *Purpose:* Monitor high-demand employer careers pages for changes and alert students before deadlines.

### 2.3 Resiliency & Caching
- **Caching:** Redis cache with 6-hour TTL for scraped URLs.
- **Retry Policy:** Exponential backoff (initial 1s, factor 2, max 3 retries) on HTTP 429 or 5xx.

---

## 3. Crustdata Integration Specification

### 3.1 Authentication & Configuration
- **Base URL:** `https://api.crustdata.com`
- **Headers:** `Authorization: Bearer <CRUSTDATA_API_KEY>`, `x-api-version: 2025-11-01`, `Content-Type: application/json`

### 3.2 Documented Endpoints Utilized
1. **Company Entity Resolution (`POST /screener/identify`):**
   - *Purpose:* Map ambiguous company names from scraped listings to a canonical `crustdata_company_id`.
   - *Payload:* `{"query": "Razorpay"}`
2. **Company Firmographic Enrichment (`POST /company/enrich`):**
   - *Purpose:* Verify that the employer is legitimate, verify company headcount, hiring trends, and tech stack.
   - *Payload:* `{"company_id": "crust_12345"}`
   - *Response Fields:* `headcount`, `funding_stage`, `tech_stack`, `verified_domain`.
3. **People Search (`POST /screener/person/search`):**
   - *Purpose:* Discover verified University Recruiters and Talent Acquisition contacts at the hiring organization for student networking.
   - *Payload:* `{"company_id": "crust_12345", "titles": ["University Recruiter", "Campus Talent Acquisition"]}`

---

## 4. Provider Adapter Pattern

Both providers are wrapped in abstract base classes within `apps/api/app/integrations/`:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class OpportunitySearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    async def scrape(self, url: str) -> Dict[str, Any]: ...
```
Never hardcode credentials or make live provider calls during test execution. Mock adapters are supplied for CI/CD.
