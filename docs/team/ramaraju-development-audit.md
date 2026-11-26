# Opportunity OS — Ramaraju Development Readiness Audit

**Prepared For:** Sanjeeth (Backend, Database & AI Integration Lead — `ramaraju` branch)  
**Repository:** `https://github.com/sanjuskb/opportunity-os.git`  
**Local Path:** `C:\Users\sanje\Documents\GitHub\opportunity-os`  
**Audited Branch:** `ramaraju` (`2242d24d1a249abc85cde3d5986a2ad49bb066f7`)  
**Audit Date:** 2026-11-26  
**Scope:** Inspection-only readiness audit (no code, schema, dependency, or branch modifications performed).

---

## 1. Executive Summary

The `ramaraju` branch is clean, properly tracked to `origin/ramaraju`, and sits at the Phase 5 architecture baseline (`2242d24`). While architectural specifications, cross-team contracts, Dockerfiles, and the initial PostgreSQL/pgvector migration are in place, **the FastAPI backend (`apps/api`) is currently a minimal 2-endpoint skeleton** (`/api/v1/health` and a stub `GET /api/v1/opportunities` returning `[]`).

Key findings across the repository:
1. **Branch Topology:** `ramaraju` (`2242d24`) is `0` commits ahead and `13` commits behind `origin/develop` (`bfea709`). All 13 commits on `origin/develop` are Sanjay's frontend/3D/rebranding updates (`apps/web/`, `docs/execution/`, `docs/qa/`, `packages/design-tokens/`, `packages/shared-config/`). Shared API contracts (`packages/shared-types`, `packages/api-client`) and `apps/api/` / `supabase/` are identical between `ramaraju` and `origin/develop`.
2. **ML Subsystem (`origin/ml`):** `ramaraju` only has the Phase 5 `ml/` scaffold (`train.py`, `evaluate.py`, `baseline_matching.yaml`). Full ML inference, MiniLM fine-tuning, and FastAPI ML route adapters (`apps/api/app/api/v1/ml.py`, `apps/api/app/ml/adapter.py`, `apps/api/app/schemas/ml.py`, and `ml/src/...`) already exist on `origin/ml` (`f14190d`), which also branched from `2242d24`.
3. **Database Gaps:** `supabase/migrations/20261123000001_initial_schema.sql` defines 25 tables and enables `pgvector`, but has **incomplete RLS policies** (9 of 10 RLS-enabled tables have zero policies; `opportunities` has a policy without `ENABLE ROW LEVEL SECURITY`; `profiles` lacks an `auth.users` signup trigger/INSERT policy), a **vector dimension mismatch** (`vector(768)` for Gemini `text-embedding-004` vs `384` for `all-MiniLM-L6-v2`), and a **Docker init incompatibility** (raw `pgvector/pgvector:pg16` in `docker-compose.yml` lacks Supabase's `auth.users` schema).

---

## 2. Git & Repository Audit

### 2.1 Current State (`ramaraju`)
- **Active Branch:** `ramaraju` tracking `origin/ramaraju`
- **Working Tree:** Clean (`nothing to commit, working tree clean`)
- **Remote (`origin`):** `https://github.com/sanjuskb/opportunity-os.git` (fetch & push)
- **Current Commit:** `2242d24d1a249abc85cde3d5986a2ad49bb066f7` — `docs(repo): add branch audit report, git workflow, and preserve 3D discovery research`

### 2.2 Branch Comparison (`ramaraju` vs `origin/develop` & `origin/ml`)
- **Merge-base (`ramaraju` & `origin/develop`):** `2242d24d1a249abc85cde3d5986a2ad49bb066f7`
- **Merge-base (`ramaraju` & `origin/ml`):** `2242d24d1a249abc85cde3d5986a2ad49bb066f7`
- **Unique to `ramaraju` (`origin/develop..ramaraju`):** 0 commits
- **In `origin/develop` missing from `ramaraju` (`ramaraju..origin/develop`):** 13 commits (111 files changed, `+407 / -13863` in reverse diff):
  - `bfea709` `feat(branding): rebrand frontend as NexteRaS (#6)`
  - `d641288` `docs(qa): add frontend branch integration and verification report (#5)`
  - `52ffca3` `Merge pull request #4 from sanjuskb/sanju`
  - `d5c2466` `fix(ci): repair .gitignore to track apps/web/src/lib, add favicon icon, and complete final repository audit`
  - `d69e2e4` `refactor(agent-control): redesign monitoring panel with horizontal tabs...`
  - `5e34a70` `feat(agent-control): implement interactive Agent Control Center, VORTEX network graph, telemetry stream, and inspector`
  - `5bed8f3`, `8bb35e0`, `730b932`, `a9554e1`, `5addd2e`, `0ff0bfd`, `ad17cb9` (frontend UI, 3D robot, landing/dashboard pages)
- **Diff in shared/backend paths (`ramaraju..origin/develop -- packages/ apps/api/ supabase/ ml/`):**
  - Only `packages/design-tokens/` and `packages/shared-config/` differ.
  - `apps/api/`, `supabase/`, `ml/`, `packages/shared-types/`, and `packages/api-client/` are **100% identical** between `ramaraju` and `origin/develop`.

---

## 3. Existing Architecture & Backend Inspection

### 3.1 Existing Backend Components (`apps/api/`)
- **Project Config (`apps/api/pyproject.toml`):**
  - Python `>=3.12`, managed via `uv` (`apps/api/uv.lock` present), `hatchling` build backend.
  - Core deps: `fastapi>=0.115.0`, `uvicorn[standard]>=0.32.0`, `pydantic>=2.9.0`, `pydantic-settings>=2.6.0`, `httpx>=0.27.0`, `sqlalchemy>=2.0.35`, `asyncpg>=0.29.0`, `redis>=5.1.0`, `websockets>=13.1`.
  - Optional `ai` group: `google-genai>=0.1.1`, `langgraph>=0.2.35`, `sentence-transformers>=3.1.0`.
  - Optional `automation` group: `playwright>=1.47.0`.
  - Optional `dev` group: `pytest>=8.3.0`, `pytest-asyncio>=0.24.0`, `ruff>=0.7.0`, `mypy>=1.12.0` (`strict = true`).
- **App Factory (`apps/api/app/main.py`):**
  - `create_application()` configures FastAPI (`docs_url="/docs"`, `redoc_url="/redoc"`), `CORSMiddleware`, and mounts `v1_router` at `/api`.
- **Settings (`apps/api/app/core/config.py`):**
  - `Settings(BaseSettings)` loads `.env` with `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL`, `APP_NAME`, `CORS_ORIGINS`, `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `OLOSTEP_API_KEY`, `CRUSTDATA_API_KEY`.
- **Routes (`apps/api/app/api/v1/router.py`):**
  - `GET /api/v1/health` -> returns `HealthResponse` (`status="healthy"`, `version="0.1.0"`, `environment`).
  - `GET /api/v1/opportunities` -> **stub** returning `[]`.
- **Schemas (`apps/api/app/schemas/common.py`):**
  - `HealthResponse`, `OpportunityResponse`, `EligibilityCheckRequest`, `EligibilityCheckResponse` (all currently `snake_case`, without `to_camel` alias generator).
- **Tests (`apps/api/tests/unit/test_sanity.py`):**
  - 2 unit tests (`test_settings_loaded`, `test_health_endpoint`). No integration or e2e tests exist on `ramaraju`.

### 3.2 Missing Backend Components (`apps/api/app/`)
All domain packages exist only as empty `__init__.py` placeholders (`11`–`75` bytes each):
- `app/models/` — No SQLAlchemy ORM models.
- `app/repositories/` — No database repositories or async session manager.
- `app/services/` — No business logic services (users, opportunities, eligibility, resumes, approvals, notifications).
- `app/core/` — Missing Supabase JWT verification (`SUPABASE_JWT_SECRET`), RFC 7807 `ProblemDetails` exception handlers, Redis client, and logging/telemetry setup.
- `app/agents/` — No LangGraph state machines (9 workflows specified in `docs/agents/langgraph-workflows.md`).
- `app/voice/` — No Gemini Live WebSocket proxy (`/api/v1/voice/stream`) or ephemeral ticket issuer (`POST /api/v1/voice/tickets`).
- `app/integrations/` — No Olostep or Crustdata HTTP adapters.
- `app/tasks/` — No ARQ background worker (`Dockerfile.worker` references `python -m app.tasks.worker`, which does not exist yet).
- `app/ml/` — No ML adapter on `ramaraju` (implemented on `origin/ml` via `apps/api/app/ml/adapter.py`, `apps/api/app/api/v1/ml.py`, `apps/api/app/schemas/ml.py`).
- Playwright browser automation — Not implemented (`playwright` is in optional dependencies only).

---

## 4. Database Inspection (`supabase/`)

### 4.1 What Exists
- **Supabase Config (`supabase/config.toml`):**
  - API port `54321`, DB port `54322` (PostgreSQL 16), Auth enabled (`site_url = "http://localhost:3000"`, `jwt_expiry = 3600`), Storage enabled (`10MiB` limit).
- **Initial Migration (`supabase/migrations/20261123000001_initial_schema.sql`):**
  - Extensions: `uuid-ossp`, `vector` (`pgvector`).
  - **25 tables defined:** `profiles`, `student_profiles`, `education`, `skills`, `user_preferences`, `career_passports`, `opportunities`, `opportunity_sources`, `opportunity_eligibility`, `opportunity_embeddings` (`vector(768)`), `saved_opportunities`, `applications`, `resumes`, `resume_versions`, `resume_customizations`, `agent_sessions`, `agent_events`, `approval_requests`, `browser_execution_logs`, `conversations`, `conversation_messages`, `voice_sessions`, `notifications`, `opportunity_monitors`, `analytics_events`.
  - **Indexes:** `idx_opportunities_type`, `idx_opportunities_created`, `idx_approval_requests_status`, `idx_embeddings_vector` (`ivfflat` with `vector_cosine_ops`, `lists = 100`).
- **Seed Data (`supabase/seed/seed.sql`):**
  - 9 skills (`Python`, `TypeScript`, `React`, `FastAPI`, `SQL`, `Machine Learning`, `Data Analysis`, `Docker`, `Communication`).
  - 2 sample opportunities (`AI Research Intern` at AI4Bharat, `Software Engineering Intern - Frontend` at Postman India).
- **Database Connection Code:** None in `apps/api/` yet.

### 4.2 Database Gaps & Issues Requiring Fixes
1. **Incomplete RLS Policies:**
   - 10 tables have `ENABLE ROW LEVEL SECURITY`, but **9 of them** (`student_profiles`, `user_preferences`, `career_passports`, `saved_opportunities`, `applications`, `resumes`, `approval_requests`, `conversations`, `notifications`) have **zero policies**, blocking all non-service-role access.
   - `opportunities` has a `CREATE POLICY` statement without `ALTER TABLE public.opportunities ENABLE ROW LEVEL SECURITY;`.
   - The remaining 14 tables (`education`, `skills`, `opportunity_sources`, `opportunity_eligibility`, `opportunity_embeddings`, `resume_versions`, `resume_customizations`, `agent_sessions`, `agent_events`, `browser_execution_logs`, `conversation_messages`, `voice_sessions`, `opportunity_monitors`, `analytics_events`) have neither RLS enabled nor policies.
2. **Missing Auth Trigger & Profile Insert Policy:** `profiles.id` references `auth.users(id)`, but there is no `handle_new_user()` trigger on `auth.users` and no `INSERT` policy on `profiles`.
3. **Missing Unique Constraint for Duplicate Application Guard:** `docs/agents/browser-execution.md` specifies a unique constraint on `(user_id, opportunity_id)` in `applications`, which is absent in `20261123000001_initial_schema.sql` (only `saved_opportunities` has `UNIQUE(user_id, opportunity_id)`).
4. **Vector Dimension Mismatch:** `opportunity_embeddings.embedding` is `vector(768)` (for Gemini `text-embedding-004`), whereas `ml/model_configs/baseline_matching.yaml` uses `all-MiniLM-L6-v2` (`384` dimensions). Must either standardize on one dimension or add a dedicated `minilm_embedding vector(384)` column/table.
5. **Missing `updated_at` Triggers & `opportunity_eligibility` Unique Constraint:** No `updated_at` auto-update triggers exist.

---

## 5. Frontend Integration Requirements

Based on `docs/api/endpoint-specification.md`, `docs/architecture/FRONTEND_API_INTEGRATION_SPEC.md`, `docs/architecture/CROSS_TEAM_CONTRACT_REGISTER.md`, `packages/shared-types/src/index.ts`, and `packages/api-client/src/index.ts`:

- **Wire Format & Serialization:**
  - All JSON payloads must serialize to `camelCase` (`model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)`), while Python internals use `snake_case`.
  - All errors must return **RFC 7807** `Content-Type: application/problem+json` (`type`, `title`, `status`, `detail`, `instance`, `invalidParams`).
  - Critical mutations (`POST /applications`, `POST /agents/approvals/{id}/decision`, `POST /resumes/{id}/tailor`) must support `Idempotency-Key` headers.
- **Required REST Endpoints (`/api/v1`):**
  - **Users & Profile:** `GET /users/me`, `PUT /users/me`, `GET /users/me/student-profile`, `PUT /users/me/student-profile` (note: `packages/api-client` also calls `/users/me/profile` — align route naming with frontend).
  - **Career Passport:** `GET /career-passport`, `POST /career-passport/items`, `DELETE /career-passport/items/{id}`.
  - **Opportunities:** `GET /opportunities` (cursor-based pagination: `cursor`, `limit`, `types`, `batch`, `remote`, `minStipend`, `query` returning `{ items, nextCursor, hasMore, totalCount }`), `GET /opportunities/{id}`, `POST /opportunities/discover`, `POST /opportunities/{id}/save`.
  - **Eligibility:** `POST /eligibility/evaluate` (note: `packages/api-client` uses `GET /eligibility/evaluate/{opportunityId}` — reconcile with `FRONTEND_API_INTEGRATION_SPEC.md`), `GET /eligibility/gap-analysis/{opportunity_id}`.
  - **Resumes:** `GET /resumes`, `POST /resumes`, `POST /resumes/{id}/tailor`, `GET /resumes/{id}/pdf`.
  - **Agents & Approvals:** `POST /agents/sessions`, `GET /agents/sessions/{id}/state`, `GET /agents/approvals/pending`, `POST /agents/approvals/{id}/decision`.
  - **Voice:** `POST /voice/tickets` (30s single-use Redis ticket), `WS /voice/stream?ticket={uuid}`, `POST /voice/sessions`.
- **Authentication:** Supabase JWT (`Authorization: Bearer <JWT>`) verified locally via `SUPABASE_JWT_SECRET` (HS256) for `< 2ms` latency.
- **Voice Integration:** Full-duplex WebSocket streaming 16kHz Int16 linear PCM audio to Gemini Live (`GEMINI_LIVE_WEBSOCKET_URL`), with JSON control envelopes (`session_init`, `vad_signal`, `transcript`, `tool_start`, `audio_output`, `interrupted`).
- **ML Integration:** Expose `/api/v1/ml/*` and `/api/v1/eligibility/*` contracts compatible with `origin/ml` (`NexteRaSMLService` adapter with graceful `503` degradation when ML dependencies are absent).

---

## 6. Dependencies & Configuration Inventory

- **Backend Python (`apps/api/pyproject.toml`):** Core FastAPI/SQLAlchemy/asyncpg/Redis/websockets declared; `google-genai`, `langgraph`, `sentence-transformers`, `playwright` in optional extras; missing `pyjwt` (for local Supabase JWT verification), `arq` (referenced in `.env.example` for background worker), and `pgvector` Python SQLAlchemy driver (`pgvector>=0.3.0`).
- **Environment Variables (`.env.example` vs `apps/api/app/core/config.py`):**
  - `config.py` is missing fields present in `.env.example`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_LIVE_WEBSOCKET_URL`, `OLOSTEP_API_BASE_URL`, `CRUSTDATA_API_BASE_URL`, `CRUSTDATA_API_VERSION`, `PLAYWRIGHT_*`, `ARQ_*`.
- **Docker (`docker-compose.yml`):**
  - `api` service sets `DATABASE_URL=postgresql://...` instead of `postgresql+asyncpg://...`.
  - `postgres` service mounts `./supabase/migrations` on raw `pgvector/pgvector:pg16`, which lacks Supabase's `auth.users` schema.

---

## 7. Prioritized Implementation Plan

| Phase | Track | Key Deliverables |
| :--- | :--- | :--- |
| **A** | **Database Foundation** | Fix `docker-compose.yml` / use `supabase start` for local dev; add migration `20261126000001_rls_and_constraints.sql` (complete RLS policies for all user-owned tables, `auth.users` -> `profiles` trigger, `applications(user_id, opportunity_id)` unique constraint, `updated_at` triggers, resolve `384` vs `768` embedding dimension); implement `app/db/session.py` (async SQLAlchemy + `asyncpg`) and SQLAlchemy ORM models in `app/models/`. |
| **B** | **FastAPI Foundation** | Expand `app/core/config.py` to cover all `.env.example` settings; implement RFC 7807 `ProblemDetails` exception handlers, request ID middleware, Redis client (`app/core/redis.py`), and `to_camel` base Pydantic schema (`CamelModel`). |
| **C** | **Auth & User Management** | Implement local HS256 Supabase JWT verification (`get_current_user` dependency); build `/api/v1/users/me`, `/users/me/student-profile`, and `/career-passport` CRUD endpoints + repositories. |
| **D** | **Opportunity APIs** | Implement cursor-paginated `GET /api/v1/opportunities`, `GET /opportunities/{id}`, `POST /opportunities/{id}/save`, and `POST /opportunities/discover` backed by PostgreSQL + pgvector. |
| **E** | **ML Inference Integration** | Coordinate with Sanju to integrate `origin/ml`'s `apps/api/app/ml/adapter.py`, `schemas/ml.py`, and `api/v1/ml.py` (via PR to `develop` or cherry-pick when ready), wiring `/eligibility/evaluate` and `/eligibility/gap-analysis/{opportunity_id}`. |
| **F** | **Gemini & LangGraph** | Implement `app/agents/` state machines (starting with Discovery, Eligibility, Resume Tailoring, Application Approval Gate), Redis/Postgres checkpointing, and `POST /voice/tickets` + `WS /voice/stream` Gemini Live proxy. |
| **G** | **External Integrations** | Build async `httpx` adapters with Redis caching and exponential backoff in `app/integrations/` for Olostep (`/v1/searches`, `/v1/scrapes`, `/v1/crawls`, `/v1/schedules`) and Crustdata (`/screener/identify`, `/company/enrich`, `/screener/person/search`), plus `app/tasks/worker.py` (ARQ). |
| **H** | **Browser Automation** | Implement sandboxed Playwright `BrowserContext` dry-run filler, Supabase Storage screenshot upload, `approval_requests` pause/resume gate, and `browser_execution_logs` audit writer (strictly adhering to anti-CAPTCHA-bypass policy). |
| **I** | **Testing & Integration** | Add unit, repository, and FastAPI integration tests (`pytest-asyncio` + mocked external providers) to `apps/api/tests/`; reconcile minor route mismatches in `packages/api-client` (`/users/me/profile` vs `/users/me`, `GET` vs `POST` `/eligibility/evaluate`) with Sanju; run `make verify`. |

---

## 8. Risks & Blockers

1. **Docker Compose Postgres vs Supabase Auth (`High`):** Running `docker compose up` mounts `supabase/migrations/` onto vanilla `pgvector/pgvector:pg16`, which will fail on `REFERENCES auth.users(id)` and `auth.uid()`. **Mitigation:** Use Supabase CLI (`supabase start`) for local DB + Auth, or provide a dev-only `auth` schema shim for standalone Docker.
2. **RLS Lockout (`High`):** Currently 9 RLS-enabled tables have zero policies. Any Supabase client or RLS-enforced session will receive empty results/permission errors until a follow-up migration adds policies.
3. **Embedding Dimension Mismatch (`Medium`):** `opportunity_embeddings` is `vector(768)` while `ml/` MiniLM uses `384`. **Mitigation:** Align on `384` (MiniLM) + `768` (Gemini) or add a dedicated column before indexing production data.
4. **API Client vs Spec Drift (`Low/Medium`):** `packages/api-client/src/index.ts` calls `/users/me/profile`, `/opportunities/discover`, `/eligibility/evaluate/{id}`, and `/agents/approval/{id}`, whereas `FRONTEND_API_INTEGRATION_SPEC.md` and `endpoint-specification.md` specify `/users/me`, `/opportunities`, `POST /eligibility/evaluate`, and `/agents/approvals/{id}/decision`. **Mitigation:** Reconcile contract in `CROSS_TEAM_CONTRACT_REGISTER.md` with Sanju before wiring frontend hooks.
5. **Missing `pyjwt`, `pgvector`, and `arq` in `apps/api/pyproject.toml` (`Low`):** Must be added to `apps/api/pyproject.toml` when implementing Phases A–C and G.
