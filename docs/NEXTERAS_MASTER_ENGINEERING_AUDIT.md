# NexteRaS (Opportunity OS) — Master Engineering & Production Readiness Audit

**Updated:** 2026-11-26 (`feat/phase0-1-core-infra` post-consolidation build; PRs `#10`, `#11`, `#12` merged to `develop`)  
**Repository:** `https://github.com/sanjuskb/opportunity-os` (`origin`)  
**Workspace Root:** [`d:/ai career intelligence autonomous system`](file:///d:/ai%20career%20intelligence%20autonomous%20system/)

> [!NOTE]
> **Post-Consolidation Status Update:** The initial forensic baseline below (`Section 1`–`Section 28`) captured the pre-consolidation state across separate branches (`main`, `develop`, `sanju`, `ml`, `ramaraju`). Since that audit, all three workstreams were merged via PRs `#10`–`#12` into `develop`, and Phases 0–9 deterministic product engineering & deployment hardening have been built and verified on `feat/phase0-1-core-infra`. Live status across all 10 workstreams is tracked in [`NEXTERAS_LIVE_ENGINEERING_PROGRESS.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_LIVE_ENGINEERING_PROGRESS.md) and [`NEXTERAS_WORKSTREAM_STATUS_MATRIX.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_WORKSTREAM_STATUS_MATRIX.md). **Autonomous LangGraph multi-agent execution (WS8) remains held at the mandatory approval gate defined in [`NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md).**

---

## Accompanying Deep-Dive Documentation Artifacts (`docs/NEXTERAS_*.md`)
* [`NEXTERAS_MASTER_ENGINEERING_AUDIT.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_MASTER_ENGINEERING_AUDIT.md) — Master forensic audit baseline & post-consolidation verification status.
* [`NEXTERAS_WORKSTREAM_STATUS_MATRIX.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_WORKSTREAM_STATUS_MATRIX.md) — Status matrix across WS1–WS10.
* [`NEXTERAS_API_INVENTORY.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_API_INVENTORY.md) — Complete 79-endpoint API & SDK contract inventory.
* [`NEXTERAS_PRODUCTION_GAP_ANALYSIS.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_PRODUCTION_GAP_ANALYSIS.md) — P0–P3 gap resolution status & remaining cutover items.
* [`NEXTERAS_PRODUCTION_ROADMAP.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_PRODUCTION_ROADMAP.md) — Sequenced 9-phase roadmap & execution completion summary.
* [`NEXTERAS_ARCHITECTURE_AND_DATA_FLOW.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_ARCHITECTURE_AND_DATA_FLOW.md) — Unified architecture reconciliation & historical diagrams.
* [`NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md) — Proposed 9-logical-agent LangGraph architecture & Human-in-the-Loop approval design *(awaiting sign-off)*.
* [`NEXTERAS_LIVE_ENGINEERING_PROGRESS.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_LIVE_ENGINEERING_PROGRESS.md) — Phase-by-phase verified implementation & test ledger.
* [`NEXTERAS_DEPLOYMENT_GUIDE.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_DEPLOYMENT_GUIDE.md) — Local Docker (`54332`/`6379`) & production Vercel/Cloud Run operations guide.
* [`NEXTERAS_ENVIRONMENT_CONFIGURATION.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_ENVIRONMENT_CONFIGURATION.md) — Environment variable inventory & safe credential management.

---

## Historical Pre-Consolidation Forensic Baseline (Preserved Below)

**Audit Date:** 2026-11-26  
**Active Checkout Inspected Initially:** `ml` (`f14190d615e1db038384567fe27080a943b8eff2`) + full Git object inspection across `origin/main`, `origin/develop`, `origin/sanju`, `origin/ml`, and `origin/ramaraju` (`aa19954db106ef0e069f9b651b672bf138a9684b`).  
**Audit Posture:** **Strictly Read-Only Forensic Audit** (historical baseline preserved below verbatim).

---

## Executive Engineering Dashboard

### Reality Check Across Four Evidence Layers
A principal audit separates **code existing in Git** from **code proven end-to-end against live services**. Today, NexteRaS consists of **three impressive but disconnected engineering silos**: modern mock UI (`origin/develop`), strong CPU ML/LangGraph components (`origin/ml`), and solid DB/Auth/ARQ backend foundations (`origin/ramaraju`). Because these silos remain unmerged and unintegrated against live services, end-to-end user value does not yet execute.

| System Domain | Authoritative Branch | Source Code Status | Mocked / Offline Test Evidence | Live Infra Verification | Prod Deploy Readiness | Overall Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Frontend UI (29 Routes & 3D)** | `origin/develop` / `ml` | Strong UI scaffold; uses `useMockStore` fixtures everywhere | `tsc --noEmit`, `next lint`, `9/9` JS unit tests PASS (`ml`) | UI does not call live APIs (`0` `fetch`/SDK calls) | `NO` (`next-intl`, Sentry, PostHog, Vercel CD missing) | **`MOCK/STUB`** *(UI Shell Complete, Data Mocked)* |
| **Supabase Auth UI & Middleware** | `origin/ramaraju` *(stale UI base)* | `@supabase/ssr` client, middleware, PKCE callback exist | `auth.test.js` (`5` tests on `origin/ramaraju`, not run here) | **Not verified live** (0 env vars, Supabase stopped) | `NO` (middleware fails open on missing env; protects only 6 paths) | **`IMPLEMENTED, NOT VERIFIED`** *(Conflicts w/ `develop`)* |
| **Backend API Core (CRUD & JWT)** | `origin/ramaraju` (`aa19954`) | 22 routes, 9 repos, 8 services, PyJWT verifier, RFC7807 errors | Unit tests (`80` funcs on `ramaraju`) mock DB/Redis/JWKS | **Not verified live** (`Docker` offline, Postgres closed) | `NO` (no rate limits, security headers, or Cloud Run CD) | **`IMPLEMENTED, NOT VERIFIED`** *(Unmerged)* |
| **Database Schema & RLS** | `origin/ramaraju` + `ml` | 25 tables, 5 migrations (`ramaraju`) + `20261125000001` (`ml`), strict RLS | Static SQL migration checks on `ramaraju` | **0 migrations applied locally** (`supabase status` failed on `ml` `major_version: 16`) | `NO` (`storage.buckets` missing; `opportunity_eligibility` missing 7 ML columns) | **`PARTIALLY COMPLETE`** |
| **Vector Pipeline (WS2)** | `origin/ramaraju` | ARQ `embed_opportunity`, `backfill_missing_embeddings`, `384`-dim HNSW | Unit tests mock `_FakeEncoder`/`_FakeRepo`/`_FakeArqPool` | **Not verified live** (Redis `6379` closed; `search_similar_by_vector` has 0 callers) | `NO` (`768`-dim unused; student/resume vectors missing) | **`PARTIALLY COMPLETE`** |
| **ML Engines & Training (ML)** | `ml` (`f14190d`) | `minilm-nexteras-v1`, multilingual encoder, NLI, eligibility, extractor, ranker | **`32/32` ML tests PASS** offline w/ `HF_HUB_OFFLINE=1` + `5/5` API ML tests PASS | Gemini adapters blocked (`GEMINI_API_KEY` unset); stateless HTTP only | `NO` (all `/ml/*` endpoints unauthenticated; `26.79s` torch import; `~1.2 GB` RSS) | **`IMPLEMENTED, NOT VERIFIED`** *(Offline OK, Auth/DB Missing)* |
| **Resume Intelligence (WS3)** | Split (`ml` + `ramaraju`) | JSON CRUD (`ramaraju`); `.txt/.md/.json/.pdf` extractor (`ml`) | Extraction & JSON CRUD tested separately offline | **Missing live Storage upload, `.docx`, `/tailor`, `/pdf`** | `NO` (0 Storage buckets/RLS, `python-docx` absent, `pymupdf` missing on `ramaraju`) | **`PARTIALLY COMPLETE`** |
| **Olostep (WS4) & Crustdata (WS5)** | None | `apps/api/app/integrations/__init__.py` empty everywhere | None | **0%** (`OLOSTEP_API_KEY` & `CRUSTDATA_API_KEY` unset) | `NO` | **`NOT IMPLEMENTED`** |
| **Gemini Live Voice (WS6)** | Split (`ramaraju` + `ml` + `develop`) | Text Gemini REST (`ml`); WS ticket/ack stub (`ramaraju`); `setTimeout` mock (`develop`) | WS ticket tests mocked; Gemini backend error-blocked tests pass | **No Gemini Live WS proxy, no WebAudio/AudioWorklet, no ASR/TTS** | `NO` (`mr` & `gu` missing across stack) | **`MOCK/STUB`** *(Live Voice Missing)* |
| **Background Workers (WS7)** | `origin/ramaraju` | ARQ `WorkerSettings` + embedding tasks only | Unit-tested w/ fakes on `ramaraju` | Redis offline; absent on `ml` (`Dockerfile.worker` breaks) | `NO` (0 `cron_jobs`, 0 research/resume/browser jobs) | **`PARTIALLY COMPLETE`** |
| **LangGraph Agents (WS8)** | `ml` (`f14190d`) | Compiled `StateGraph` + `MemorySaver` + M11 `interrupt()` prototype | Tested offline w/ `MemorySaver` (`test_langgraph_and_api_e2e.py` PASS) | `apps/api/app/agents/` empty; disconnected from `human_approvals` | `NO` (needs `PostgresSaver`, API wiring & real tools) | **`PROTOTYPE`** |
| **Playwright Automation (WS9)** | None (`pyproject.toml` extra) | Optional dependency declaration only | None | **0 automation code**, Chromium absent from `Dockerfile.worker` | `NO` | **`NOT IMPLEMENTED`** |
| **SDK (`packages/api-client`)** | `origin/ramaraju` / `ml` | Typed fetch wrapper (6 methods) | `api-client.test.ts` (`7` tests on `ramaraju`) | **4 of 6 methods hit `404`/`405` against `ramaraju` backend** | `NO` | **`PARTIALLY COMPLETE`** *(Broken Contracts)* |

---

## 1. Audit Mandate & Verification Discipline
1. **Truth over Optimism:** Prior QA files ([`FINAL_REPOSITORY_AUDIT.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/qa/FINAL_REPOSITORY_AUDIT.md), [`REPOSITORY_AUDIT.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/qa/REPOSITORY_AUDIT.md)) and Ramaraju's audit claimed high completion inside isolated silos. This audit independently inspects **all branches**, local services, test mocks, and contract seams.
2. **Environment Probe Result (Checked 2026-11-26):**
   * **All 21 NexteRaS env vars** (`SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `DIRECT_URL`, `REDIS_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_LIVE_WEBSOCKET_URL`, `OLOSTEP_API_KEY`, `CRUSTDATA_API_KEY`, `NEXT_PUBLIC_API_BASE_URL`, `SENTRY_DSN`, `POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_KEY`, `ML_MATCHING_MODEL_PATH`, `HF_HOME`) are **`MISSING (Unset)`**. Only `.env.example` files exist; zero `.env` or `.env.local` files exist on disk.
   * **Local Ports (`127.0.0.1`):** `54321`, `54322`, `54323` (Supabase), `6379` (Redis), `8000` (API), `3000` (Web) are all **CLOSED (`False`)**.
   * **Local Tools & Daemons:** `git`, `node`, `pnpm`, `python` (`3.13` host / `3.11.16` `ml/.venv`), `uv`, `docker`, `supabase` (scoop), `gh`, `playwright` exist on PATH, **but** `docker info` fails (Docker Desktop engine pipe unavailable) and `supabase status` on `ml` fails immediately (`Failed reading config: Invalid db.major_version: 16`).

---

## 2. Git Repository, Branch Topology, PRs & Divergence Forensics

### 2.1 Branch State Snapshot
| Branch | Local HEAD | Remote HEAD (`origin/*`) | Sync State | File Count (`git ls-tree`) | Role & Contents |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`main`** | `9cee065d9793cec25db919b2922a7294ff99f29c` | `9cee065d9793cec25db919b2922a7294ff99f29c` | Synced | `113` | Initial baseline + branch protection template |
| **`develop`** | `52ffca3708411479b02d94bcb99d8ae7ed566767` | `bfea70995bdf2141a69a02b6dcedb173ffe34ff3` | **Behind 2 commits** | `245` *(remote)* | Merged frontend (`sanju` + PRs #1–#6) |
| **`sanju`** | — | `a8022a3771ab6045fd505b6c111ebeea34724a69` | Origin only (aligned w/ `develop`) | `245` | Completed mock frontend + 3D + Agent Control UI |
| **`ml`** *(Checked Out)* | `f14190d615e1db038384567fe27080a943b8eff2` | `f14190d615e1db038384567fe27080a943b8eff2` | Synced | `330` | `sanju` frontend + `ml/` + stateless `/api/v1/ml/*` + 3 commits (`d03aad0`, `6efef77`, `f14190d`) |
| **`ramaraju`** | `2242d24d1a249abc85cde3d5986a2ad49bb066f7` | `aa19954db106ef0e069f9b651b672bf138a9684b` | **Behind 4 commits** | `227` *(remote)* | 4 unmerged backend/WS2/Auth commits (`dafbb36`, `cc1c5a5`, `39d5e7d`, `aa19954`) built on stale `2242d24` UI |

* **Working Tree (`ml`):** Clean relative to tracked files; untracked artifacts present: [`ml/artifacts/minilm-nexteras-v1/`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/artifacts/minilm-nexteras-v1/) (`model.safetensors` `90,864,192` bytes gitignored/untracked checkpoint), [`deliverables/`](file:///d:/ai%20career%20intelligence%20autonomous%20system/deliverables/), and pre-existing [`docs/NEXTERAS_END_TO_END_INTEGRATION_READINESS.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_END_TO_END_INTEGRATION_READINESS.md) (written prior to Ramaraju's `17:38–17:39` commits, now outdated on WS1/WS2/Auth).
* **Pull Requests (GitHub):** 6 closed/merged PRs (`#1`–`#6`), **0 open PRs**. Neither `origin/ramaraju` (`aa19954`) nor `origin/ml` (`f14190d`) has an open PR into `develop`.
* **Latest Commit Timestamps on `origin/ramaraju` (`2026-11-26`):** `dafbb36` (Backend Tasks 1–3), `cc1c5a5` (`17:38:59 +0530` Backend Foundation + Resumes + Voice Sessions), `39d5e7d` (`17:39:10 +0530` WS2 Embedding Pipeline + ARQ), `aa19954` (`17:39:14 +0530` Supabase Auth Integration on old UI).

### 2.2 Critical Divergence & Conflict Matrix
Computing common merge bases (`merge-base(ramaraju, ml) = 2242d24`, `merge-base(develop, ramaraju) = 2242d24`, `merge-base(sanju, ml) = a8022a3`):
* **`origin/ramaraju` vs `origin/develop` conflicts (7 files):** `.gitignore`, `apps/web/package.json`, `apps/web/src/app/layout.tsx`, `apps/web/src/app/login/page.tsx`, `apps/web/src/app/page.tsx`, `apps/web/src/app/settings/page.tsx`, `pnpm-lock.yaml` — plus `origin/ramaraju` omits/deletes **19 `apps/web` routes** and `components/landing/*` introduced later on `sanju`/`develop`.
* **`origin/ramaraju` vs `origin/ml` conflicts:** All 7 above **plus** `apps/api/app/api/v1/router.py`, `apps/api/app/core/config.py`, `apps/api/pyproject.toml` (where `ml` has `ml/` deps + `/ml/*` router while `ramaraju` has `pyjwt`/`pgvector`/`arq`/lifespan + CRUD/WS router) and overlapping dual-vector SQL migrations (`20261125000001` on `ml` vs `20261126000002` on `ramaraju`).

---

## 3. Workstream Verification Summary (WS1–WS10)
Complete evidence breakdowns live in [`NEXTERAS_WORKSTREAM_STATUS_MATRIX.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_WORKSTREAM_STATUS_MATRIX.md):
* **WS1 (Declared: `COMPLETED`):** Actually **`IMPLEMENTED, NOT VERIFIED`** — solid CRUD/JWT/migrations sit on `origin/ramaraju`, untested against live Postgres/Redis, unmerged with `ml`/`develop`, missing real eligibility, resume upload/storage, and company/university portals.
* **WS2 (Declared: `COMPLETED`):** Actually **`PARTIALLY COMPLETE` / `IMPLEMENTED, NOT VERIFIED`** — worker, hash dedup, and repository exist on `origin/ramaraju`, unit-tested only with mocks, AND `EmbeddingRepository.search_similar_by_vector()` has **zero callers**.
* **WS3 (`NEXT TO START`):** **`PARTIALLY COMPLETE`** (split JSON CRUD on `ramaraju` + PDF/text extractor on `ml`; missing multipart upload, `.docx`, Storage bucket/policies, tailoring, PDF generation).
* **WS4 (Olostep) & WS5 (Crustdata):** **`NOT IMPLEMENTED`** (`0%`).
* **WS6 (Gemini/Voice):** **`PARTIALLY COMPLETE`** (REST text adapters on `ml`) / **`MOCK/STUB`** (Live Voice WS + UI drawer).
* **WS7 (Workers/Scheduling):** **`PARTIALLY COMPLETE`** (ARQ embeddings on `ramaraju`; 0 crons; broken on `ml`).
* **WS8 (LangGraph):** **`PROTOTYPE`** (`MemorySaver` prototype on `ml`; intentionally deferred).
* **WS9 (Playwright):** **`NOT IMPLEMENTED`** (`0%`).
* **WS10 (Frontend/Deploy/Obs):** **`PARTIALLY COMPLETE`** (Mock UI on `develop`, stale Auth on `ramaraju`, missing Sentry/PostHog/Vercel/Cloud Run/9-language parity).

---

## 4. Intended vs. Current Architecture Reconciliation
See [`NEXTERAS_ARCHITECTURE_AND_DATA_FLOW.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_ARCHITECTURE_AND_DATA_FLOW.md) for all **8 Mermaid diagrams** illustrating current siloed realities vs target end-to-end execution. Key architectural divergences:
1. **TanStack Query & `next-intl`:** Specified in [`FRONTEND_STATE_ARCHITECTURE.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_STATE_ARCHITECTURE.md) and [`FRONTEND_IMPLEMENTATION_READINESS_CHECKLIST.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_IMPLEMENTATION_READINESS_CHECKLIST.md), **not installed** in [`apps/web/package.json`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/package.json) on any branch.
2. **Framer Motion / GSAP:** Architecture table mentions Motion & GSAP; frontend uses pure CSS keyframe animations in `ScrollReveal` + Three.js (`R3F`) + external Spline iframe (`https://my.spline.design/...` in [`GenkubRobot.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/landing/GenkubRobot.tsx)) — CSS + R3F is lightweight and working well without needing GSAP bloat.
3. **Host Compute Constraints vs Architecture:** Heavy PyTorch + Transformers load (`26.79s` cold import locally, `~1.2 GB` RSS per transformer model) justifies separating the ML inference / ARQ embedding worker from the latency-sensitive Cloud Run FastAPI gateway (which matches separate `Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.ml`, though missing Cloud Run manifests).

---

## 5. Backend API Architecture & Dual-Router Audit
Detailed in [`NEXTERAS_API_INVENTORY.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_API_INVENTORY.md):
* **`origin/ramaraju` (`apps/api/app/api/v1/router.py` + `voice.py`):** 22 HTTP routes + 1 WS route (`/api/v1/health`, `/health/ready`, `/users/me*`, `/career-passport*`, `/opportunities*`, `/applications*`, `/agents/approvals*`, `/notifications*`, stub `/eligibility/evaluate`, `/resumes*`, `/voice/sessions`, `/voice/tickets`, `WS /voice/stream`).
* **`ml` (`apps/api/app/api/v1/router.py` + `ml.py`):** 7 ML routes + `/health` + stub `/opportunities` returning `[]`.
* **Critical Contract Collision:** Both branches define `POST /api/v1/eligibility/evaluate` with **incompatible schemas** (`{opportunity_id}` stub on `ramaraju` vs stateless `{student, opportunity}` payload on `ml`). Furthermore, **zero** endpoints in [`ml.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/api/v1/ml.py) enforce authentication (`Depends(get_current_user)`).

---

## 6. Database Schema, Supabase Migrations & Missing Columns
Inspected across all 5 migrations on `origin/ramaraju` (`20261123000001`, `20261126000001`–`000004`) plus [`20261125000001_add_minilm_384_embeddings.sql`](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261125000001_add_minilm_384_embeddings.sql) on `ml`:
* **25 Tables Created & RLS Hardened (`origin/ramaraju`):** Includes `profiles`, `student_profiles`, `user_preferences`, `career_passports`, `education`, `skills`, `resumes`, `resume_versions`, `resume_customizations`, `organizations`, `opportunities`, `opportunity_sources`, `opportunity_eligibility`, `opportunity_embeddings`, `opportunity_monitors`, `saved_opportunities`, `applications`, `human_approvals`, `notifications`, `voice_sessions`, `conversations`, `conversation_messages`, `agent_sessions`, `agent_events`, `browser_execution_logs`, `analytics_events`.
* **Security Strengths (`origin/ramaraju`):** `handle_new_user()` uses `SECURITY DEFINER SET search_path = public, extensions` (`20261126000001`); client `INSERT`/`DELETE` revoked on `applications` and `UPDATE` restricted to safe columns on `profiles`/`notifications` (`20261126000003`); `20261126000004` adds embedding integrity `CHECK` constraint (`embedding_status <> 'ready' OR embedding_minilm_384 IS NOT NULL`).
* **Database Gaps Blocking Core Features:**
  1. **`public.opportunity_eligibility` lacks 7 fields** required by `ml`'s [`EligibilityEngine`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/eligibility/engine.py): `eligible_academic_years`, `max_active_backlogs`, `min_experience_months`, `allowed_locations`, `remote_allowed`, `required_citizenship`, `preferred_skills`.
  2. **Zero Storage Buckets or `storage.objects` Policies:** Even though `supabase/config.toml` sets `[storage] enabled = true`, no bucket SQL exists.
  3. **9 Unwired Tables:** `education`, `resume_versions`, `resume_customizations`, `opportunity_sources`, `opportunity_monitors`, `agent_sessions`, `agent_events`, `browser_execution_logs`, `conversations`, `conversation_messages`, `analytics_events` have no FastAPI endpoints.
  4. **Local Supabase Config Bug on `ml`:** `ml` [`supabase/config.toml`](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/config.toml) sets `major_version = 16`, crashing local CLI `2.x` (`origin/ramaraju` updated it to `17`).

---

## 7. Vector Database & Embedding Pipeline Audit (WS2 & 768 vs 384 Dim)
* **Why Both `768` and `384` Dimensions Exist:** Initial schema created `embedding vector(768)` + `ivfflat` assuming Gemini `text-embedding-004`. Later, `ml` trained local `minilm-nexteras-v1` (`384`-dim) and added `embedding_minilm_384 vector(384)` (`HNSW`). Both `ml` (`20261125000001`) and `origin/ramaraju` (`20261126000002`) intentionally keep both columns side-by-side (`768` nullable, `384` active).
* **Actual Runtime Pipeline (`origin/ramaraju`):**
  * `CanonicalEmbeddingAdapter` (`app/ml/embeddings.py`) strictly produces L2-normalized **384-dim** float32 vectors (`minilm-nexteras-v1` or `all-MiniLM-L6-v2` fallback). **Nothing populates `embedding` (768-dim).**
  * `opportunity_text.py` hashes canonical opportunity text (`sha256`), avoiding redundant re-embedding on metadata changes.
  * `EmbeddingRepository` handles `upsert_pending`, `save_ready`, `mark_failed`, stale/retry isolation, and **`search_similar_by_vector()`**.
* **Audit Failures on WS2:**
  1. **Vector search is orphaned:** `search_similar_by_vector()` has **zero callers** in any FastAPI endpoint or service; `POST /api/v1/opportunities/discover` executes plain SQL `ILIKE` filtering.
  2. **No Student / Resume Vectors:** Only `opportunity_embeddings` exists; student profiles and career passports have no stored vectors (`pgvector` ANN matching must compute query vector dynamically at search time until added).
  3. **Zero Live Proof:** All 17 WS2 unit tests (`test_embeddings_repository`, `test_ws2c_*`, `test_ws2d1–3_*`) mock `SentenceTransformer`, `AsyncSession`, and `ArqRedis`; `test_ws2d4_pipeline_live.py` was not executed live (Docker/Postgres/Redis offline).

---

## 8. Machine Learning Models, Training, Benchmarks & Hardware Footprint
Inspected [`ml/model_configs/ml_registry.yaml`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/model_configs/ml_registry.yaml), [`ml/evaluation/latest_evaluation_report.json`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/evaluation/latest_evaluation_report.json), and [`ml/datasets/README.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/datasets/README.md), and ran real offline model inference tests (`HF_HUB_OFFLINE=1` from local `%USERPROFILE%\.cache\huggingface\hub`):

| Model / Module | Checkpoint / Algorithm | Observed Benchmark Evidence (Synthetic Datasets) | Measured Memory & CPU Speed | Gaps & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **`semantic_matcher`** | [`ml/artifacts/minilm-nexteras-v1`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/artifacts/minilm-nexteras-v1/) (`all-MiniLM-L6-v2` contrastive fine-tune, 384-dim) | `curriculum_v2` (88 triplets: 48/16/24): Test R@1 improved `0.7917 -> 1.0000`, mean margin `+0.0982 -> +0.2357` | `90.86 MB` safetensors; RSS `707.2–867.9 MB`; `60.04 ms`/query | Trained on 88 synthetic triplets only; untested on real external JDs |
| **`multilingual_encoder`** | `paraphrase-multilingual-MiniLM-L12-v2` (384-dim) + script/hinglish regex | 24-query synthetic benchmark: `en` `1.0`, `hinglish` `1.0`, `hi` `0.6667`, `ta` `0.6667`, `bn` `0.3333`, `kn` `0.3333`, `te` `0.0`, `ml` `0.0` | RSS `1227.9 MB` | Weak zero-shot retrieval for South/East Indic scripts (`te`/`ml`/`bn`/`kn` flagged weak); **`mr`/`gu` missing** |
| **`evidence_nli_verifier`** | `cross-encoder/nli-deberta-v3-small` / lexical fallback | 9 synthetic claims: DeBERTa `0.8889` acc; lexical fallback `0.7778` overall (`0.3333` supported) | RSS `1207.7 MB` | Sync HTTP API defaults `ENABLE_PRETRAINED_NLI=false` (lexical fallback runs in sync requests) |
| **`resume_structured_extractor`** | Deterministic regex/section parser + optional Gemini REST JSON | 4 synthetic resumes: `0` hallucinated skills (`test_extraction_benchmark_zero_hallucinations`) | CPU instant without LLM | **No `.docx` parser**, no table/OCR layout robustness, Gemini blocked w/o key |
| **`deterministic_eligibility`** | 10-rule hard filter engine ([`ml/src/eligibility/engine.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/eligibility/engine.py)) | 8 edge-case synthetic scenarios passing cleanly | Sub-ms CPU | 7 rule fields missing in Supabase `public.opportunity_eligibility` |
| **`opportunity_ranker`** | Deterministic 6-weight ranker (+ gated LightGBM/XGBoost) | Excludes expired/ineligible/duplicate items (`ranking_benchmark.json`) | Sub-ms CPU | GBDT permanently gated until `MIN_LABELED_SESSIONS_FOR_GBDT = 500` collected |

* **Hardware & Cold-Start Reality:** In observed tests, [`ResourceManagedModelCache`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/infrastructure/runtime.py) (`max_loaded_models=1`) prevents simultaneous model OOM, **but** importing `torch` alone measured **`26.79s`** on local Windows CPU, `test_langgraph_and_api_e2e.py` took **`94.80s`**, and `test_model_inference_real.py` took **`106.21s`**. Production containers must pre-bake Hugging Face caches and allocate >= `2–4 GiB` RAM per ML/ARQ worker.

---

## 9. Resume Intelligence & Supabase Storage Audit (WS3)
* **Backend CRUD (`origin/ramaraju`):** [`resumes.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/) implements `GET/POST /api/v1/resumes`, `GET/DELETE /api/v1/resumes/{id}` over JSON payloads only.
* **ML Extractor (`ml`):** [`extractor.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/extraction/extractor.py) extracts `.txt`, `.md`, `.json`, `.pdf` (`pymupdf`), validates uploads (`10 MB`, safe filenames), redacts PII in logs, and validates Gemini JSON output strictly against source text.
* **What Is Missing:**
  1. Multipart file upload endpoint (`POST /api/v1/resumes/upload`) with magic-byte MIME verification.
  2. `.docx` parsing (`python-docx` absent; `extractor.py` explicitly raises `ValueError("Unsupported extension: .docx")`).
  3. `pymupdf` missing from `origin/ramaraju:apps/api/pyproject.toml`.
  4. Supabase Storage private `resumes` bucket, `storage.objects` RLS policies, and signed upload/download URL generation.
  5. Resume tailoring endpoint (`/resumes/{id}/tailor`), PDF compiler (`/resumes/{id}/pdf`), and services for `resume_versions` & `resume_customizations`.

---

## 10. Deterministic Eligibility & Opportunity Ranking Audit
* `ml` [`EligibilityEngine`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/eligibility/engine.py) & [`engine`/`parser`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/eligibility/parser.py) properly distinguish required vs preferred skills, B.Tech/B.E. equivalencies, CGPA vs %, backlogs, experience, location, remote eligibility, citizenship, and deadline expiry — while `origin/ramaraju:POST /api/v1/eligibility/evaluate` remains a hardcoded `score=0.0` stub.
* Reconciling both requires merging the engines, updating `public.opportunity_eligibility` SQL columns, and mapping authenticated student DB profiles into the evaluation call.

---

## 11. External Intelligence Providers: Olostep (WS4) & Crustdata (WS5)
* **Code Audit Finding:** `apps/api/app/integrations/__init__.py` contains **one placeholder comment line across all branches** (`ml`, `develop`, `ramaraju`, `main`).
* **Missing Entirely:** Zero Olostep HTTP clients (`/searches`, `/scrapes`, `/answers`, `/crawl`, `/maps`, `/batch`, monitors), zero Crustdata firmographic/people/job enrichment clients, zero HTML sanitization for scraped postings, zero rate-limit/retry backoff wrappers, zero scheduled monitor handlers, and both API keys unset.

---

## 12. Gemini LLM, Gemini Live & 9-Language Voice Pipeline (WS6)
* **Backend Gemini (`ml`):** [`gemini_backends.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/integration/gemini_backends.py) provides synchronous REST clients via `httpx` for JSON extraction fallback and Indic-to-English query translation (`GEMINI_API_KEY` unset -> blocked in production).
* **Voice WebSocket (`origin/ramaraju`):** [`app/voice/tickets.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/) + [`app/api/v1/voice.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/) implement secure single-use 30s Redis WS tickets (`GETDEL`), **but** `WS /api/v1/voice/stream` only acknowledges binary PCM bytes with `{"event": "audio_received", "bytes": N}` and handles `session_init` / `interrupted` / `ping` echoes. Zero Gemini Live upstream WebSocket connection, zero ASR/TTS, and zero Gemini function calling exist.
* **Frontend Voice UI (`origin/develop` / `ml`):** [`VoiceDrawer.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/dashboard/VoiceDrawer.tsx) fakes listening and answers via `setTimeout(1800ms)` + `setTimeout(700ms)` over 7 hardcoded queries; zero WebAudio `AudioContext` / `AudioWorklet` / browser `WebSocket` code exists in `apps/web/src`.
* **9-Language Product Mandate vs. 7-Language Repo Implementation:**
  * Architecture docs, [`packages/shared-config/src/index.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/packages/shared-config/src/index.ts), [`apps/api/app/schemas/common.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/schemas/common.py), [`VoiceDrawer.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/dashboard/VoiceDrawer.tsx), and [`ml/src/multilingual/preprocessing.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/multilingual/preprocessing.py) only configure **7 languages** (`en, hi, te, ta, kn, ml, bn` + `hinglish`).
  * **Marathi (`mr`) and Gujarati (`gu`) are completely absent across all layers** — including missing Unicode Gujarati block detection (`U+0A80–U+0AFF`) and Devanagari lexical disambiguation (`mr` vs `hi` would currently misclassify Marathi as `hi`), missing UI locale files (`next-intl` not installed), and missing Noto Indic fonts.

---

## 13. Background Workers & ARQ Scheduling Audit (WS7)
* `origin/ramaraju` builds ARQ [`WorkerSettings`](file:///d:/ai%20career%20intelligence%20autonomous%20system/) (`max_jobs=10`, `job_timeout=300`, `max_tries=3`) with DB/Redis lifecycle hooks and two tasks (`embed_opportunity`, `backfill_missing_embeddings`).
* **Critical Gaps:**
  1. Missing from `ml` & `develop` (where [`infra/docker/Dockerfile.worker`](file:///d:/ai%20career%20intelligence%20autonomous%20system/infra/docker/Dockerfile.worker) command `arq app.tasks.worker.WorkerSettings` crashes).
  2. Zero `cron_jobs` configured (no deadline alerts, periodic Olostep monitors, Crustdata refreshes, or stale vector sweeps).
  3. Zero resume parsing or Playwright execution jobs.
  4. Never executed against a real Redis instance (`127.0.0.1:6379` closed).

---

## 14. LangGraph Orchestration & Human Approval Gate (WS8)
* **Prototype Status (`ml`):** [`langgraph_adapter.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/integration/langgraph_adapter.py) compiles a genuine LangGraph `StateGraph` (`PERCEIVE -> REASON -> PLAN -> DELEGATE_VERIFY -> [M11 interrupt()] -> ACT / ACT_BLOCKED -> EVALUATE_ADAPT`) verified offline with `MemorySaver` (`test_langgraph_and_api_e2e.py`). Because full agent development was intentionally deferred, this prototype is sound.
* **Integration Work Remaining:**
  * `apps/api/app/agents/` is empty across all branches.
  * Replace in-memory `MemorySaver` with `PostgresSaver`, persist execution telemetry into `agent_sessions` and `agent_events`, trigger/resume graph execution from `POST /api/v1/agents/approvals/{id}/decision` (`origin/ramaraju`), and replace simulated [`AgentControlCenter`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/agent-control/agentData.ts) UI data with real SSE/WS events.

---

## 15. Playwright Browser Automation & Execution Safety (WS9)
* **Audited Status: `NOT IMPLEMENTED`** (`0` application automation files under `apps/api` or `ml`; `playwright>=1.47.0` sits only in optional `pyproject.toml` extras; `Dockerfile.worker` lacks Chromium binary/dependencies).
* Safety policy documented in [`ADR-005-browser-automation-approval-gate.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/decisions/ADR-005-browser-automation-approval-gate.md) & [`TEST_STRATEGY.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/qa/TEST_STRATEGY.md) rightly specifies pausing cleanly (`requires_manual_completion`) upon encountering Cloudflare/CAPTCHAs without attempting bypasses — all implementation remains to be built.

---

## 16. Frontend Architecture, UI Routes, 3D & State Management
* **`origin/develop` & `ml` (`apps/web`):**
  * **29 Routes Exist:** Public marketing (`/`, `/about`, `/features`, `/how-it-works`, `/ai-agents`, `/voice-ai`), Auth/Onboarding (`/login`, `/register`, `/forgot-password`, `/role-selection`, `/onboarding`), Student (`8` routes including `/overview`, `/opportunities`, `/opportunities/[id]`, `/career-passport`, `/resume`, `/applications`, `/interview`, `/analytics`, `/notifications`, `/settings`), `/agent-control-center`, Company (`4` routes: `dashboard`, `applicants`, `candidates`, `create`), University (`3` routes: `dashboard`, `students`, `verification`).
  * **Zero Live Data:** Recursive grep confirmed **0** `fetch(`, `new WebSocket`, `useQuery`, `@opportunity-os/api-client`, `@supabase/*`, `@sentry/*`, `posthog-js`, or `next-intl` usages anywhere in `apps/web/src` on `ml`/`develop`. Every workspace reads Zustand [`mockStore.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/lib/mock-data/mockStore.ts).
  * **3D Stack:** Selective Three.js/R3F [`EcosystemScene.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/landing/ecosystem/EcosystemScene.tsx) + external Spline iframe [`GenkubRobot.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/landing/GenkubRobot.tsx) + mobile fallback [`CampusFallback.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/components/landing/hero/CampusFallback.tsx).
* **`origin/ramaraju` Auth Conflict:** Added `@supabase/ssr` Auth UI onto stale pre-redesign UI, deleting 19 modern routes and landing components — requires careful surgical grafting, not naive git merging.

---

## 17. TypeScript SDK (`packages/api-client`) & Shared Contracts
* Even against `origin/ramaraju`, **4 of 6 methods in `@opportunity-os/api-client` fail**:
  * `getProfile()` -> `GET /users/me/profile` -> **`404`** (`/users/me` + `/users/me/student-profile`).
  * `discoverOpportunities(q)` -> `GET /opportunities/discover?q=...` -> **`405`** (`GET /opportunities` / `POST /opportunities/discover`).
  * `checkEligibility(id)` -> `GET /eligibility/evaluate/{id}` -> **`405`** (`POST /eligibility/evaluate`).
  * `approveAction(id, approved)` -> `POST /agents/approval/{id}` -> **`404`** (`POST /agents/approvals/{id}/decision`).
* Missing SDK wrappers for Resumes, Career Passport, Notifications, Voice Tickets/Sessions, Education, and ML routes.
* Shared config (`@opportunity-os/shared-config`) defines only 7 languages (omitting `mr`, `gu`).

---

## 18. Authentication, Authorization & Multi-Role RBAC
* **Backend Auth (`origin/ramaraju`):** Strong PyJWT `JWTVerifier` supporting `HS256`, `ES256`, and `RS256` + JWKS rotation handling + strict `anon` role rejection (`403`) + RFC7807 `401` errors + `sub` UUID enforcement preventing spoofing.
* **Security Defects Found:**
  1. **Unauthenticated ML Routes (`ml`):** All 7 routes in [`apps/api/app/api/v1/ml.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/api/v1/ml.py) lack `Depends(get_current_user)`.
  2. **Next.js Middleware Fail-Open (`origin/ramaraju`):** `apps/web/src/middleware.ts` bypasses auth checks (`NextResponse.next`) whenever Supabase env vars are missing, and only protects `6` routes (`omitting /overview, /notifications, /onboarding, /role-selection, /agent-control-center, /company/*, /university/*`).
  3. **No Multi-Role RBAC Implementation:** `company/*` (4 pages) and `university/*` (3 pages) exist in the UI with zero JWT role claims (`role-selection` mocked) and zero role-restricted backend routes/tables.

---

## 19. Security, Privacy, Secrets Hygiene & Compliance
* **Git History Secret Scan (`git rev-list --all`):** Verified **0 real secret hits** (API keys, private keys, JWT literals) across all commits on all branches. `.env*` commits touched only `.example` templates.
* **ML Security Guards ([`ml/src/infrastructure/security.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/infrastructure/security.py)):** Path traversal sanitization, `10 MB` upload size limit, regex `redact_pii()` log masking, and fail-closed `Gemini` placeholder key rejection pass unit tests.
* **Missing Production Security Controls:**
  1. **Zero Rate Limiting:** No `slowapi` or Redis rate-limiting middleware exists on FastAPI routes (login/ML/upload abuse vector).
  2. **Zero Security Headers:** Neither FastAPI (`main.py`) nor Next.js ([`next.config.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/next.config.ts)) sets `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, or `Strict-Transport-Security`.

---

## 20. Test Suite Inventory, Mocking Boundaries & Observed Results

### 20.1 Executed Locally on Current Checkout (`ml` — `f14190d`)
| Check / Suite | Command Executed | Exact Observed Outcome | Scope & Limitations |
| :--- | :--- | :--- | :--- |
| **Workspace Type-Check** | `pnpm -r run type-check` | **PASS (0 errors)** | 5/6 workspace targets checked |
| **Workspace Lint** | `pnpm -r run lint` | **PASS** (`next lint`: `0 warnings/errors`) | Static ESLint 9 across `apps/web`; packages echo ok |
| **Frontend JS Unit Tests** | `pnpm -r run test` | **PASS (`9/9` passed in `968.23ms`)** | Static config/UI/adapter assertions only (`apps/web/tests/*.test.js`); zero live browser/API tests |
| **API Style & Format** | `apps/api/.venv/Scripts/ruff.exe check apps/api` & `format --check` | **PASS** (`28 files formatted`) | `ml` API subset only |
| **API Mypy (In-Package)** | `cd apps/api && .\.venv\Scripts\mypy.exe app` | **PASS** (`0 issues in 21 files`) | Run from repo root (`mypy.exe apps/api/app`) **FAILED with `11 errors in 6 files`** resolving into `ml/src/*` where stubs are absent in `apps/api/.venv` |
| **API Pytest (`apps/api/.venv`)** | `apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests -v` | **PASS (`5 passed, 1 warning in 5.94s`)** | `test_ml_routes.py` (`3`) + `test_sanity.py` (`2`); fallback mode w/o `ml` deps |
| **API Pytest (`ml/.venv`)** | `ml\.venv\Scripts\python.exe -m pytest apps\api\tests -v` | **PASS (`5 passed, 2 warnings in 4.99s`)** | Missing `pytest-asyncio` in `ml/.venv` triggers `asyncio_mode` config warnings |
| **ML Fast Unit/Adapters** | `HF_HUB_OFFLINE=1` `ml\.venv\Scripts\python.exe -m pytest ml\tests -m "not slow" --ignore=ml/tests/test_langgraph_and_api_e2e.py` | **PASS (`27 passed, 3 deselected in 13.95s`)** | Offline synthetic fixtures; mocked Gemini backend |
| **ML E2E + LangGraph** | `HF_HUB_OFFLINE=1` `ml\.venv\Scripts\python.exe -m pytest ml\tests\test_langgraph_and_api_e2e.py` | **PASS (`2 passed in 94.80s`)** | Real FastAPI `TestClient` + real trained `minilm-nexteras-v1` + compiled `StateGraph` w/ `MemorySaver` (`94.80s` cold load) |
| **ML Slow Real Inference** | `HF_HUB_OFFLINE=1` `ml\.venv\Scripts\python.exe -m pytest ml\tests\test_model_inference_real.py` | **PASS (`3 passed in 106.21s`)** | Real CPU inference on 4 cached HF models (`minilm-nexteras-v1`, `all-MiniLM-L6-v2`, `paraphrase-multilingual-MiniLM-L12-v2`, `nli-deberta-v3-small`) |

### 20.2 Unexecuted Tests Sitting on Unmerged `origin/ramaraju` (`aa19954`)
* **Unit Tests (`80` functions across `12` files):** Static inspection confirmed `test_auth_jwt.py` (12), `test_migrations_static.py` (11), `test_health_endpoints.py` (8), `test_w1d_foundation_gaps.py` (8), `test_embeddings_repository.py` (7), `test_ws2c_*` (7), `test_resumes_api.py` (6), `test_ws2d1–3_*` (15), `test_db_session.py` (4), `test_sanity.py` (2) — **all mock Postgres, Redis, JWKS, ARQ, and SentenceTransformer (`_FakeDb`, `_FakeRepo`, `_FakeEncoder`, `_FakeArqPool`)**.
* **Integration Tests (`21` functions across `9` files):** `test_protected_routes_and_voice.py` (9), `test_ws2d4_pipeline_live.py` (3), `test_database_schema.py` (2), `test_repositories_live.py` (2), and 5 single-test live suites — **all require live Postgres/Redis (`skipif` offline) and were NOT executed in this environment**.
* **SDK/Web Auth Tests on `origin/ramaraju`:** `apps/web/tests/auth.test.js` (5), `packages/api-client/tests/api-client.test.ts` (7).

---

## 21. CI/CD Pipelines, Docker & Local Infrastructure
* **GitHub Workflows ([`.github/workflows/`](file:///d:/ai%20career%20intelligence%20autonomous%20system/.github/workflows/)):**
  * `backend-checks.yml` only triggers on `pull_request` (not `push`), only runs `apps/api/tests/unit` + `ruff` + `mypy` — **omits live integration Postgres/Redis service containers, `ml/tests`, and worker startup tests**.
  * `frontend-checks.yml` runs `type-check`, `lint`, `test`, `build` cleanly (`pnpm 12.4.2`).
  * Zero CD/deployment workflows exist for Vercel or Google Cloud Run.
* **Docker & Local Infra ([`infra/docker/`](file:///d:/ai%20career%20intelligence%20autonomous%20system/infra/docker/)):**
  * `Dockerfile.api`, `Dockerfile.web`, `Dockerfile.worker`, `Dockerfile.ml` exist. `Dockerfile.worker` breaks on `ml` because `app.tasks.worker` only exists on `origin/ramaraju`, and lacks Chromium/Playwright runtime binaries.
  * `origin/ramaraju:docker-compose.yml` improved local Supabase host routing & added `.dockerignore`, while `ml` `supabase/config.toml` has invalid `db.major_version = 16`.

---

## 22. Production Deployment, Observability & Analytics Audit
* **Vercel & Cloud Run:** **Zero** `vercel.json`, **zero** Cloud Run `service.yaml` / Terraform / `gcloud run deploy` manifests or scripts exist anywhere in the repo.
* **Monitoring (Sentry) & Analytics (PostHog):** Grep confirmed **zero** `sentry-sdk`, `@sentry/nextjs`, `posthog-python`, or `posthog-js` installations or initializations across all branches (`SENTRY_DSN`, `POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_KEY` all unset).
* **Prior Readiness Claims vs Reality:** `docs/qa/RELEASE_READINESS_CHECKLIST.md` leaves Sprint 1 feature gates unchecked (accurate), whereas older Phase 5 reports overstated production readiness relative to the real missing backend/ML/frontend wiring.

---

## 23. Student Core Capabilities Matrix (Capabilities 1–15)

| # | Intended Product Capability | Audited Readiness | Exact Current State |
| :---: | :--- | :--- | :--- |
| **1** | Multilingual voice onboarding | **`MOCK/STUB`** | `VoiceDrawer` uses `setTimeout`; `WS /voice/stream` acks bytes only; no Gemini Live or `mr`/`gu` |
| **2** | Build/maintain Career Passport | **`PARTIALLY COMPLETE`** | DB + CRUD API on `ramaraju` (no `education` route); UI mocked on `develop` |
| **3** | Create & analyze resumes | **`PARTIALLY COMPLETE`** | Extractor (`ml`) + JSON CRUD (`ramaraju`); no file upload, Storage, `.docx`, `/tailor`, or PDF |
| **4** | Discover live internships/hackathons/fellowships | **`MOCK/STUB`** | `POST /opportunities/discover` does SQL `ILIKE` on seeded rows; Olostep missing; UI mocked |
| **5** | Research companies/opps (Olostep/Crustdata) | **`NOT IMPLEMENTED`** | `0%` external integration code across all branches |
| **6** | Evaluate eligibility (rules + ML) | **`PARTIALLY COMPLETE`** | Real engines built offline (`ml`), stubbed on `ramaraju` API; DB missing 7 rule columns |
| **7** | Rank opportunities by suitability | **`PARTIALLY COMPLETE`** | Offline 6-weight ranker works (`ml`); disconnected from Postgres discovery; GBDT gated |
| **8** | Explain match / mismatch reasons | **`PARTIALLY COMPLETE`** | Explanation structures generated by `ml` engines; not returned by live DB routes or UI |
| **9** | Identify skill gaps & learning paths | **`PARTIALLY COMPLETE`** | Missing skill calculation exists in ML eligibility/ranking; curated learning paths are mock UI |
| **10** | Prepare tailored resumes/applications | **`NOT IMPLEMENTED`** | No `/resumes/{id}/tailor` or PDF generation; NLI verification exists standalone on `ml` |
| **11** | Execute application via Playwright | **`NOT IMPLEMENTED`** | Zero browser automation code across all branches |
| **12** | Explicit approval gate before submit | **`PROTOTYPE`** | Split: LangGraph M11 `interrupt()` (`ml`) + Approvals DB API (`ramaraju`) — disconnected |
| **13** | Monitor opps, companies, deadlines | **`NOT IMPLEMENTED`** | Schema tables exist (`opportunity_monitors`); 0 workers, crons, or Olostep/Crustdata monitors |
| **14** | Multilingual interview preparation | **`MOCK/STUB`** | Hardcoded Q&A state in [`apps/web/src/app/interview/page.tsx`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/app/interview/page.tsx); 0 backend routes |
| **15** | Application history & analytics | **`MOCK/STUB`** | Applications CRUD on `ramaraju` (no resume/Playwright tracking); Analytics UI mocked (`analytics_events` empty) |

---

## 24. Critical Technical Risks & Architectural Debt Register
1. **Unmerged Branch Silos Risk:** Attempting a direct `git merge` of `origin/ramaraju` into `origin/develop` or `ml` will collide on `apps/web` (`19` deleted routes in `ramaraju` + `layout/login/page/settings` conflicts) and `apps/api` (`router.py`/`config.py`/`pyproject.toml`).
2. **Dual Vector Schema & Orphaned Search Debt:** `embedding vector(768)` takes schema space with zero writers while `search_similar_by_vector()` on `384`-dim has zero readers.
3. **Unauthenticated Heavy Compute DoS Risk:** `ml.py` exposes synchronous CPU-bound transformer endpoints (`up to 1.2 GB RSS`, multi-second cold-start) with zero auth and zero rate limiting.
4. **In-Memory LangGraph Loss Risk:** `MemorySaver` loses workflow state on container restart or scale-out replica switches.
5. **9-Language vs 7-Language Compliance Debt:** Omitting Marathi (`mr`) and Gujarati (`gu`) excludes two major Indian student demographics, while offline zero-shot embeddings fail (`0.0` R@1) on Telugu (`te`) and Malayalam (`ml`) without mandatory LLM/translation fallback.

---

## 25. Cross-Branch Integration & Merge Strategy
Execute strictly in this sequence on a dedicated integration branch off `origin/develop` (never pushing directly to `main`):
1. **Base from `origin/develop` (`bfea709`):** Keeps all 29 modern UI routes, landing 3D, Agent Control UI, and passing `pnpm` CI checks.
2. **Integrate `origin/ramaraju` Backend & Migrations (`aa19954`) selectively:** Bring in `supabase/` (`major_version = 17` + 5 migrations), `infra/`, `docker-compose.yml`, `.dockerignore`, and the entire `apps/api/` backend core (FastAPI lifespan, security, repos, services, ARQ workers, unit/integration tests).
3. **Graft `origin/ramaraju` Supabase Auth UI cleanly:** Copy `apps/web/src/lib/supabase/*`, `src/lib/auth/redirect.ts`, `src/app/auth/callback/route.ts`, `src/components/auth/AuthProvider.tsx`, `src/middleware.ts`, and `apps/web/tests/auth.test.js`, then wire Auth context/forms into the **modern `develop` UI** `layout.tsx`, `login/page.tsx`, `register/page.tsx`, `settings/page.tsx` (fixing `middleware.ts` fail-open bug + expanding protected route list).
4. **Integrate `origin/ml` (`f14190d`) ML Subsystem & Adapter:** Bring in `ml/`, `apps/api/app/ml/adapter.py`, `apps/api/app/schemas/ml.py`, `apps/api/app/api/v1/ml.py` (adding `Depends(get_current_user)`!), reconcile dual-vector migration `20261125000001` vs `20261126000002`, unify `apps/api/pyproject.toml` deps, and replace `origin/ramaraju`'s stub `POST /api/v1/eligibility/evaluate` with real DB + ML evaluation.

---

## 26. Immediate Local Unblocking Checklist
1. Start Docker Desktop (`LinuxEngine` pipe must come online).
2. Copy `.env.example` / `apps/web/.env.local.supabase-local.example` into root `.env`, `apps/api/.env`, and `apps/web/.env.local`; supply real `GEMINI_API_KEY` (required for extraction/translation tests beyond offline rules), and provision `OLOSTEP_API_KEY` / `CRUSTDATA_API_KEY` before Phase 5.
3. Update `supabase/config.toml` (`major_version = 17`, already fixed on `origin/ramaraju`) -> run `supabase start` and verify all migrations apply cleanly.
4. Boot Redis container -> verify `arq app.tasks.worker.WorkerSettings` and execute `origin/ramaraju`'s 21 integration tests live (`pytest apps/api/tests/integration`).

---

## 27. Conclusion: Direct Answers to 22 Key Engineering Questions

1. **Can the app run end-to-end right now on any single branch?**
   **No.** `origin/develop` & `ml` run UI mocks only (`0` backend/auth calls); `origin/ramaraju` has backend + Auth + worker code but breaks 4/6 SDK routes, lacks ML/LangGraph engines, deletes 19 modern UI routes, and has unverified DB/Redis locally.
2. **Are Ramaraju's latest backend and vector commits in GitHub?**
   **Yes — on `origin/ramaraju` (`aa19954`, pushed `2026-11-26 17:39 +0530`), NOT merged into `develop`, `ml`, or `main`.** Local `ramaraju` is 4 commits stale (`2242d24`).
3. **Is WS1 (`Backend & Database Foundation`) truly COMPLETED?**
   **No — it is `IMPLEMENTED, NOT VERIFIED` (with missing capabilities).** Core repositories/services/JWT/migrations look well-engineered statically, **but** live Postgres tests have not been executed here, `/eligibility/evaluate` is a stub, `education`/analytics/role endpoints are absent, and it isn't merged.
4. **Is WS2 (`Vector Database Pipeline`) truly COMPLETED?**
   **No — it is `PARTIALLY COMPLETE` / `IMPLEMENTED, NOT VERIFIED`.** Ingestion worker (`embed_opportunity`, `backfill_missing_embeddings`) exists on `origin/ramaraju` (unit-tested with mocks only), **but** `EmbeddingRepository.search_similar_by_vector()` has **zero API callers**, and `vector(768)` remains unused.
5. **What is causing the 768-dim vs 384-dim discrepancy, and is it dangerous?**
   Initial DDL defined `embedding vector(768)` (`IVFFlat`) for Gemini embeddings; `ml` trained a `384`-dim MiniLM model (`embedding_minilm_384`, `HNSW`). Migrations safely allow both columns alongside `20261126000004`, **so it does not crash writes**, but in code only `384`-dim is ever written/queried (`768` is orphaned dead weight unless explicitly supported or dropped).
6. **Is the ML subsystem real or mocked?**
   **Real locally (`32/32` ML tests passed offline with real PyTorch/HF checkpoints).** `minilm-nexteras-v1`, `paraphrase-multilingual-MiniLM-L12-v2`, `nli-deberta-v3-small`, and the deterministic extractor/eligibility/ranker engines work locally on CPU — though trained/benchmarked on small synthetic datasets (`88` triplets, `24` queries, `9` claims) and GBDT is gated (`<500` interactions).
7. **Does the ML backend work inside FastAPI right now?**
   **Only in stateless isolation on the `ml` branch**, unauthenticated (`no JWT`), disconnected from Postgres (`apps/api/tests`: `5/5` passed in `5.94s`; real E2E test: `2/2` passed in `94.80s`). It does **not** exist yet on `origin/ramaraju` or `develop`.
8. **Does resume PDF/DOCX upload & Supabase Storage work?**
   **No.** `origin/ramaraju` only stores JSON resumes; `ml` only extracts `.txt/.md/.json/.pdf` (`pymupdf`); `.docx` explicitly raises `ValueError`; there is no multipart `/upload` endpoint, no Storage bucket/policies, no `/tailor`, and no `/pdf` export.
9. **Does Olostep integration exist anywhere?**
   **No (`NOT IMPLEMENTED`, `0%`).**
10. **Does Crustdata integration exist anywhere?**
    **No (`NOT IMPLEMENTED`, `0%`).**
11. **Does Gemini Live real-time voice work?**
    **No.** Frontend `VoiceDrawer.tsx` is a `setTimeout` simulation; `origin/ramaraju:WS /voice/stream` is an authenticated PCM frame-ack stub with no Gemini Live upstream connection, no ASR/TTS, and no function calling.
12. **Do all 9 required Indian languages work?**
    **No — two languages (`Marathi [mr]` and `Gujarati [gu]`) are completely missing across frontend, backend, schemas, and ML.** Among the configured 7 + `hinglish`, offline multilingual vector R@1 scored `0.0` on Telugu (`te`) and Malayalam (`ml`), requiring Gemini translation fallback.
13. **Are Redis & ARQ background jobs running and tested?**
    ARQ embedding tasks exist on `origin/ramaraju` (unit-tested with `_FakeArqPool` only), **missing on `ml`**, **zero `cron_jobs` exist**, and Redis is offline locally (`6379` closed).
14. **Is LangGraph working in production?**
    **No — intentionally a `PROTOTYPE`.** Works offline with `MemorySaver` + M11 `interrupt()` on `ml`, not wired into Postgres checkpoints, `human_approvals` DB, or FastAPI routes.
15. **Is Playwright application automation implemented?**
    **No (`NOT IMPLEMENTED`, `0%`).**
16. **Does the Next.js frontend actually talk to FastAPI or Supabase today?**
    On `develop`/`ml`: **No (`0` real API calls, `useMockStore` only).** On `ramaraju`: Supabase Auth exists on an obsolete UI subset, and `packages/api-client` fails with `404`/`405` on 4 of 6 methods.
17. **Can merging `origin/ramaraju` into `origin/develop` cause data loss or major regressions?**
    **Yes, if blindly auto-merged.** `origin/ramaraju` deletes 19 modern routes and `components/landing/*` relative to `develop`, and overwrites redesigned pages (`login`, `settings`, `layout`, `page`).
18. **Are there security vulnerabilities in the current code?**
    Yes: (a) all 7 `/api/v1/ml/*` routes on `ml` are **unauthenticated**, (b) `origin/ramaraju` `middleware.ts` **fails open** when Supabase env vars are missing and only covers 6/29 paths, (c) **zero rate limiting** (`slowapi`/Redis) and **zero HTTP security headers** exist. No secrets were leaked in Git history.
19. **Are Vercel, Cloud Run, Sentry, and PostHog configured?**
    **No.** None of those 4 production operational systems exist in code, packages, or workflows yet (only base Dockerfiles exist).
20. **How long does local cold ML inference take, and what does that mean for Cloud Run?**
    `import torch` took `26.79s` and end-to-end API/LangGraph execution took `94.80s` (`test_model_inference_real.py` `106.21s`), hitting `707–1228 MB` RSS per model. Cloud Run ML workers need `>= 2–4 GiB` RAM, pre-cached weights, min-instances (avoiding cold starts), and async ARQ offloading rather than blocking gateway HTTP workers.
21. **Can `@opportunity-os/api-client` be used as-is?**
    **No.** 4 of 6 methods target broken paths/verbs (`404`/`405`), and it lacks Resumes, Passport, Notifications, Voice, Education, and ML endpoints.
22. **How close is NexteRaS to genuine production readiness?**
    The individual building blocks (29-page frontend, CPU ML models/LangGraph prototype, Supabase SQL schema/RLS, FastAPI repos/ARQ workers) represent substantial engineering progress (~35–40% structural asset coverage, <10% integrated E2E runtime verification). Reaching true production requires completing branch unification + live DB/Auth/SDK repair + real Resume Storage/DOCX/PDF + Olostep/Crustdata + Gemini Live Voice (9 langs) + Persistent LangGraph/Playwright + Cloud Run/Sentry observability.

---

## 28. Next 30 Prioritized Engineering Tasks (Single-Developer Order)

1. Provision local Docker Desktop, Redis, and `.env` / `.env.local` secrets (`SUPABASE_*`, `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`).
2. Create an integration branch from `origin/develop` (`bfea709`), inspect/cherry-pick/merge `origin/ramaraju` (`aa19954`) backend (`apps/api/`, `supabase/`, `infra/`, `docker-compose.yml`, `.dockerignore`) without reverting the 19 modern `apps/web` routes.
3. Graft `origin/ramaraju`'s Supabase SSR files (`lib/supabase/*`, `lib/auth/redirect.ts`, `auth/callback/route.ts`, `AuthProvider.tsx`, `middleware.ts`) onto modern `develop` `layout.tsx`, `login/page.tsx`, `register/page.tsx`, `settings/page.tsx`.
4. Fix `middleware.ts` fail-open behavior on missing Supabase env vars and protect all private routes (`/overview`, `/career-passport`, `/opportunities/*`, `/resume`, `/applications`, `/interview`, `/analytics`, `/notifications`, `/settings`, `/agent-control-center`, `/company/*`, `/university/*`).
5. Port `ml/` and `apps/api/app/{ml/adapter.py,schemas/ml.py,api/v1/ml.py}` onto the unified branch; merge dependencies in `apps/api/pyproject.toml` (adding `pymupdf`, `python-docx`, `pyjwt`, `pgvector`, `arq`, `slowapi`).
6. Reconcile SQL migrations (`20261125000001` vs `20261126000002` + `major_version = 17`), start local Supabase CLI (`supabase start`), and verify clean schema bootstrap.
7. Run `origin/ramaraju`'s 21 live integration tests against local Postgres + pgvector + Redis to establish true runtime baseline.
8. Add JWT `Depends(get_current_user)` authentication and input size limits to all `/api/v1/ml/*` routes and delete stub `GET /api/v1/opportunities` from `ml`.
9. Fix all 4 broken HTTP routes in `packages/api-client/src/index.ts` and add client methods for Resumes, Career Passport, Notifications, Voice Tickets/Sessions, Education, and ML endpoints.
10. Add API migration adding `eligible_academic_years`, `max_active_backlogs`, `min_experience_months`, `allowed_locations`, `remote_allowed`, `required_citizenship`, `preferred_skills` to `public.opportunity_eligibility` (plus decision on deprecating/retaining unused `embedding vector(768)`).
11. Replace `POST /api/v1/eligibility/evaluate` stub with real DB profile/passport/opportunity fetch + ML `EligibilityEngine` + match explanation payload.
12. Wire `EmbeddingRepository.search_similar_by_vector()` + `CanonicalEmbeddingAdapter` into `POST /api/v1/opportunities/discover` & `BaselineOpportunityRanker`.
13. Implement `GET/POST/DELETE /api/v1/users/me/education` endpoints over `public.education` and include academic records in Career Passport responses.
14. Register ARQ `cron_jobs` (`backfill_missing_embeddings` sweep, deadline monitor/notifications) in `app/tasks/worker.py`.
15. Add Redis-backed rate limiting (`slowapi` or custom token bucket) + FastAPI/Next.js HTTP security headers (`CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `HSTS`).
16. Install `@tanstack/react-query` in `apps/web` cleanly and migrate `/login`, `/register`, `/overview`, `/career-passport`, `/opportunities`, `/opportunities/[id]`, `/applications`, and `/notifications` off `useMockStore` onto real API + Supabase sessions.
17. Create SQL migration adding private `resumes` Supabase Storage bucket and `auth.uid()`-scoped `storage.objects` RLS policies.
18. Add `.docx` extraction (`python-docx`) + magic-byte MIME validation to `ResumeExtractionService` and implement `POST /api/v1/resumes/upload` + async extraction job.
19. Implement grounded resume tailoring (`POST /api/v1/resumes/{id}/tailor`) backed by Career Passport + `EvidenceVerificationService`, and ATS PDF rendering (`GET /api/v1/resumes/{id}/pdf`) using `resume_versions` / `resume_customizations`.
20. Wire `/resume` UI editor to real file upload, NLI grounding badges, tailored versions, and PDF downloads.
21. Implement Olostep client (`apps/api/app/integrations/olostep.py`) with search/scrape/crawl/maps/batch/monitor ingestion into `opportunities` + `opportunity_sources` + auto-enqueue `embed_opportunity`.
22. Implement Crustdata client (`apps/api/app/integrations/crustdata.py`) enriching `public.organizations` with verification status, headcount, and hiring velocity + periodic ARQ watcher.
23. Expand multilingual support from 7 to **9 languages** by adding **Marathi (`mr`)** and **Gujarati (`gu`)** to `shared-config`, DB/API enums, ML script/lexical detector, Noto fonts, `next-intl` catalogs, and Gemini fallback prompts.
24. Replace `VoiceDrawer.tsx` `setTimeout` simulation with real `AudioContext` / `AudioWorkletNode` 16kHz PCM streaming + jitter-buffered playback + text fallback.
25. Upgrade `WS /api/v1/voice/stream` to bidirectional Gemini Live API proxy with turn interruption, persistence to `voice_sessions`/`conversation_messages`, and Gemini function calling.
26. Move `ml/src/integration/langgraph_adapter.py` into `apps/api/app/agents/` backed by `PostgresSaver`, persisting telemetry to `agent_sessions` & `agent_events`.
27. Link LangGraph M11 `interrupt()` directly to `public.human_approvals` so `POST /agents/approvals/{id}/decision` resumes suspended runs and triggers post-approval execution; wire `/agent-control-center` to live SSE/WS telemetry.
28. Implement Playwright Chromium execution worker (`apps/api/app/automation/`) logging dry-run screenshots/diffs into `browser_execution_logs` and halting safely on CAPTCHAs/MFA (`requires_manual_completion`).
29. Implement `company/*` & `university/*` RBAC claims/endpoints, real `/interview` & `/analytics` APIs (logging anonymized sessions toward the `500`-row GBDT threshold), plus Sentry + PostHog telemetry across Web, API, and Worker.
30. Add Vercel & Cloud Run deployment configs (with pre-baked `HF_HOME` and >= `2–4 GiB` worker memory), expand GitHub Actions CI to include integration + worker + Playwright E2E checks on push/PR, and verify staging before promoting to `main`.
