# NexteRaS (Opportunity OS) — Complete API & Contract Inventory

**Updated:** 2026-11-26 (`feat/phase0-1-core-infra` post-consolidation build)  
**Pre-Consolidation Audit Baseline:** `origin/ramaraju` (`aa19954`), `ml` (`f14190d`), `origin/develop` (`bfea709`)

---

## Post-Consolidation Unified Backend API (`feat/phase0-1-core-infra`)

Following consolidation PRs `#10`–`#12` and Phases 0–9 hardening, FastAPI serves **78 OpenAPI HTTP operations + 1 WebSocket endpoint (`WS /api/v1/voice/stream`) = 79 unified `/api/v1` endpoints** across `router.py`, `ml.py`, `voice.py`, `automation.py`, and `portals.py`, all synchronized with [`packages/api-client/src/index.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/packages/api-client/src/index.ts) and verified by [`test_api_contracts.py`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/tests/unit/test_api_contracts.py):

* **Health & Security:** `GET /api/v1/health`, `GET /api/v1/health/ready`, Redis-backed rate limiting + OWASP headers (`SecurityHeadersMiddleware`), fail-closed Next.js SSR [`middleware.ts`](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/web/src/middleware.ts) (`33` Next.js build routes; `/auth/callback` PKCE handler).
* **Profiles, Education & Passport:** `GET/PUT /api/v1/users/me`, `GET/PUT /api/v1/users/me/student-profile`, `GET/POST/DELETE /api/v1/users/me/education`, `GET /api/v1/career-passport`, `POST /api/v1/career-passport/items`, `DELETE /api/v1/career-passport/items/{item_id}`.
* **Opportunities, Vector Search & Eligibility:** `GET /api/v1/opportunities`, `GET /api/v1/opportunities/saved`, `GET /api/v1/opportunities/{opportunity_id}`, `POST /api/v1/opportunities/{opportunity_id}/save`, `POST /api/v1/opportunities/discover` (calls `EmbeddingRepository.search_similar_by_vector()` + live eligibility), `POST /api/v1/eligibility/evaluate` (live Postgres + ML 10-rule evaluator).
* **Resumes & Storage (WS3):** `GET/POST /api/v1/resumes`, `POST /api/v1/resumes/upload` (multipart PDF/DOCX + Supabase Storage private bucket), `GET/DELETE /api/v1/resumes/{resume_id}`, `POST /api/v1/resumes/{resume_id}/analyze`, `POST /api/v1/resumes/{resume_id}/tailor`, `GET /api/v1/resumes/{resume_id}/versions`, `GET /api/v1/resumes/{resume_id}/pdf`, `GET /api/v1/resumes/{resume_id}/download-url`.
* **Olostep Research, Crustdata & Watchtower (WS4–WS5):** `POST /api/v1/research/discover`, `GET /api/v1/companies`, `GET /api/v1/companies/{org_id}`, `POST /api/v1/companies/enrich`, `GET/POST /api/v1/watchtower/monitors`, `DELETE /api/v1/watchtower/monitors/{monitor_id}`.
* **Multilingual Voice, AI Chat & Conversations (WS6):** `POST /api/v1/ai/chat`, `GET/POST /api/v1/voice/sessions`, `POST /api/v1/voice/tickets`, `WS /api/v1/voice/stream` (Gemini Live `BidiGenerateContent` relay + tool calls), `GET /api/v1/conversations`, `GET /api/v1/conversations/{conversation_id}`.
* **Applications, Approvals, Playwright Automation & Telemetry (WS7–WS9):** `GET/POST /api/v1/applications`, `GET/DELETE /api/v1/applications/{application_id}`, `PATCH /api/v1/applications/{application_id}/status`, `POST /api/v1/applications/{application_id}/prepare-automation`, `POST /api/v1/applications/{application_id}/execute-approved`, `GET /api/v1/agents/approvals/pending`, `GET /api/v1/agents/approvals/{approval_id}`, `POST /api/v1/agents/approvals/{approval_id}/decision`, `GET /api/v1/agents/sessions`, `GET /api/v1/agents/sessions/{session_id}/events`, `GET /api/v1/browser-logs`, `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{notification_id}/read`.
* **ML Inference (JWT-Authenticated):** `GET /api/v1/ml/health`, `POST /api/v1/ml/extract-resume`, `POST /api/v1/ml/multilingual/understand`, `POST /api/v1/ml/semantic-match`, `POST /api/v1/ml/eligibility/evaluate`, `POST /api/v1/ml/rank-opportunities`, `POST /api/v1/ml/verify-evidence`, `POST /api/v1/ml/recommend-pipeline`.
* **Multi-Role Portals, Interview & Analytics (WS10):** `GET/POST /api/v1/interview/sessions`, `POST /api/v1/interview/sessions/{session_id}/respond`, `GET /api/v1/analytics/overview`, `POST /api/v1/analytics/events`, `GET /api/v1/company/applicants`, `GET /api/v1/company/candidates`, `POST /api/v1/company/opportunities`, `PATCH /api/v1/company/applications/{application_id}/advance`, `GET /api/v1/university/overview`, `GET /api/v1/university/students`, `POST /api/v1/university/students/{student_profile_id}/verify`.

---

## Historical Pre-Consolidation Audit Findings (Preserved Below)

## 1. Critical Finding: API Split-Brain & SDK Contract Mismatches

Two mutually incompatible FastAPI `router.py` trees exist on different branches, while `packages/api-client` fails against **both** of them:
1. **`origin/ramaraju` (`aa19954`):** 22 DB/Auth/WS/stub endpoints under `/api/v1` — lacks all `ml` endpoints.
2. **`ml` (`f14190d`):** 7 unauthenticated stateless ML endpoints under `/api/v1/ml/*` + `/api/v1/eligibility/evaluate` + stub `/api/v1/opportunities` — lacks Auth, DB, Resumes, Applications, Approvals, and Voice.
3. **`packages/api-client/src/index.ts`:** Contains **4 breaking path/method mismatches** (`404`/`405`) even against `origin/ramaraju`.

---

## 2. `origin/ramaraju` FastAPI Endpoints (`apps/api/app/api/v1/router.py` & `voice.py`)

*Mount Prefix: `/api` + router prefix `/v1` = `/api/v1/*`*

| Method | Path | Auth Required | Schema In / Out | DB / External Dependency | Implementation Reality | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | None | `-> HealthResponse` | None | Static liveness ping | `IMPLEMENTED, NOT VERIFIED` *(Unit-tested)* |
| `GET` | `/api/v1/health/ready` | None | `-> ReadinessResponse` (`503` on fail) | AsyncPG `SELECT 1` + Redis `PING` | Real dependency check (`503` if degraded) | `IMPLEMENTED, NOT VERIFIED` *(Fake DB/Redis unit tests)* |
| `GET` | `/api/v1/users/me` | Bearer JWT (`authenticated`) | `-> ProfileResponse` | `ProfileRepository` (`public.profiles`) | Real DB read/auto-provision | `IMPLEMENTED, NOT VERIFIED` |
| `PUT` | `/api/v1/users/me` | Bearer JWT | `ProfileUpdateRequest -> ProfileResponse` | `ProfileRepository` | Real DB update | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/users/me/student-profile` | Bearer JWT | `-> StudentProfileResponse` | `StudentProfileRepository` (`public.student_profiles`) | Real DB read | `IMPLEMENTED, NOT VERIFIED` |
| `PUT` | `/api/v1/users/me/student-profile` | Bearer JWT | `StudentProfileUpdateRequest -> StudentProfileResponse` | `StudentProfileRepository` | Real DB update | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/career-passport` | Bearer JWT | `-> CareerPassportListResponse` | `CareerPassportRepository` (`public.career_passports`) | Real DB query (no `education` join) | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/career-passport/items` | Bearer JWT | `CareerPassportItemCreate -> CareerPassportItemResponse` | `CareerPassportRepository` | Real DB insert | `IMPLEMENTED, NOT VERIFIED` |
| `DELETE` | `/api/v1/career-passport/items/{item_id}` | Bearer JWT | `-> 204 No Content` | `CareerPassportRepository` | Ownership-scoped delete | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/opportunities` | None / Public | Query filters + cursor -> `OpportunityListResponse` | `OpportunityRepository` (`public.opportunities`) | Cursor-paginated SQL list | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/opportunities/saved` | Bearer JWT | Cursor -> `OpportunityListResponse` | `OpportunityRepository` (`saved_opportunities` join) | Authenticated user's bookmarks | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/opportunities/{opportunity_id}` | None / Public | `-> OpportunityResponse` | `OpportunityRepository` | Detail lookup | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/opportunities/discover` | Bearer JWT *(verify)* | `OpportunityDiscoverRequest -> OpportunityListResponse` | `OpportunityRepository` (`ILIKE` SQL only) | **No Olostep, no Crustdata, no `pgvector` search** (`search_similar_by_vector` uncalled) | `PARTIALLY COMPLETE` |
| `POST` | `/api/v1/opportunities/{opportunity_id}/save` | Bearer JWT | `-> SavedOpportunityResponse` | `OpportunityRepository` | Bookmark toggle | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/applications` | Bearer JWT | `-> ApplicationListResponse` | `ApplicationRepository` (`public.applications`) | User-scoped application list | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/applications` | Bearer JWT | `ApplicationCreate -> ApplicationResponse` (`201`) | `ApplicationRepository` + `ApprovalRepository` | Creates app + pending human approval | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/applications/{application_id}` | Bearer JWT | `-> ApplicationResponse` | `ApplicationRepository` | Ownership-scoped get | `IMPLEMENTED, NOT VERIFIED` |
| `PATCH` | `/api/v1/applications/{application_id}/status` | Bearer JWT | `ApplicationStatusUpdate -> ApplicationResponse` | `ApplicationRepository` | Atomic transition SQL | `IMPLEMENTED, NOT VERIFIED` |
| `DELETE` | `/api/v1/applications/{application_id}` | Bearer JWT | `-> 204 No Content` | `ApplicationRepository` | Ownership-scoped delete | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/agents/approvals/pending` | Bearer JWT | `-> HumanApprovalListResponse` | `ApprovalRepository` (`public.human_approvals`) | Lists pending gates | `IMPLEMENTED, NOT VERIFIED` |
| `GET` | `/api/v1/agents/approvals/{approval_id}` | Bearer JWT | `-> HumanApprovalResponse` | `ApprovalRepository` | Ownership-scoped get | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/agents/approvals/{approval_id}/decision` | Bearer JWT | `ApprovalDecisionRequest -> HumanApprovalResponse` | `ApprovalRepository`, `ApplicationRepository`, `NotificationRepository` | Atomic DB approval + notification; **does NOT resume LangGraph or trigger Playwright** | `PARTIALLY COMPLETE` |
| `GET` | `/api/v1/notifications` | Bearer JWT | `-> NotificationListResponse` | `NotificationRepository` (`public.notifications`) | Lists notifications | `IMPLEMENTED, NOT VERIFIED` |
| `PATCH` | `/api/v1/notifications/{notification_id}/read` | Bearer JWT | `-> NotificationResponse` | `NotificationRepository` | Marks notification read | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/eligibility/evaluate` | Bearer JWT *(checked)* | `EligibilityEvaluateRequest -> EligibilityResultResponse` | None | **Hardcoded placeholder:** `is_eligible=False, score=0.0, reasons=["Profile evaluation pending ML integration."]` | **`MOCK/STUB`** |
| `GET` | `/api/v1/resumes` | Bearer JWT | `-> ResumeListResponse` | `ResumeRepository` (`public.resumes`) | Lists JSON resumes | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/resumes` | Bearer JWT | `ResumeCreateRequest -> ResumeResponse` (`201`) | `ResumeRepository` | JSON-only insert; **no file upload/storage/parsing** | `PARTIALLY COMPLETE` |
| `GET` | `/api/v1/resumes/{resume_id}` | Bearer JWT | `-> ResumeResponse` | `ResumeRepository` | Ownership-scoped get | `IMPLEMENTED, NOT VERIFIED` |
| `DELETE` | `/api/v1/resumes/{resume_id}` | Bearer JWT | `-> 204 No Content` | `ResumeRepository` | Ownership-scoped delete | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/voice/sessions` | Bearer JWT | `VoiceSessionCreateRequest -> VoiceSessionResponse` (`201`) | `VoiceSessionRepository` (`public.voice_sessions`) | Telemetry persistence | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/voice/tickets` | Bearer JWT | `-> VoiceTicketResponse` | `VoiceTicketStore` (Redis `SET EX 30` / dev memory) | Issues single-use 30s WS ticket | `IMPLEMENTED, NOT VERIFIED` |
| `WS` | `/api/v1/voice/stream` | Query `?ticket=...` (single-use) | Binary PCM / JSON `session_init`, `interrupted`, `ping` | `VoiceTicketStore` (`GETDEL`) | **Stub loop:** acknowledges PCM bytes (`{event:"audio_received"}`) with **NO Gemini Live connection, NO ASR/TTS** | **`MOCK/STUB`** |

---

## 3. `ml` Branch FastAPI Endpoints (`apps/api/app/api/v1/router.py` & `ml.py`)

*NOTE: None of the `ml` endpoints enforce JWT authentication (`Depends(get_current_user)` absent) and none read/write PostgreSQL.*

| Method | Path | Auth | Request / Response | Engine / Model Used | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | **None** | `-> HealthResponse` | Static JSON | `VERIFIED COMPLETE` *(Local `TestClient`)* |
| `GET` | `/api/v1/opportunities` | **None** | `-> []` | None | **`MOCK/STUB`** *(Returns empty list `[]`)* |
| `GET` | `/api/v1/ml/health` | **None** | `-> MLHealthResponse` | Checks `NexteRaSMLService` cache/config | `VERIFIED COMPLETE` *(Local `TestClient`)* |
| `POST` | `/api/v1/ml/extract-resume` | **None (Security Gap)** | `ResumeExtractionAPIRequest` -> `ExtractionResponse` | Deterministic rules + `pymupdf` PDF / optional Gemini REST | `IMPLEMENTED, NOT VERIFIED` *(Unit-tested w/ mock Gemini; `.docx` unsupported)* |
| `POST` | `/api/v1/ml/multilingual/understand` | **None (Security Gap)** | `MultilingualQueryAPIRequest` -> `MultilingualUnderstandingResult` | `paraphrase-multilingual-MiniLM-L12-v2` + script heuristic | `IMPLEMENTED, NOT VERIFIED` *(Only 7 langs + Hinglish; missing `mr`/`gu`)* |
| `POST` | `/api/v1/ml/semantic-match` | **None (Security Gap)** | `SemanticMatchAPIRequest` -> Ranked docs + scores | `minilm-nexteras-v1` (384-dim CPU SentenceTransformer) | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/eligibility/evaluate` | **None (Conflict w/ `ramaraju`)** | `{student, opportunity}` -> `EligibilityResult` | 10-rule deterministic `EligibilityEngine` | `IMPLEMENTED, NOT VERIFIED` *(Schema incompatible with `ramaraju` `{opportunity_id}` contract)* |
| `POST` | `/api/v1/ml/rank-opportunities` | **None (Security Gap)** | `{student, preferences, candidates}` -> `RankingResponse` | `BaselineOpportunityRanker` (6-weight scorer + hard exclusion) | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/ml/verify-evidence` | **None (Security Gap)** | `VerificationRequest` -> `VerificationResult` | Lexical fallback (default) or `nli-deberta-v3-small` | `IMPLEMENTED, NOT VERIFIED` |
| `POST` | `/api/v1/ml/recommend-pipeline` | **None (Security Gap)** | Full stateless JSON payload -> Pipeline response | Chains Extract -> Multilingual -> Eligibility -> Rank -> Verify | `PARTIALLY COMPLETE` *(Cold load on Windows CPU >15s inside E2E `TestClient`)* |

---

## 4. Next.js SSR / Route Handlers & Middleware

| Route / File | Branch | Purpose | Security & Implementation Audit |
| :--- | :--- | :--- | :--- |
| `/auth/callback` (`apps/web/src/app/auth/callback/route.ts`) | `origin/ramaraju` only | Exchanges Supabase PKCE/OAuth `code` for session cookies | Validates relative `next` via `sanitizeNextPath` (good against open redirects); not merged into `develop`/`ml` |
| `apps/web/src/middleware.ts` | `origin/ramaraju` only | Refreshes Supabase SSR session & guards routes via `supabase.auth.getUser()` | **Security/Sync Issues:** (1) Fails open (`NextResponse.next`) if public Supabase env vars are missing; (2) Only protects 6 paths (`/career-passport`, `/applications`, `/resume`, `/interview`, `/analytics`, `/settings`) — omits `/overview`, `/notifications`, `/onboarding`, `/agent-control-center`, `/company/*`, `/university/*` present on `develop`/`ml` |
| Any Next.js `/api/*` Route Handlers | All branches | N/A | **0 route handlers** exist (`apps/web` calls backend or mocks) |

---

## 5. TypeScript API Client (`packages/api-client/src/index.ts`) Breaking Mismatches

| SDK Method (`OpportunityOsClient`) | SDK Request Sent | Actual `origin/ramaraju` Backend Route | Result Against Live Backend |
| :--- | :--- | :--- | :--- |
| `getProfile()` | `GET /users/me/profile` | `GET /api/v1/users/me` + `GET /api/v1/users/me/student-profile` | **`404 Not Found`** |
| `discoverOpportunities(query)` | `GET /opportunities/discover?q=...` | `GET /api/v1/opportunities` or `POST /api/v1/opportunities/discover` | **`405 Method Not Allowed`** |
| `checkEligibility(opportunityId)` | `GET /eligibility/evaluate/${opportunityId}` | `POST /api/v1/eligibility/evaluate` (stub) | **`405 Method Not Allowed`** |
| `approveAction(approvalId, approved)` | `POST /agents/approval/${approvalId}` | `POST /api/v1/agents/approvals/${approvalId}/decision` | **`404 Not Found`** |
| `submitApplication(opportunityId)` | `POST /applications` | `POST /api/v1/applications` | Aligned path *(payload schema requires `resume_id` verification)* |
| `getPendingApprovals()` | `GET /agents/approvals/pending` | `GET /api/v1/agents/approvals/pending` | Aligned path *(unused in `apps/web` UI)* |
| **Missing SDK Methods** | *(None in `api-client`)* | Resumes, Passport CRUD, Notifications, Voice Tickets/Sessions, Saved Opps, ML endpoints | **Unimplemented in `@opportunity-os/api-client`** |

---

## 6. Missing Product & Spec Endpoints (`NOT IMPLEMENTED` Anywhere)

* **Resume Intelligence (WS3):** `POST /api/v1/resumes/upload` (multipart PDF/DOCX + Storage), `POST /api/v1/resumes/{id}/tailor`, `GET`/`POST /api/v1/resumes/{id}/pdf`, `GET /api/v1/resumes/{id}/versions`.
* **External Discovery & Enrichment (WS4–WS5):** Olostep crawl/monitor triggers & webhook handlers; Company enrichment & hiring status (`/companies/*` backed by Crustdata).
* **Academic Education Records:** `GET/POST/DELETE /api/v1/users/me/education` (`public.education` table exists with zero backend handlers).
* **Agent Orchestration & Execution (WS8–WS9):** `POST /api/v1/agents/runs`, `GET /api/v1/agents/sessions/{id}`, SSE/WS event stream (`agent_events`), Playwright dry-run trigger & screenshot retrieval (`browser_execution_logs`).
* **Role-Based Portals Present in Frontend (`develop`/`ml`):** Company endpoints (`/company/opportunities`, `/company/applicants`, `/company/candidates`) and University verification endpoints (`/university/students`, `/university/verification`) plus Analytics endpoints (`/analytics/skills-gap`, `/analytics/activity`).
* **Interview Simulator (Multilingual):** Backend endpoints for stateful mock interview turns & scoring (`/api/v1/interview/*`).
