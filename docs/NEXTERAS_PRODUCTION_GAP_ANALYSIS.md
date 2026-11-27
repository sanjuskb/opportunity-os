# NexteRaS (Opportunity OS) — Production Gap Analysis

**Updated:** 2026-11-27 (`feat/ws8-autonomous-agents` build on top of `develop` @ `d7ccac9` / PR #13)  
**Pre-Consolidation Audit Baseline:** `origin/main`, `origin/develop`, `origin/sanju`, `origin/ml`, and `origin/ramaraju`

---

## Post-Consolidation Gap Resolution Summary (`feat/ws8-autonomous-agents`)

All **10 P0 launch blockers** (`GAP-P0-01` through `GAP-P0-10`) and **all P1 platform & autonomous agent gaps** (`GAP-P1-01` through `GAP-P1-06`) identified in the initial audit have been resolved across `develop` (PRs `#10`–`#13`) and `feat/ws8-autonomous-agents`:
* **Resolved P0s:** Branches consolidated (`#10`–`#13`); all frontend pages wired to FastAPI + TanStack Query (`useOpportunityOs.ts`); SDK contracts synchronized & verified across all `83` HTTP operations + `WS /api/v1/voice/stream`; local PG17 + pgvector (`54332`) & Redis (`6379`) stack automated via `bootstrap_local_db.py`; `search_similar_by_vector()` activated; `/api/v1/ml/*` protected by JWT + rate limits & Next.js middleware fail-closed; live `/eligibility/evaluate` + aligned SQL columns; real Gemini Live `WS /voice/stream` + `AudioStreamingService`; private `resumes` Storage + DOCX + PDF tailoring/export; **9 Indian languages** (`en, hi, te, ta, kn, ml, bn, mr, gu`) supported across frontend, backend, and ML.
* **Resolved P1 Platform & WS8 Autonomous Agents:** Olostep (`olostep.py`) & Crustdata (`crustdata.py`) clients + caching, Playwright Chromium sandbox runner (`playwright_runner.py` with CAPTCHA halt, owned screenshot API & approval `403` guard), ARQ `WorkerSettings` with 3 `cron_jobs` & domain jobs, RBAC Company/University portals, live `/interview` + `/analytics`, Sentry/PostHog (`observability.py`) + Docker/Vercel/Cloud Run manifests + expanded CI, AND the full **WS8 autonomous 9-agent LangGraph orchestrator** (`apps/api/app/agents/orchestrator.py` with `AsyncPostgresSaver`, M11 `interrupt()`/`Command(resume=...)` via `POST /agents/approvals/{id}/decision`, SSE `GET /agents/sessions/{id}/stream`, and Control Center UI live wiring — offline unit/contract/sandbox suites verified `94/94` unit / `109` total passed, with live PG17 E2E `test_agents_postgres_e2e.py` ready to execute when Docker PG17 `54332` is booted).
* **Remaining Post-MVP / Production Cutover Items:** Applying migrations (`20261123000001`–`20261127000004`) to hosted Supabase, provisioning staging secrets in Cloud Run / Vercel, running live PG17 `tests/integration/test_agents_postgres_e2e.py` in staging/Docker host, collecting `>= 500` anonymized `analytics_events` sessions for the supervised GBDT ranker (`GAP-P2-04`), and institutional DigiLocker/NAD & external ML corpora expansion (`P3`).

---

## Historical Pre-Consolidation Audit Baseline (Preserved Below)

## Severity Definitions
* **P0 — Launch Blocker:** Prevents compiling, merging, authenticating, storing real data, or executing core product promises cleanly without security vulnerabilities or data loss.
* **P1 — Core Production Requirement:** Required for real autonomous product operation (discovery, firmographics, agent orchestration, resume PDFs, rate limiting, monitoring).
* **P2 — Operational Hardening & Experience:** Required for maintainability, CI reliability, memory/CPU scaling, full localization, and production telemetry.
* **P3 — Post-MVP Scale & Enhancement:** Required for institutional verification, larger benchmark datasets, and learned supervised rankers.

---

## Summary Count by Priority

| Severity | Gap Count | Key Theme |
| :--- | :---: | :--- |
| **P0** | 10 | Branch divergence/conflicts, zero live UI-API integration, broken SDK contracts, unverified live DB/Redis, uncalled pgvector search, unauthenticated ML routes, stub eligibility & voice WS, missing file upload/Storage/DOCX, 9-vs-7 language gap |
| **P1** | 6 | Unimplemented Olostep & Crustdata, unpersisted LangGraph prototype, unimplemented Playwright runner, missing ARQ crons/job queues, missing rate limits/Sentry/PostHog/headers, unimplemented company/university/education APIs |
| **P2** | 4 | Missing Cloud Run/Vercel CD & thin CI, Windows/PyTorch heavy RSS & teardown hang, missing `next-intl` UI i18n, uncollected interaction logs (`<500`) |
| **P3** | 2 | Unbuilt DigiLocker/NAD gateway, small synthetic ML evaluation benchmarks |

---

## 1. P0 — Launch Blockers

### GAP-P0-01: Severe Three-Way Branch Divergence & Direct Merge Conflicts
* **Evidence:**
  * `origin/develop` (`bfea709`) holds the 29-route modern UI (`@opportunity-os/web`), Spline/Three.js hero, and Agent Control Center.
  * `origin/ml` (`f14190d`) branches from `sanju` (`a8022a3`), adding the `ml/` subsystem and 7 stateless FastAPI `/api/v1/ml/*` routes.
  * `origin/ramaraju` (`aa19954`) branches from stale `2242d24`, implementing FastAPI core, SQLAlchemy, ARQ, 5 migrations, and `@supabase/ssr` Auth UI **while deleting/omitting 19 frontend routes and `components/landing/*`**.
  * Common conflicted files between `origin/ml` and `origin/ramaraju`: `.gitignore`, `apps/api/app/api/v1/router.py`, `apps/api/app/core/config.py`, `apps/api/pyproject.toml`, `apps/web/package.json`, `apps/web/src/app/{layout,login/page,page,settings/page}.tsx`, `docker-compose.yml`, `pnpm-lock.yaml`.
* **Risk:** Naive `git merge` of `ramaraju` into `develop` or `ml` will either overwrite the modern frontend or break Supabase SSR Auth, FastAPI startup lifespan, or ML routes.
* **Fix:** Perform a structured cherry-pick/merge consolidation onto an integration branch preserving `origin/develop`'s 29 routes + `ml`'s `ml/` & ML routes + `origin/ramaraju`'s backend core, migrations, ARQ worker, and SSR auth helpers cleanly.

### GAP-P0-02: Zero Frontend-to-Backend Integration (`develop` / `ml`)
* **Evidence:** Recursive scan of `apps/web/src/**/*.{ts,tsx}` on `ml`/`develop` found **zero** `fetch(`, `new WebSocket(`, `useQuery`, `@opportunity-os/api-client`, or `@supabase/*` calls (matches existed only inside mock strings). All 29 routes read hardcoded fixtures from `useMockStore`.
* **Fix:** Wire `apps/web` to `@opportunity-os/api-client` (with TanStack Query v5) and Supabase Auth session tokens.

### GAP-P0-03: 4/6 Methods in `@opportunity-os/api-client` Fail With HTTP `404`/`405`
* **Evidence:** Comparing `origin/ramaraju:packages/api-client/src/index.ts` vs `origin/ramaraju:apps/api/app/api/v1/router.py`:
  * `getProfile()` -> `GET /users/me/profile` vs backend `GET /users/me` + `/users/me/student-profile` (`404`).
  * `discoverOpportunities()` -> `GET /opportunities/discover?q=...` vs backend `GET /opportunities` / `POST /opportunities/discover` (`405`).
  * `checkEligibility()` -> `GET /eligibility/evaluate/{id}` vs backend `POST /eligibility/evaluate` (`405`).
  * `approveAction()` -> `POST /agents/approval/{id}` vs backend `POST /agents/approvals/{id}/decision` (`404`).
* **Fix:** Regenerate or synchronize TypeScript API client methods & DTOs against FastAPI OpenAPI schema and expand SDK coverage to Resumes, Career Passport, Notifications, Voice, and ML endpoints.

### GAP-P0-04: Zero Live Database, pgvector, Supabase Auth, or Redis Verification
* **Evidence:**
  * All 21 NexteRaS env vars are `UNSET` locally; zero `.env` files exist.
  * Docker daemon offline; PostgreSQL (`54322`), Redis (`6379`), API (`8000`), Web (`3000`) closed.
  * `supabase status` failed immediately on `ml` with `Invalid db.major_version: 16` (`origin/ramaraju` updated `supabase/config.toml` to `17`).
  * Unit tests on `origin/ramaraju` mock `AsyncSession`, `Redis`, `SentenceTransformer`, and `JWKClient`; live integration tests in `apps/api/tests/integration/` remain unexecuted.
* **Fix:** Boot local Supabase CLI (Postgres 17 + pgvector) + Redis, apply all 5+ migrations cleanly, run all `apps/api/tests/integration/` tests live, and capture results.

### GAP-P0-05: Semantic `pgvector` Search Disconnected From API & Unused `vector(768)` Column
* **Evidence:** `EmbeddingRepository.search_similar_by_vector()` (`origin/ramaraju`) has **zero** callers across services or routes; `POST /api/v1/opportunities/discover` executes plain SQL `ILIKE` filtering. Additionally, `embedding vector(768)` (initial schema) is unpopulated while `embedding_minilm_384 vector(384)` HNSW is written by the worker. No student profile/resume vector table exists yet.
* **Fix:** Wire `search_similar_by_vector()` into discovery/ranking service; formally standardize on `vector(384)` (`minilm-nexteras-v1`) or implement dual-write/drop unused column via migration; add student/resume embedding storage for fast matching.

### GAP-P0-06: Unauthenticated ML Endpoints (`ml` Branch) & Fail-Open Next.js Auth Middleware (`ramaraju`)
* **Evidence:**
  * All 7 endpoints in `apps/api/app/api/v1/ml.py` (`extract-resume`, `recommend-pipeline`, etc.) lack `Depends(get_current_user)` — exposing expensive PyTorch CPU inference and optional paid Gemini API quota to unauthenticated callers.
  * `origin/ramaraju:apps/web/src/middleware.ts` passes requests unauthenticated if Supabase env vars are missing (`if (!config) return NextResponse.next(...)`) and only protects 6 of 29 routes.
* **Fix:** Enforce JWT authentication + rate limiting on all `/api/v1/ml/*` routes; change Next.js middleware in production to fail closed (or explicit public-only allowlist) and protect all authenticated dashboard routes (`/overview`, `/notifications`, `/onboarding`, `/role-selection`, `/agent-control-center`, `/company/*`, `/university/*`).

### GAP-P0-07: Eligibility Engine Stubbed on `ramaraju` + DB Schema Gaps vs ML Rule Engine
* **Evidence:** `origin/ramaraju:POST /api/v1/eligibility/evaluate` returns hardcoded `is_eligible=False, score=0.0, reasons=["Profile evaluation pending ML integration."]`. Meanwhile `ml`'s real 10-rule `EligibilityEngine` checks `eligible_academic_years`, `max_active_backlogs`, `min_experience_months`, `allowed_locations`, `remote_allowed`, `required_citizenship`, and `preferred_skills` — **none of which exist as columns in `public.opportunity_eligibility`**.
* **Fix:** Add migration for missing `opportunity_eligibility` columns, wire `NexteRaSMLService.evaluate_eligibility()` into `origin/ramaraju`'s endpoint, and fetch real `student_profiles` + `career_passports` + `opportunities` from Postgres.

### GAP-P0-08: Voice Assistant Is Simulated UI + Frame-Ack WebSocket Stub (WS6)
* **Evidence:**
  * `VoiceDrawer.tsx` simulates speech recognition and answers via `setTimeout` (`1800ms`, `700ms`) over hardcoded `DEMO_VOICE_QUERIES`. Zero WebAudio `AudioContext` / `AudioWorklet` capture exists.
  * `origin/ramaraju:WS /api/v1/voice/stream` validates a ticket and echoes `{"event": "audio_received"}` without opening any Gemini Live WebSocket, transcribing audio, calling backend tools, or returning TTS audio.
* **Fix:** Build browser `AudioWorklet` 16kHz PCM streamer + playback queue, upgrade `/voice/stream` to bidirectional Gemini Live API relay (with Gemini function calling + STT/TTS text fallback), and pass `GEMINI_API_KEY` securely via server config.

### GAP-P0-09: Resume Upload, `.docx`, Supabase Storage, Tailoring & PDF Export Missing (WS3)
* **Evidence:**
  * `origin/ramaraju` `/resumes` supports JSON metadata only.
  * Zero Supabase Storage buckets or `storage.objects` RLS policies exist in migrations.
  * `ml/src/extraction/extractor.py` supports `.txt/.md/.json/.pdf` (`pymupdf` missing from `ramaraju`'s `pyproject.toml`), and explicitly rejects `.docx`.
  * Zero tailoring workflow (`/resumes/{id}/tailor`) or PDF export (`/resumes/{id}/pdf`) exists.
* **Fix:** Create private `resumes` Storage bucket with `auth.uid()` RLS policies, add multipart `POST /resumes/upload` with magic-byte validation, install `python-docx` + `pymupdf` in unified API env, wire `ResumeExtractionService`, and build grounded tailoring + PDF generation.

### GAP-P0-10: 9-Language Product Mandate vs. 7-Language Implementation (`mr` & `gu` Missing)
* **Evidence:** Prompt requires **9 languages** (`en, hi, te, ta, bn, mr, gu, kn, ml`). Repo code (`APP_CONFIG.SUPPORTED_LANGUAGES`, `apps/api/app/schemas/common.py`, `ml/src/multilingual/preprocessing.py`, `ml/datasets/synthetic/multilingual_eval_corpus.json`) configures only **7 languages** (`en, hi, te, ta, kn, ml, bn` + `hinglish`). Marathi (`mr`) and Gujarati (`gu`) are completely absent, and `preprocessing.py` script heuristics cannot distinguish Devanagari Marathi from Hindi without lexical cues. Furthermore, synthetic tests showed weak offline cross-lingual retrieval R@1 for `te` (`0.0`), `ml` (`0.0`), `bn` (`0.3333`), `kn` (`0.3333`), and `ta` (`0.6667`).
* **Fix:** Add `mr` and `gu` across TypeScript configs, DB/API validation, ML script/lexical detector, and Gemini translation prompts; enforce Gemini Live / translation fallback for all non-English/code-switched queries.

---

## 2. P1 — Core Production Requirements

### GAP-P1-01: Olostep Web Intelligence Engine Completely Unimplemented (WS4)
* **Impact:** Platform cannot discover live internships/fellowships or monitor portals.
* **Remediation:** Build `apps/api/app/integrations/olostep.py` (search, scrape, answers, crawl, maps, batch, monitors) with provenance logging into `public.opportunity_sources` and `public.opportunity_monitors`.

### GAP-P1-02: Crustdata Company Intelligence Completely Unimplemented (WS5)
* **Impact:** Cannot verify company legitimacy, headcount, funding, or hiring signals.
* **Remediation:** Build `apps/api/app/integrations/crustdata.py` to enrich `public.organizations` and schedule periodic company watcher refreshes.

### GAP-P1-03: LangGraph Prototype (`MemorySaver`) Isolated From API & Approvals DB (WS8)
* **Impact:** Workflows lose state on restart and `POST /agents/approvals/{id}/decision` does not resume suspended executions.
* **Remediation:** Migrate LangGraph prototype from `ml/src/integration/` into `apps/api/app/agents/`, replace `MemorySaver` with `PostgresSaver`, persist `agent_sessions`/`agent_events`, and bind M11 `interrupt()` directly to `public.human_approvals`.

### GAP-P1-04: Playwright Browser Automation Engine Unimplemented (WS9)
* **Impact:** Autonomous form pre-fill dry-runs and post-approval submission workflows cannot run.
* **Remediation:** Add Chromium + Playwright runtime in dedicated worker container (`Dockerfile.worker`), implement controlled form-fill/screenshot capture writing to `public.browser_execution_logs`, and enforce mandatory stop on CAPTCHA/MFA or unapproved submission.

### GAP-P1-05: Background Scheduling (`cron_jobs`) & Async Jobs Missing (WS7)
* **Impact:** `Dockerfile.worker` breaks on `ml`; on `ramaraju`, ARQ only handles opportunity embeddings (no periodic discovery, deadline checks, stale vector sweeps, or async resume extraction).
* **Remediation:** Unify ARQ worker into merged branch, register `cron_jobs` (`check_deadlines`, `sweep_pending_embeddings`, `run_olostep_monitors`), and add job tracking endpoints.

### GAP-P1-06: Missing Rate Limiting, Security Headers, Sentry, PostHog & Role Portals RBAC
* **Impact:** Public API vulnerable to brute-force/DoS and missing runtime crash/funnel telemetry; Company (`4` pages) and University (`3` pages) routes + `public.education` have zero API support or role RBAC.
* **Remediation:** Add Redis-backed rate limiting, FastAPI & Next.js security headers (`CSP`, `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`), Sentry + PostHog SDKs, role claims in JWT/profiles, and Company/University/Education endpoints.

---

## 3. P2 — Operational Hardening & Experience

* **GAP-P2-01 (No Production Deploy Manifests / Thin CI):** Zero Cloud Run service YAML/Terraform/CD workflows, zero Vercel project config; `.github/workflows/backend-checks.yml` only triggers on PRs and omits `apps/api/tests/integration` + worker/ML tests.
* **GAP-P2-02 (ML Process Memory & Cold-Start Latency):** Loading multiple transformer models hits `707–1228 MB` RSS each (requiring dedicated ML/ARQ worker Cloud Run memory >= `2–4 GiB` and strict `max_loaded_models=1` eviction). Additionally, `import torch` alone measured `26.79s` on local Windows CPU, and running `test_langgraph_and_api_e2e.py` end-to-end took `94.80s` across model loads, requiring pre-warmed container images (`HF_HOME` baked in or mounted) and warm min-instances in production.
* **GAP-P2-03 (Missing `next-intl` & UI Localization):** Only English strings render outside `VoiceDrawer` demo phrases; zero Indic fonts (`Noto Sans Devanagari/Telugu/Tamil/Kannada/Malayalam/Bengali/Gujarati`) configured.
* **GAP-P2-04 (Supervised GBDT Ranker Permanently Cold-Started):** Requires `>= 500` anonymized student interaction sessions (`analytics_events`), which has zero logging endpoints today.

---

## 4. P3 — Post-MVP Scale & Enhancements

* **GAP-P3-01 (Institutional Credentials / DigiLocker / NAD Gateway):** Frontend shows verified DigiLocker/AICTE badges; no government API integration or cryptographic verification workflow exists.
* **GAP-P3-02 (Synthetic-Only ML Benchmarks):** `matching_curriculum_v2` (`88` triplets) and `multilingual_eval_corpus` (`24` queries) must be augmented with real anonymized student-opportunity feedback and external corpora (e.g., ESCO, AI4Bharat) before claiming generalized production precision.
