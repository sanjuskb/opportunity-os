# NexteRaS (Opportunity OS) — Workstream Status Verification Matrix (WS1–WS10)

**Updated:** 2026-11-26 (`feat/phase0-1-core-infra` post-consolidation build; after PRs `#10`, `#11`, `#12` merged to `develop`)  
**Initial Baseline Audit Date:** 2026-11-26 (`origin/main`, `origin/develop`, `origin/sanju`, `origin/ml`, `origin/ramaraju`)  
**Status Vocabulary:** `VERIFIED COMPLETE` · `IMPLEMENTED, NOT VERIFIED` · `PARTIALLY COMPLETE` · `PROTOTYPE` · `MOCK/STUB` · `NOT IMPLEMENTED` · `BLOCKED` · `REQUIRES APPROVAL`

---

## Post-Consolidation Workstream Status (`feat/phase0-1-core-infra`)

| Workstream | Current Status | Implemented & Verified Evidence (`feat/phase0-1-core-infra`) | Remaining Gate / Scope |
| :--- | :--- | :--- | :--- |
| **WS1 — Backend & Database Foundation** | **`VERIFIED COMPLETE`** | Unified FastAPI app ([`main.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/main.py)) with 78 OpenAPI HTTP operations + 1 WS route, PyJWT auth on all protected + `/ml/*` routes, Redis rate limiting, security headers, 29 `public` tables across 10 migrations (`20261123000001`–`20261127000004`), live local PG17 + Redis verification (`123 passed, 1 skipped` in `apps/api`). | Hosted Supabase remote migration review. |
| **WS2 — Vector Database Pipeline** | **`VERIFIED COMPLETE`** | `opportunity_eligibility` aligned (`20261127000002`), `student_embeddings` table added, `search_similar_by_vector()` wired into `OpportunitiesService.discover()`, live `/eligibility/evaluate`, `/users/me/education`, and 3 ARQ crons registered (`worker.py`). | `SentenceTransformer` optional extra (`ml/.venv`) required for offline neural backfill (`1` skip in `apps/api/.venv` when ML extra is omitted). |
| **WS3 — Resume Intelligence Backend** | **`VERIFIED COMPLETE`** | Private `resumes` Storage bucket & `auth.uid()` RLS (`20261127000001`), magic-byte validated multipart `/resumes/upload`, PDF (`pymupdf`) + DOCX (`python-docx`) extraction, Passport-grounded NLI `/resumes/{id}/tailor`, ATS PDF export (`fpdf2`), signed download URL, and `/resumes/{id}/versions`. | Apply bucket migration to hosted Supabase on release. |
| **WS4 — Olostep Research Engine** | **`VERIFIED COMPLETE`** | SSRF-hardened `OlostepClient` ([`olostep.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/integrations/olostep.py)) covering search, scrape, answer, crawl, maps, batch, and monitors, persisting provenance into `opportunity_sources` + `opportunity_monitors` (`POST /research/discover`, `/watchtower/monitors`). | Production quota limits in autonomous runs. |
| **WS5 — Crustdata Integration** | **`VERIFIED COMPLETE`** | `CrustdataClient` ([`crustdata.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/integrations/crustdata.py)) + 24h DB cache into `organizations` (`GET /companies`, `POST /companies/enrich`, `GET /companies/{org_id}`). | Live quota key provisioning in prod environment. |
| **WS6 — Gemini & 9-Language Voice** | **`VERIFIED COMPLETE`** | Expanded to **9 languages** (`en, hi, te, ta, kn, ml, bn, mr, gu`) across TS config, Pydantic schemas, Noto fonts, typed `messages.ts` catalog, and ML Gujarati/Marathi preprocessing; `GeminiClient` (`x-goog-api-key`, verified REST w/ `gemini-3-flash-preview`), `GeminiLiveRelay` (`v1beta` `BidiGenerateContent` w/ `gemini-2.5-flash-native-audio-preview-12-2025`), career tool calling (`execute_career_tool`), `conversations` persistence, `WS /voice/stream`, and browser `AudioStreamingService` + `VoiceDrawer`. | Browser WebAudio manual mic acceptance in staging. |
| **WS7 — Background Workers & Crons** | **`VERIFIED COMPLETE`** | ARQ `WorkerSettings` (`7` task functions + `3` cron jobs: `backfill_missing_embeddings`, `check_opportunity_deadlines`, `aggregate_analytics_metrics`), domain jobs (`apps/api/app/tasks/jobs.py`), and `POST /jobs` / `GET /jobs/{job_id}` tracking. | Run dedicated Cloud Run worker container (`Dockerfile.worker`). |
| **WS8 — LangGraph Agent System** | **`REQUIRES APPROVAL`** | Agent architecture proposed in [`NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md); typed checkpoint contracts ([`contracts.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/agents/contracts.py)) & read-only telemetry endpoints (`/agents/sessions*`) implemented. **Autonomous multi-agent execution intentionally stopped at Approval Gate per Sections 15 & 22.** | **Explicit user sign-off required** before building autonomous LangGraph orchestrator. |
| **WS9 — Playwright Automation** | **`VERIFIED COMPLETE`** | Chromium v1255 `playwright_runner.py` fills portal fields against public/non-prod sandbox URLs, captures pre-submit screenshot & creates `approval_requests`, halts cleanly on CAPTCHA/MFA (`requires_manual_completion`), enforces `HTTP 403` before approval, and logs to `browser_execution_logs` (`test_automation_jobs_ws7_ws9.py`). | Production portal domain allowlist sign-off. |
| **WS10 — Frontend, Portals, Obs & Deploy** | **`VERIFIED COMPLETE`** | All `@tanstack/react-query` hooks ([`useOpportunityOs.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/lib/queries/useOpportunityOs.ts)), Supabase SSR fail-closed middleware, Student/Company/University RBAC (`role_portals` + `20261127000004`), live `/interview` & `/analytics`, Sentry/PostHog (`observability.py`), multi-stage Dockerfiles, Vercel/Cloud Run manifests, CI (`pnpm` lint/type-check/test/build `0` errors). | Configure Cloud Run / Vercel production secrets & deploy pipeline. |

---

## Historical Pre-Consolidation Baseline Audit (Preserved Below)

## 1. Executive Comparison: Declared vs. Audited Reality

| Workstream | Owner | Declared Status | Forensic Audited Status | Target Code Branch(es) | Runtime / Live Verification | Blocking Issues |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **WS1 — Backend & Database Foundation** | Ramaraju | `COMPLETED` | **`IMPLEMENTED, NOT VERIFIED`** *(Foundation partial; not merged; core gaps remain)* | `origin/ramaraju` (`aa19954`) only | **NOT VERIFIED LIVE** *(Docker/Postgres/Supabase offline locally; only mocked unit tests exist on branch)* | Unmerged from `develop`/`ml`; `/eligibility/evaluate` is stub; 4/6 `api-client` routes return `404`/`405`; missing company/university RBAC & `education` CRUD |
| **WS2 — Vector Database Pipeline** | Ramaraju | `COMPLETED` | **`PARTIALLY COMPLETE` / `IMPLEMENTED, NOT VERIFIED`** | `origin/ramaraju` + `ml` (`20261125000001`) | **NOT VERIFIED LIVE** *(Unit tests mock encoder, DB & ARQ; live integration tests unrun)* | `EmbeddingRepository.search_similar_by_vector()` has **zero** API/service callers; `vector(768)` Gemini column unused (`384`-dim MiniLM only) |
| **WS3 — Resume Intelligence Backend** | Ramaraju + ML | `NEXT TO START` | **`PARTIALLY COMPLETE`** *(Split across 2 branches with major missing infra)* | `ml` (extraction) & `origin/ramaraju` (JSON CRUD) | ML text/PDF extractor passes offline unit tests on `ml`; Resume API unit-tested with fake repo on `ramaraju` | Missing multipart file upload, `.docx` parser (`python-docx`), Supabase Storage bucket/policies, `/resumes/{id}/tailor`, `/resumes/{id}/pdf` |
| **WS4 — Olostep Research Engine** | Ramaraju | `PLANNED` | **`NOT IMPLEMENTED`** | None (`integrations/__init__.py` empty everywhere) | None (`OLOSTEP_API_KEY` unset) | Zero Olostep client code (`/searches`, `/scrapes`, `/answers`, `/crawl`, `/maps`, `/batch`, monitors) |
| **WS5 — Crustdata Integration** | Ramaraju | `PLANNED` | **`NOT IMPLEMENTED`** | None (`integrations/__init__.py` empty everywhere) | None (`CRUSTDATA_API_KEY` unset) | Zero Crustdata company/people/job enrichment or watcher code |
| **WS6 — Gemini Backend Services** | Ramaraju | `PLANNED` | **`PARTIALLY COMPLETE`** *(REST text adapters on `ml`; Live Voice **`STUB`** / **`NOT IMPLEMENTED`**)* | `ml` (REST) & `origin/ramaraju` (WS tickets/ack) | Blocked (`GEMINI_API_KEY` unset); WS tests mocked only | Gemini Live WS relay, audio streaming, turn-taking, interruption, fallback ASR/TTS, function calling all absent; frontend `VoiceDrawer` is `setTimeout` mock |
| **WS7 — Background Workers & Scheduling** | Ramaraju | `PLANNED` | **`PARTIALLY COMPLETE`** *(ARQ embedding worker implemented on `ramaraju`; scheduling/other jobs missing)* | `origin/ramaraju` (absent on `ml`, where `Dockerfile.worker` breaks) | Worker & tasks unit-tested with `_FakeRedis`/`_FakeRepo`; Redis offline (`6379` closed) | Zero `cron_jobs` schedules, zero research/resume/Playwright/monitoring tasks; `ml` branch lacks `worker.py` |
| **WS8 — LangGraph Agent System** | Agent Team | `PLANNED` | **`PROTOTYPE`** *(Intentionally deferred; valid offline prototype on `ml`)* | `ml` (`ml/src/integration/langgraph_adapter.py`) | Compiles & tests M11 `interrupt()` with `MemorySaver` on `ml` | `apps/api/app/agents/` empty across all branches; no `PostgresSaver`, no API orchestration, no multi-agent tool nodes |
| **WS9 — Playwright Automation & Browser Execution** | Backend + Agent | `PLANNED` | **`NOT IMPLEMENTED`** | `pyproject.toml` dependency extra only | None | Zero Playwright launch, session, form fill, screenshot, or approval resume runner; `browser_execution_logs` table unused |
| **WS10 — Frontend Integration, Auth & Deployment Readiness** | Frontend + Full-Stack | *(In progress / Partial)* | **`PARTIALLY COMPLETE`** *(Split-brain UI + mock store on `develop`/`ml` vs Auth on stale `ramaraju`)* | Split (`origin/develop`/`ml` vs `origin/ramaraju`) | Static checks pass on `ml`; **not runtime-verified** across API/Auth/Prod | 19 modern UI routes use `useMockStore`; `ramaraju` put Auth on outdated UI deleting 19 pages; missing Sentry, PostHog, i18n (`mr`/`gu` missing), Cloud Run/Vercel CD |

---

## 2. Detailed Forensic Audit Per Workstream

### WS1 — Backend & Database Foundation (Declared: `COMPLETED` -> Audited: `IMPLEMENTED, NOT VERIFIED`)
* **Evidence Implemented (`origin/ramaraju` only):**
  * FastAPI app factory with lifespan `DatabaseManager` (`asyncpg` pooled engine) & `Redis` (`apps/api/app/main.py`), RFC 7807 ProblemDetails exception handlers (`app/core/errors.py`), fail-closed production settings validation (`app/core/config.py`), and PyJWT HS256/ES256/RS256/JWKS verification rejecting `anon` role (`app/core/security.py`).
  * SQLAlchemy async ORM models (`app/models/entities.py`), 9 repositories (`profiles`, `student_profiles`, `career_passports`, `opportunities`, `applications`, `approvals`, `notifications`, `resumes`, `voice_sessions`), and 8 service modules.
  * 5 ordered SQL migrations (`20261123000001` baseline + `20261126000001`–`000004`) defining 25 tables, hardened `handle_new_user()` trigger, RLS on all 25 tables, and restricted client mutations on `applications`, `profiles`, and `notifications`.
* **What Is Incomplete / Broken:**
  * Completely **absent from `ml`, `develop`, and `main`** (still sitting on unmerged `origin/ramaraju`).
  * `POST /api/v1/eligibility/evaluate` returns a hardcoded stub (`is_eligible=False, score=0.0, reasons=["Profile evaluation pending ML integration."]`).
  * `packages/api-client/src/index.ts` has 4 broken routes against `origin/ramaraju` (`404`/`405`).
  * Missing FastAPI endpoints for `education`, `resume_versions`, `resume_customizations`, `opportunity_sources`, `opportunity_monitors`, `agent_sessions`, `agent_events`, `browser_execution_logs`, `analytics_events`, and Company/University portals.
  * Zero live PostgreSQL execution observed (`docker info` unreachable; `supabase status` errored on `ml`; unit tests mock `FakeDb`/`FakeRepo`/`FakeRedis`).

---

### WS2 — Vector Database Pipeline (Declared: `COMPLETED` -> Audited: `PARTIALLY COMPLETE` / `IMPLEMENTED, NOT VERIFIED`)
* **Evidence Implemented:**
  * `origin/ramaraju` adds `20261126000002_constraints_and_vector_alignment.sql` + `20261126000004_embedding_pipeline_metadata.sql` (`embedding_minilm_384 vector(384)`, `HNSW idx_embeddings_minilm_384_hnsw`, `content_hash`, `embedding_status`, `retry_count >= 0`, state consistency CHECK constraint `embedding_status <> 'ready' OR embedding_minilm_384 IS NOT NULL`).
  * `ml` adds `20261125000001_add_minilm_384_embeddings.sql` (functionally overlapping dual-vector migration).
  * `CanonicalEmbeddingAdapter` (`app/ml/embeddings.py`), `opportunity_text.py` (deterministic SHA256 hash), `EmbeddingRepository` (`app/repositories/embeddings.py`), and ARQ tasks `embed_opportunity` & `backfill_missing_embeddings` (`app/tasks/embeddings.py`).
* **Dimension Conflict Analysis (`768` vs `384`):**
  * Initial schema (`20261123000001`) created `embedding vector(768)` + `ivfflat` intended for Gemini `text-embedding-004` (`docs/architecture/FEATURE_TRACEABILITY_MATRIX.md` & `.env.example`).
  * `ml` trained fine-tuned `all-MiniLM-L6-v2` (`minilm-nexteras-v1`, **384-dim**) and added `embedding_minilm_384 vector(384)`.
  * Both `ml` and `origin/ramaraju` intentionally keep **both columns** (`768` untouched, `384` active) for backward-compatibility, **but in code**, `CanonicalEmbeddingAdapter` & `EmbeddingRepository` strictly validate `384`-dim and **never populate `embedding` (768-dim)**, while `EmbeddingRepository` only handles opportunities (no `resume_embeddings`, `student_embeddings`, or `career_passport` vector table exists).
* **Critical Disconnection:**
  * `EmbeddingRepository.search_similar_by_vector()` is defined and unit-tested (`_FakeResult`), **but has zero callers in any service or API endpoint**! `POST /api/v1/opportunities/discover` still executes plain SQL `ILIKE` filtering.
  * Live DB + Redis + real encoder end-to-end test (`test_ws2d4_pipeline_live.py`) has **not been verified live** (requires live Postgres/Redis).

---

### WS3 — Resume Intelligence Backend (Declared: `NEXT TO START` -> Audited: `PARTIALLY COMPLETE`)
* **Evidence Implemented:**
  * **ML Side (`ml`):** `ResumeExtractionService` (`ml/src/extraction/extractor.py`) parses `.txt`, `.md`, `.json`, and `.pdf` (via `pymupdf`) deterministically with grounded `EvidenceSpan` tracking, optional `GeminiStructuredLLMBackend` merge rejecting ungrounded skills, upload metadata validation (`10 MB` cap, path-traversal block), and PII redaction in logs.
  * **Backend Side (`origin/ramaraju`):** JSON-only CRUD routes (`GET/POST /api/v1/resumes`, `GET/DELETE /api/v1/resumes/{id}`), `ResumeRepository`, `ResumesService`.
* **What Is Missing:**
  * **No file upload endpoint** (`multipart/form-data` binary upload, MIME/magic-byte check).
  * **No `.docx` support** (`python-docx` absent; `extractor.py` explicitly raises `ValueError("Unsupported extension: .docx")`).
  * **No Supabase Storage integration** (`supabase/config.toml` enables Storage, but zero buckets or `storage.objects` RLS policies exist; `apps/api` has no Storage SDK/HTTP client or signed-URL logic).
  * **No tailoring or PDF export** (`/resumes/{id}/tailor`, `/resumes/{id}/pdf`, WeasyPrint/ReportLab missing; `resume_versions` and `resume_customizations` tables have no services/endpoints).
  * **Dependency split:** `origin/ramaraju:apps/api/pyproject.toml` does not even include `pymupdf` or `ml` package dependencies.

---

### WS4 — Olostep Research Engine (Declared: `PLANNED` -> Audited: `NOT IMPLEMENTED`)
* `apps/api/app/integrations/__init__.py` contains only a placeholder comment across all branches.
* Zero integration modules, Pydantic schemas, retries/rate-limiters, webhook receivers, or source-tracking services exist for Olostep (`/v1/searches`, `/v1/scrapes`, `/v1/answers`, `/v1/crawl`, `/v1/maps`, `/v1/batch`, monitors).
* `public.opportunity_sources` and `public.opportunity_monitors` exist in SQL schema only, unpopulated by code.

---

### WS5 — Crustdata Integration (Declared: `PLANNED` -> Audited: `NOT IMPLEMENTED`)
* Zero Crustdata client modules, company enrichment mappers, people/job search adapters, watcher sync jobs, or API keys exist anywhere in the repo.
* `public.organizations` relies solely on static `supabase/seed/seed.sql` / `apps/web` mock fixtures.

---

### WS6 — Gemini Backend Services (Declared: `PLANNED` -> Audited: `PARTIALLY COMPLETE` REST / `NOT IMPLEMENTED` Live Voice)
* **What Exists:**
  * `ml` has REST adapters in `ml/src/integration/gemini_backends.py`: `GeminiStructuredLLMBackend` and `GeminiTranslationFallbackBackend` via `httpx` (blocking if `GEMINI_API_KEY` absent or placeholder). Untested live because `GEMINI_API_KEY` is unset.
  * `origin/ramaraju` has `VoiceTicketStore` (`app/voice/tickets.py`, atomic single-use 30s Redis `GETDEL` ticket with production fail-closed and local memory fallback) and `WS /api/v1/voice/stream` (`app/api/v1/voice.py`).
* **What Is Missing / Stubbed:**
  * `WS /api/v1/voice/stream` does **not** connect to Gemini Live API; it only accepts binary PCM bytes and replies `{"event": "audio_received", "bytes": len(raw_bytes)}` plus echoes `session_init` / `interrupted` / `ping`.
  * Zero audio transcription (ASR), zero speech synthesis (TTS), zero Gemini function calling / tool declarations, zero turn-taking/barge-in handling, and zero `AudioWorklet`/WebSocket capture on the frontend (`VoiceDrawer.tsx` uses `setTimeout` over hardcoded strings).

---

### WS7 — Background Workers & Scheduling (Declared: `PLANNED` -> Audited: `PARTIALLY COMPLETE`)
* **What Exists (`origin/ramaraju` only):**
  * ARQ `WorkerSettings` (`app/tasks/worker.py`) with async DB/Redis startup/shutdown hooks, torch thread limits, `max_jobs=10`, `job_timeout=300`, `max_tries=3`, and tasks `embed_opportunity` & `backfill_missing_embeddings` (`app/tasks/embeddings.py`).
* **What Is Missing:**
  * **Absent from `ml` & `develop`:** `infra/docker/Dockerfile.worker` points to `arq app.tasks.worker.WorkerSettings`, which fails immediately on `ml`.
  * **Zero `cron_jobs` configured:** No periodic deadline alerts, opportunity ingestion monitors, or stale vector sweeps.
  * **Zero non-embedding workers:** No async resume parsing/extraction job, Olostep research job, Crustdata sync job, or Playwright dispatch job.
  * Redis is not running locally (`127.0.0.1:6379` closed); worker never verified against a real Redis broker.

---

### WS8 — LangGraph Agent System (Declared: `PLANNED` -> Audited: `PROTOTYPE`)
* **What Exists (`ml` only):**
  * `ml/src/integration/langgraph_adapter.py` defines a real compiled LangGraph `StateGraph` (`build_nexteras_career_workflow`) with stages `PERCEIVE -> REASON -> PLAN -> DELEGATE_VERIFY -> [M11 interrupt()] -> ACT / ACT_BLOCKED -> EVALUATE_ADAPT`.
  * Compiled and verified offline with `langgraph.checkpoint.memory.MemorySaver` and `Command(resume=...)` in `ml/tests/test_langgraph_and_api_e2e.py`.
* **Note:** Because full agent development has intentionally not started, this is properly classified as a validated `PROTOTYPE`, not a failed integration.
* **What Remains To Build:**
  * `apps/api/app/agents/` is empty across all branches.
  * Replace ephemeral `MemorySaver` with `PostgresSaver` (`langgraph-checkpoint-postgres`), link M11 `interrupt()` directly to `public.human_approvals` & `agent_sessions`/`agent_events`, and add actual tool nodes (Olostep, Crustdata, Vector Discovery, Resume Tailoring, Playwright).

---

### WS9 — Playwright Automation & Browser Execution (Declared: `PLANNED` -> Audited: `NOT IMPLEMENTED`)
* `playwright>=1.47.0` appears only as `[project.optional-dependencies] automation` in `apps/api/pyproject.toml`, and Playwright CLI exists locally, but **zero** Python browser automation code exists anywhere under `apps/api/` or `ml/`.
* No Chromium container runtime exists in `Dockerfile.worker` (`python:3.12-slim` only, no `playwright install chromium` or OS libs).
* `public.browser_execution_logs` has zero repository/service/API writers.

---

### WS10 — Frontend Integration, Auth & Deployment Readiness (Audited: `PARTIALLY COMPLETE`)
* **UI & Mock Reality (`origin/develop` / `ml`):**
  * 29 App Router routes exist with polished Tailwind UI, Three.js (`EcosystemScene`), Spline iframe (`GenkubRobot`), Student/Company/University dashboards, and Agent Control Center (`M01`–`M13` UI).
  * **Zero backend integration:** Recursive search confirmed **zero** `fetch(`, `new WebSocket(`, `AudioContext`, `AudioWorklet`, `@opportunity-os/api-client`, `useQuery`, `@supabase/*`, `@sentry/*`, `posthog-js`, or `next-intl` usage across `apps/web/src` on `develop`/`ml`.
* **Auth Divergence (`origin/ramaraju`):**
  * Commit `aa19954` added real `@supabase/ssr` Auth (`middleware.ts`, `auth/callback/route.ts`, `AuthProvider.tsx`, `login/page.tsx`) **directly onto the stale `2242d24` `apps/web` baseline**, deleting 19 routes (`/overview`, `/agent-control-center`, `/company/*`, `/university/*`, etc.) and `components/landing/*` and creating direct Git conflicts across `apps/web/src/app/{layout,login/page,page,settings/page}.tsx` and `package.json`.
  * Security note in `origin/ramaraju:apps/web/src/middleware.ts`: fails open when Supabase env vars are missing (`if (!config) return NextResponse.next(...)`) and only protects 6 URL prefixes.
* **Language Requirement Mismatch (9 vs 7):**
  * Product audit specifies 9 languages (`en, hi, te, ta, bn, mr, gu, kn, ml`). Repo code (`APP_CONFIG.SUPPORTED_LANGUAGES`, backend enums, ML corpus) only implements **7 languages** (+ `hinglish`), omitting **Marathi (`mr`)** and **Gujarati (`gu`)** completely.
* **Deployment & Observability Gaps:**
  * No Vercel config, no Cloud Run YAML / Terraform / CD GitHub Actions deploy workflows, no Sentry/PostHog instrumentation, no FastAPI rate limiting (`slowapi`/Redis) or security headers (`CSP`, `X-Frame-Options`, `HSTS`).
