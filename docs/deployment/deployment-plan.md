# Opportunity OS — Deployment & Environment Variable Strategy

## 1. Multi-Stage Deployment Architecture

| Tier | Component | Hosting Environment | Scalability Strategy |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 15+ Web App | Vercel / Cloudflare Pages / Container | Edge-cached static assets, SSR on demand |
| **Backend API** | FastAPI Service | AWS ECS / Render / Railway | Horizontal scaling with stateless replicas |
| **Database** | PostgreSQL 16 + pgvector | Supabase Managed Cloud | Connection pooling via Supabase pooler |
| **Task Queue & Cache** | Redis 7 + ARQ | Upstash / Redis Cloud | Low-latency in-memory queue |
| **Workers** | Playwright & Agent Workers | Dedicated Container Worker Instances | Isolated compute instances with browser binary support |

---

## 2. Environment Variable Configuration Plan

Environment variables are partitioned into safe logical groups. All secrets are populated via secure secrets managers (GitHub Secrets, Supabase Dashboard, Cloud Provider Vault).

```text
# Logical Groupings:
1. Core Runtime: ENVIRONMENT, LOG_LEVEL, DEBUG
2. Networking: FRONTEND_PORT, BACKEND_PORT, NEXT_PUBLIC_API_BASE_URL, CORS_ORIGINS
3. Supabase: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, DATABASE_URL
4. Redis: REDIS_URL, REDIS_HOST, REDIS_PORT
5. AI Models: GEMINI_API_KEY, GEMINI_MODEL, GEMINI_LIVE_WEBSOCKET_URL
6. Web Intel: OLOSTEP_API_KEY, OLOSTEP_API_BASE_URL
7. Firmographics: CRUSTDATA_API_KEY, CRUSTDATA_API_BASE_URL, CRUSTDATA_API_VERSION
8. Browser Automation: PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS
```

---

## 3. Health Checks & Rollback Strategy

- **API Health Endpoint:** `GET /api/v1/health` verifies database connectivity and Redis reachability before traffic routing.
- **Zero-Downtime Deployments:** Blue/Green deployment or rolling updates with automated rollback if the health endpoint fails for 3 consecutive checks.
