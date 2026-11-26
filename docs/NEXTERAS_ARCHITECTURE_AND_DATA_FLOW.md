# NexteRaS (Opportunity OS) — Architecture & Data Flow Audit

**Updated:** 2026-11-26 (`feat/phase0-1-core-infra` post-consolidation build)  
**Pre-Consolidation Audit Baseline:** `origin/main`, `origin/develop`, `origin/sanju`, `origin/ml`, and `origin/ramaraju`

---

## Post-Consolidation Architecture Reconciliation (`feat/phase0-1-core-infra`)

After merging PRs `#10`–`#12` into `develop` and building Phases 0–9 on `feat/phase0-1-core-infra`, the fragmented three-branch reality documented below has been unified into the single integrated target system:
* **Frontend + Auth + i18n:** Next.js 15 (`29` pages / `33` build routes) uses `@tanstack/react-query` hooks ([`useOpportunityOs.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/lib/queries/useOpportunityOs.ts)) over `@opportunity-os/api-client`, fail-closed SSR [`middleware.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/middleware.ts), typed 9-language catalog [`messages.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/lib/i18n/messages.ts), and `AudioStreamingService` (`audioStreamer.ts`).
* **Unified FastAPI + Intelligence Layer:** Single gateway ([`main.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/main.py)) exposing 78 OpenAPI HTTP operations + `WS /api/v1/voice/stream`, JWT-guarded `/ml/*`, Redis rate limiting, OWASP security headers, Sentry/PostHog (`observability.py`), `OlostepClient`, `CrustdataClient`, `GeminiClient` + `GeminiLiveRelay`, and Student/Company/University RBAC.
* **Postgres 17 + pgvector + Storage:** `29` `public` tables across `10` ordered SQL migrations, `student_embeddings` + `opportunity_embeddings` (`embedding_minilm_384` HNSW), private `resumes` Storage bucket + RLS, and live `search_similar_by_vector()`.
* **Background Workers & Safe Browser Sandbox:** ARQ `WorkerSettings` (`7` tasks, `3` crons) + Playwright Chromium `playwright_runner.py` with mandatory pre-submit screenshot pause (`approval_requests` `403` guard) and CAPTCHA/MFA halt.
* **Autonomous Agent Gate:** Typed `PostgresSaver` contracts ([`contracts.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/agents/contracts.py)) & read-only session telemetry are live; full autonomous orchestration (`orchestrator.py`) is designed in [`NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md`](file:///d:/ai%20career%20intelligence%20autonomous%20system/docs/NEXTERAS_AGENT_ARCHITECTURE_PROPOSAL.md) and **paused awaiting explicit approval**.

---

## Historical Pre-Consolidation Forensic Baseline (Preserved Below)

**Legend:**
- `[IMPLEMENTED - ml]` — Exists on `ml` / `origin/ml` branch.
- `[IMPLEMENTED - ramaraju]` — Exists on `origin/ramaraju` branch (unmerged).
- `[IMPLEMENTED - develop]` — Exists on `origin/develop` / `origin/sanju` / `ml` frontend.
- `[STUB]` / `[MOCK]` — Hardcoded, simulated, or placeholder response.
- `[PROTOTYPE]` — Compiled/tested in memory only; not DB-backed or wired into API runtime.
- `[NOT IMPLEMENTED]` — Absent across all branches.
- `[DISCONNECTED]` — Implemented in isolation but lacking caller or upstream/downstream wiring.

---

## 1. Intended vs. Current System Architecture Comparison

NexteRaS is designed as a cohesive, voice-first, multilingual (9 Indian languages required: `en, hi, te, ta, bn, mr, gu, kn, ml`; only 7 + `hinglish` configured) autonomous career operating system. In reality, **no single branch runs the complete architecture today**: frontend innovation lives on `origin/develop` and `ml`, ML/LangGraph prototypes live on `ml`, and DB/Auth/ARQ/FastAPI core services live on unmerged `origin/ramaraju`.

| Architecture Layer | Intended Technology | Current Implemented State | Verification Status | Branch(es) |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend App** | Next.js 15, React 19, TypeScript, Tailwind | 29 App Router pages on `develop`/`ml` driven strictly by Zustand `useMockStore`; stale subset (10 routes deleted/reverted) + `@supabase/ssr` Auth UI added on `origin/ramaraju` | `next lint`, `tsc --noEmit`, `9/9` JS unit tests pass on `ml`; `next build` & live API integration unverified across merged branches | `ml` / `origin/develop` vs `origin/ramaraju` |
| **3D & Motion** | Spline, R3F / Three.js, Motion / GSAP | Custom Three.js `EcosystemScene` (`R3F`) + external Spline iframe (`GenkubRobot.tsx`) + CSS `ScrollReveal`; zero Framer Motion / GSAP packages installed | Renders in static tests (`landing-hero.test.js`); zero live WebGL/browser performance audit executed | `origin/develop` / `ml` |
| **i18n / Localization** | 9 Indic languages (`next-intl`, Noto fonts) | Only 7 languages configured (`en, hi, te, ta, kn, ml, bn` in `APP_CONFIG`); zero `next-intl` package or message catalogs; Marathi (`mr`) & Gujarati (`gu`) absent everywhere | Config contract checked; UI copy is English-only outside hardcoded `VoiceDrawer` demo phrases | All branches (gap) |
| **Backend API** | FastAPI + Pydantic v2 | Diverged into two incompatible routers: 22 DB/JWT/WS/stub routes on `origin/ramaraju` vs 7 stateless ML routes on `ml` | Unit-tested with fake repos/Redis on `origin/ramaraju` (not executed live in this env); 3 ML routes tested on `ml` (`test_ml_routes.py`) | Split: `origin/ramaraju` & `ml` |
| **Database & Vectors** | Supabase PostgreSQL 17 + `pgvector` | 25 tables, strict RLS (`20261126000001`/`000003`), dual vector columns (`vector(768)` + `vector(384)` HNSW), pipeline state (`20261126000004`) | Static SQL migration regex tests exist; **0 live Postgres migrations applied or queried** (`Docker` offline, `supabase status` failed on `ml`) | `origin/ramaraju` (+ `20261125000001` on `ml`) |
| **Auth & Storage** | Supabase Auth (JWT) + Supabase Storage | PyJWT HS256/ES256/RS256 verifier + `@supabase/ssr` middleware on `origin/ramaraju`; **zero storage buckets or storage policies defined** | JWT verifier unit-tested with mocked JWKS; E2E Supabase signup/login & Storage upload **NOT VERIFIED** | `origin/ramaraju` |
| **Primary LLM & Voice** | Gemini + Gemini Live WebSocket API | Text-only Gemini REST adapters (`httpx`) on `ml`; WS ticket store + PCM ack loop on `origin/ramaraju`; **no Gemini Live relay, no WebAudio client** | Unit/mock tests only (`GEMINI_API_KEY` missing); live Gemini API unverified | Split / `[NOT IMPLEMENTED]` |
| **ML Pipeline** | PyTorch, HF Sentence Transformers, scikit-learn | Fine-tuned `minilm-nexteras-v1` (384-dim), `paraphrase-multilingual-MiniLM-L12-v2`, `nli-deberta-v3-small`, deterministic eligibility/extractor/ranker | Offline unit tests + synthetic benchmarks executed; live latency/accuracy on real student data unverified; LightGBM ranker gated (`<500` rows) | `ml` |
| **Web / Company Intel** | Olostep + Crustdata | **0 HTTP clients, 0 schemas, 0 worker jobs** (`apps/api/app/integrations/__init__.py` is empty comment across all branches) | `[NOT IMPLEMENTED]` | None |
| **Agent Orchestration** | LangGraph + PostgreSQL checkpointer | Cyclic graph `build_nexteras_career_workflow` with `MemorySaver` + M11 `interrupt()` in `ml/src/integration/` (`apps/api/app/agents/` is empty) | `[PROTOTYPE]` (in-memory only; no `PostgresSaver`, no API trigger) | `ml` |
| **Browser Automation** | Playwright | `playwright` listed only as optional `automation` dependency extra in `apps/api/pyproject.toml`; 0 automation runners | `[NOT IMPLEMENTED]` | None |
| **Background Workers** | Redis + ARQ | ARQ worker (`app/tasks/worker.py`) + `embed_opportunity` / `backfill_missing_embeddings` on `origin/ramaraju`; absent on `ml` | Unit-tested with `_FakeRedis` / `_FakeRepo`; Redis offline locally | `origin/ramaraju` |
| **Deploy & Observability** | Vercel, Cloud Run, Sentry, PostHog | 4 Dockerfiles + Compose on `ramaraju`; **zero Vercel/Cloud Run manifests, zero Sentry SDK, zero PostHog SDK, zero rate limiting** | `[NOT IMPLEMENTED]` (infra code incomplete) | Partial Docker only |

---

## 2. Diagram 1 — Current Branch-Fragmented Reality vs. Target Architecture

```mermaid
flowchart TB
    subgraph Target["Intended Unified Architecture"]
        direction TB
        TWeb["Next.js 15 App + WebAudio + Supabase SSR"] --> TClient["api-client SDK"]
        TClient --> TAPI["FastAPI Gateway + PyJWT + Rate Limit"]
        TAPI --> TDB["Supabase Postgres 17 + pgvector + Storage"]
        TAPI --> TRedis["Redis + ARQ Workers"]
        TAPI --> TLG["LangGraph StateGraph + PostgresSaver"]
        TAPI --> TVoice["Gemini Live WS Relay"]
        TRedis --> TIntel["Olostep + Crustdata + ML Indexer"]
        TLG --> TPW["Playwright Sandbox After M11 Approval"]
    end

    subgraph Reality["Current Split Across 3 Unmerged Branches"]
        direction LR
        subgraph DevBranch["origin/develop and origin/sanju"]
            WUI["29 App Router Pages"] --> MockStore["Zustand useMockStore (Static Fixtures)"]
            VoiceUI["VoiceDrawer (setTimeout 7-Lang Mock)"] -.->|"No WS/AudioWorklet"| WUI
            AgentUI["Agent Control Center (Local Graph Mock)"] -.->|"No API Calls"| WUI
        end

        subgraph RamBranch["origin/ramaraju (aa19954) - Unmerged"]
            OldUI["Stale Web UI + Supabase SSR Auth"] -->|"4 Broken SDK Paths (404/405)"| ApiClient["packages/api-client"]
            RAPI["FastAPI Core (22 Routes + PyJWT)"] --> RDB["25 Tables + RLS + 384/768 Vectors"]
            RAPI --> RVoice["WS /voice/stream (Frame Ack Stub)"]
            RWorker["ARQ Embedding Worker"] --> RDB
            RAPI -.->|"Stub 0.0 / Missing Caller"| VecSearch["search_similar_by_vector (Uncalled)"]
        end

        subgraph MLBranch["ml (f14190d) - Checked Out Locally"]
            MAPI["FastAPI ML Router (7 Unauth Routes)"] --> MLCore["MiniLM-v1 + Multilingual + NLI + Eligibility + Extractor"]
            MLCore --> LGProto["LangGraph Prototype (MemorySaver)"]
        end
    end
```

---

## 3. Diagram 2 — Voice Interaction & Gemini Live Bidirectional Streaming Flow

Shows the exact divide between UI simulation (`VoiceDrawer.tsx`), unmerged ticket/WS plumbing (`origin/ramaraju`), and missing Gemini Live integration.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant UI as "VoiceDrawer.tsx [MOCK - develop/ml]"
    participant Auth as "Supabase Auth [IMPLEMENTED - ramaraju]"
    participant TicketAPI as "POST /api/v1/voice/tickets [IMPLEMENTED - ramaraju]"
    participant WS as "WS /api/v1/voice/stream [STUB - ramaraju]"
    participant GeminiLive as "Gemini Live Bidirectional API [NOT IMPLEMENTED]"
    participant TTS as "AudioContext PCM Playback [NOT IMPLEMENTED]"

    Note over Student,UI: Current experience on develop / ml branch
    Student->>UI: Selects 1 of 7 languages (mr/gu missing) & clicks Mic
    UI->>UI: setTimeout(1800ms) -> hardcodes DEMO_VOICE_QUERIES[lang]
    UI->>UI: setTimeout(700ms) -> displays canned response

    Note over Student,TTS: Partially built backend (origin/ramaraju) & missing E2E path
    Student->>Auth: Sign in & hold JWT [NOT WIRED in modern UI]
    Auth-->>Student: Supabase Access JWT
    Student->>TicketAPI: Request short-lived 30s WS ticket (Authorization Bearer JWT)
    TicketAPI-->>Student: {ticket, expires_in_seconds: 30} (Redis SET EX / dev memory)
    Student->>WS: WebSocket connect ?ticket=... [WebAudio 16kHz client NOT IMPLEMENTED]
    WS->>WS: Consume single-use ticket (Redis GETDEL)
    Student->>WS: Send binary PCM bytes / JSON {"type": "session_init"}
    WS-->>Student: Ack {"event": "audio_received", "bytes": N} (NO transcription/AI)
    WS-xGeminiLive: Forward PCM stream & tool definitions [NOT IMPLEMENTED]
    GeminiLive-xWS: Stream Indic voice audio + function calls [NOT IMPLEMENTED]
    WS-xTTS: Stream TTS/audio chunks back to browser [NOT IMPLEMENTED]
```

---

## 4. Diagram 3 — Opportunity Discovery, Company Enrichment & Vector Indexing Flow

Shows why `POST /api/v1/opportunities/discover` currently performs plain `ILIKE` SQL queries and never invokes external providers or vector similarity search.

```mermaid
flowchart TD
    Trigger["Discovery Trigger (Schedule / User Search)"] --> CRON{"ARQ Scheduled Jobs [NOT IMPLEMENTED]"}
    CRON -->|"Missing"| Olostep["Olostep Adapter (/searches, /scrapes, /crawl) [NOT IMPLEMENTED]"]
    CRON -->|"Missing"| Crust["Crustdata Adapter (/company/enrich) [NOT IMPLEMENTED]"]
    Olostep -.->|"Would ingest"| OppTable[("public.opportunities + opportunity_sources")]
    Crust -.->|"Would verify"| CompTable[("public.organizations + monitors")]

    APIDisc["POST /api/v1/opportunities/discover [IMPLEMENTED - ramaraju]"] --> SQLFilter["Plain SQL ILIKE & Filter Query"]
    SQLFilter --> OppTable

    OppWrite["Opportunity Created / Updated"] --> EmbTask["ARQ Task: embed_opportunity [IMPLEMENTED - ramaraju]"]
    Backfill["backfill_missing_embeddings() [IMPLEMENTED - ramaraju]"] --> EmbTask
    EmbTask --> Canon["Canonical Text + SHA256 Hash [IMPLEMENTED - ramaraju]"]
    Canon --> Encoder["CanonicalEmbeddingAdapter (384-dim MiniLM) [IMPLEMENTED - ramaraju/ml]"]
    Encoder -->|"Saves ready row"| EmbTable[("public.opportunity_embeddings (vector_384 HNSW + stale vector_768)")]

    EmbTable -->|"DISCONNECTED: 0 Callers in API/Services"| VecRepo["EmbeddingRepository.search_similar_by_vector() [IMPLEMENTED - ramaraju]"]
```

---

## 5. Diagram 4 — Resume Upload, Storage, Grounded Extraction & Tailoring Flow

Compares the currently separated pieces: mock frontend (`/resume`), JSON-only REST backend (`origin/ramaraju`), stateless extraction/NLI ML services (`ml`), and missing Storage/DOCX/PDF-export layers.

```mermaid
flowchart TD
    User["Student on /resume Page [MOCK - develop/ml]"] -->|"Currently toggles static mock JSON"| MockRes["Hardcoded Resume Preview"]
    User -->|"Intended: Upload PDF/DOCX"| UploadAPI["POST /api/v1/resumes/upload [NOT IMPLEMENTED]"]
    UploadAPI -->|"Missing Supabase Bucket & Policies"| SupaStore[("Supabase Storage Bucket [NOT IMPLEMENTED]")]
    UploadAPI --> FileVal["File Validation & Size Guard [IMPLEMENTED - ml/src/infrastructure/security.py]"]
    FileVal -->|"PDF works (pymupdf)"| PDFExt["PDF Text Extraction [IMPLEMENTED - ml]"]
    FileVal -->|"DOCX Unsupported (raises ValueError)"| DocxExt["DOCX Text Extraction [NOT IMPLEMENTED]"]
    PDFExt --> DetExt["Deterministic + Optional Gemini JSON Extractor [IMPLEMENTED - ml]"]
    DetExt -->|"Writes normalized JSON"| ResumeCrud["POST /api/v1/resumes (JSON CRUD Only) [IMPLEMENTED - ramaraju]"]
    ResumeCrud --> ResumeTables[("public.resumes, resume_versions, resume_customizations")]

    Passport[("public.career_passports [IMPLEMENTED - ramaraju]")] --> TailorSvc["Grounded Resume Tailoring Service [NOT IMPLEMENTED]"]
    ResumeTables --> TailorSvc
    TailorSvc -->|"Claims checked against premise"| NLIVer["EvidenceVerificationService (DeBERTa / Lexical Fallback) [IMPLEMENTED - ml]"]
    NLIVer --> ExportPDF["POST /resumes/id/pdf Generator [NOT IMPLEMENTED]"]
```

---

## 6. Diagram 5 — Hybrid Eligibility, Semantic Matching, Ranking & Explainability Pipeline

Illustrates the sharp contract mismatch between `origin/ramaraju` (stubbed endpoint + SQL schema without full fields), `ml` (full stateless ML pipeline), and `@opportunity-os/api-client`.

```mermaid
flowchart LR
    ClientCall["api-client checkEligibility(id) -> GET /eligibility/evaluate/id [405 BUG]"] -.->|"Broken route/verb"| RamAPI
    RamAPI["POST /api/v1/eligibility/evaluate [STUB - ramaraju]"] -->|"Always returns score=0.0"| StubOut["Static Msg: pending ML integration"]

    MLReq["POST /api/v1/ml/recommend-pipeline [UNAUTHENTICATED - ml]"] --> Multi["MultilingualUnderstandingService (paraphrase-MiniLM) [IMPLEMENTED - ml]"]
    Multi -->|"Direct fails often for te/ml/bn/kn -> Gemini fallback"| SemMatch["SemanticMatcher (minilm-nexteras-v1 384-dim) [IMPLEMENTED - ml]"]
    MLReq --> DetElig["EligibilityEngine: 10 Rule Families [IMPLEMENTED - ml]"]
    DetElig -->|"DB missing backlog/loc/year cols"| Ranker["BaselineOpportunityRanker (6 Weights) [IMPLEMENTED - ml]"]
    SemMatch --> Ranker
    Ranker -->|"Always excludes ineligible/expired/dup"| NLIGate["Verification Check [IMPLEMENTED - ml]"]
    NLIGate --> GBDT["Supervised GBDT Ranker [GATED: Needs >= 500 user logs]"]
```

---

## 7. Diagram 6 — LangGraph Orchestration & Human-in-the-Loop Approval Gate

Shows the end-to-end safety workflow where `ml` holds an in-memory LangGraph prototype (`MemorySaver`), `origin/ramaraju` holds DB approval persistence, and Playwright execution does not yet exist.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant UI as "Agent Control / Approvals UI [MOCK - develop]"
    participant LangGraph as "LangGraph StateGraph [PROTOTYPE - ml: MemorySaver]"
    participant ApprovalAPI as "Approvals API (/agents/approvals) [IMPLEMENTED - ramaraju]"
    participant ApprovalDB as "public.human_approvals + notifications [IMPLEMENTED - ramaraju]"
    participant Playwright as "Playwright Browser Executor [NOT IMPLEMENTED]"

    Student->>LangGraph: Trigger career pipeline (initial_state)
    LangGraph->>LangGraph: PERCEIVE -> REASON -> PLAN -> DELEGATE_VERIFY
    LangGraph-->>Student: HALT at M11 via LangGraph interrupt() (MemorySaver only)
    Note over LangGraph,ApprovalDB: Disconnected: LangGraph interrupt() does NOT write to public.human_approvals

    Student->>ApprovalAPI: GET /api/v1/agents/approvals/pending
    ApprovalAPI->>ApprovalDB: Query pending approval rows
    ApprovalDB-->>ApprovalAPI: Pending approval list
    ApprovalAPI-->>UI: Approvals payload [Currently unconsumed by UI]

    Student->>ApprovalAPI: POST /api/v1/agents/approvals/{id}/decision (approved=true)
    ApprovalAPI->>ApprovalDB: Atomic status update + transition application + create notification
    ApprovalAPI-->>Student: Approval record (Does NOT resume LangGraph or launch browser)

    LangGraph-xPlaywright: Command(resume={approved: true}) -> Execute portal form fill [NOT IMPLEMENTED]
```

---

## 8. Diagram 7 — Supabase Database, Dual Vector Dimensions & RLS Topology

Documents the 25 tables, security remediation policies (`20261126000001` & `000003`), dual vector columns (`vector(768)` unused vs `vector(384)` HNSW active in code), and unimplemented schemas.

```mermaid
erDiagram
    AUTH_USERS ||--|| PROFILES : "handle_new_user() trigger"
    PROFILES ||--o| STUDENT_PROFILES : "1-to-1"
    PROFILES ||--o| USER_PREFERENCES : "language (7 configured, missing mr/gu)"
    PROFILES ||--o{ CAREER_PASSPORTS : "1-to-many items"
    PROFILES ||--o{ EDUCATION : "no FastAPI endpoint yet"
    PROFILES ||--o{ RESUMES : "no Storage/PDF yet"
    RESUMES ||--o{ RESUME_VERSIONS : "no endpoint yet"
    RESUMES ||--o{ RESUME_CUSTOMIZATIONS : "no endpoint yet"
    PROFILES ||--o{ APPLICATIONS : "RESTRICTED client insert/delete"
    PROFILES ||--o{ HUMAN_APPROVALS : "append/decision controlled"
    PROFILES ||--o{ NOTIFICATIONS : "update read-only cols"
    PROFILES ||--o{ VOICE_SESSIONS : "session telemetry"
    OPPORTUNITIES ||--o| OPPORTUNITY_ELIGIBILITY : "missing backlog/loc/year cols"
    OPPORTUNITIES ||--o| OPPORTUNITY_EMBEDDINGS : "dual vector 768 unused / 384 HNSW"
    OPPORTUNITIES ||--o{ APPLICATIONS : "targets"
    OPPORTUNITY_SOURCES ||--o{ OPPORTUNITIES : "Olostep provenance (0 records)"
    AGENT_SESSIONS ||--o{ AGENT_EVENTS : "0 API endpoints"
    AGENT_SESSIONS ||--o{ BROWSER_EXECUTION_LOGS : "0 API endpoints"

    OPPORTUNITY_EMBEDDINGS {
        uuid id PK
        uuid opportunity_id FK
        vector embedding "vector(768) IVFFlat - UNPOPULATED"
        vector embedding_minilm_384 "vector(384) HNSW - ACTIVE IN CODE"
        text embedding_model_id
        text embedding_model_version
        text content_hash
        text embedding_status "pending | ready | failed"
        int retry_count
    }
```

---

## 9. Diagram 8 — Authentication, Security Boundaries & Production Deployment Topology

Highlights auth split-brain (`@supabase/ssr` on stale `origin/ramaraju` UI vs unauthenticated UI/ML routes on `ml`/`develop`) and missing production infrastructure.

```mermaid
flowchart TB
    Browser["Student Browser"] -->|"Vercel Target [NO VERCEL CONFIG]"| NextEdge["Next.js 15 Middleware"]
    NextEdge -->|"origin/ramaraju ONLY: fails open if env missing; covers only 6 paths"| SupaAuth["Supabase Auth Cloud/Local"]
    NextEdge -->|"develop / ml: NO middleware.ts"| MockPages["All 29 Pages Accessible Unauthenticated"]

    Browser -->|"Cloud Run Target [NO CLOUD RUN/CD CONFIG]"| FastAPI["FastAPI Container (Dockerfile.api)"]
    FastAPI -->|"origin/ramaraju routes"| PyJWT["JWTVerifier (HS256 / ES256 / RS256) + Reject anon role"]
    FastAPI -->|"ml routes (unmerged)"| NoAuth["UNAUTHENTICATED ML Routes!"]
    PyJWT -->|"Missing: SlowAPI rate limit, security headers, Sentry, PostHog"| SupaPG[("Supabase PostgreSQL 17 + RLS")]

    Worker["ARQ Container (Dockerfile.worker)"] -->|"Fails on ml (no worker.py); exists on ramaraju"| Redis[("Redis 7 Queue")]
    Worker -->|"No cron_jobs configured"| SupaPG
```
