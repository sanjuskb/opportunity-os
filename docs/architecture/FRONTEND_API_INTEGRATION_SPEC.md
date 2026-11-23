# Opportunity OS — Frontend API Integration Specification & Contract Alignment

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** API Client, Data Fetching & Cross-Team Contract Alignment  
**Owner:** Sanju (Frontend & ML Lead)  
**Backend Partner:** Ramaraju (Backend & Database Lead)  
**Implementation Target:** `packages/api-client/`, `packages/shared-types/`, and `apps/web/src/hooks/`  

---

## 1. Architecture Overview & Client Boundary

Opportunity OS enforces a clear architectural contract boundary between the Next.js frontend (`apps/web`) and the FastAPI backend (`apps/api`). 

### 1.1 Core Tenets
1. **Typed SDK Layer:** React components never call `fetch()` directly. All HTTP requests are executed via typed client methods exported by `@opportunity-os/api-client`.
2. **Server-State Management with TanStack Query v5:** All remote queries and mutations are managed by custom hooks (e.g. `useOpportunitiesQuery`, `useEligibilityMutation`) providing caching, revalidation, optimistic updates, and loading/error states.
3. **RFC 7807 Standardized Error Handling:** Every non-2xx response adheres to the RFC 7807 Problem Details schema, mapped automatically into typed JavaScript errors with actionable UI feedback.
4. **Idempotency on Critical Mutations:** Application submissions, approval decisions, and AI resume generations supply an `Idempotency-Key: <UUIDv4>` header to protect students against duplicate workflows on unstable connections.

---

## 2. Exhaustive API Route & Contract Specification

Below is the complete contract specification for every endpoint consumed by the frontend.

### 2.1 Authentication & Session
- **`GET /api/v1/users/me`**
  - **Hook:** `useCurrentUserQuery()`
  - **Query Key:** `['users', 'me']`
  - **Response:** `StudentProfile`
  - **Stale Time:** 10 minutes (`10 * 60 * 1000`)
- **`PUT /api/v1/users/me/student-profile`**
  - **Hook:** `useUpdateStudentProfileMutation()`
  - **Request Body:** `Partial<StudentProfile>`
  - **Invalidations:** `['users', 'me']`, `['eligibility']`

### 2.2 Career Passport
- **`GET /api/v1/career-passport`**
  - **Hook:** `useCareerPassportQuery()`
  - **Query Key:** `['career-passport']`
  - **Response:**
    ```typescript
    export interface CareerPassportDTO {
      id: string;
      studentId: string;
      skills: Array<{ name: string; verified: boolean; level: 'beginner' | 'intermediate' | 'advanced' }>;
      projects: Array<{ id: string; title: string; description: string; githubUrl?: string; liveUrl?: string; techStack: string[] }>;
      certifications: Array<{ id: string; title: string; issuer: string; issueDate: string; credentialUrl?: string }>;
      education: Array<{ collegeName: string; degree: string; branch: string; cgpa: number; graduationYear: number }>;
    }
    ```
  - **Stale Time:** 5 minutes
- **`POST /api/v1/career-passport/items`**
  - **Hook:** `useAddPassportItemMutation()`
  - **Request Body:** `{ type: 'project' | 'certification' | 'skill'; data: Record<string, unknown> }`
  - **Invalidations:** `['career-passport']`, `['resumes']`
- **`DELETE /api/v1/career-passport/items/{id}`**
  - **Hook:** `useDeletePassportItemMutation()`
  - **Invalidations:** `['career-passport']`

### 2.3 Opportunity Discovery & Search
- **`GET /api/v1/opportunities`**
  - **Hook:** `useInfiniteOpportunitiesQuery(filters)`
  - **Query Key:** `['opportunities', 'list', filters]`
  - **Parameters:**
    - `cursor?: string` (Base64 cursor for infinite scrolling)
    - `limit?: number` (Default 20, max 50)
    - `types?: OpportunityType[]`
    - `batch?: number`
    - `remote?: boolean`
    - `minStipend?: number`
    - `query?: string`
  - **Response:**
    ```typescript
    export interface PaginatedOpportunitiesResponse {
      items: Opportunity[];
      nextCursor: string | null;
      hasMore: boolean;
      totalCount: number;
    }
    ```
  - **Stale Time:** 2 minutes
- **`GET /api/v1/opportunities/{id}`**
  - **Hook:** `useOpportunityDetailQuery(id)`
  - **Query Key:** `['opportunities', 'detail', id]`
  - **Response:** `Opportunity`
  - **Stale Time:** 15 minutes
- **`POST /api/v1/opportunities/{id}/save`**
  - **Hook:** `useBookmarkOpportunityMutation()`
  - **Request Body:** `{ saved: boolean }`
  - **Optimistic Updates:** Toggles `isBookmarked` immediately in cache.

### 2.4 Eligibility Evaluation Engine
- **`POST /api/v1/eligibility/evaluate`**
  - **Hook:** `useEvaluateEligibilityMutation()`
  - **Request Body:** `{ opportunityId: string }`
  - **Response:** `EligibilityResult`
  - **Query Key Cached:** `['eligibility', opportunityId]`
- **`GET /api/v1/eligibility/gap-analysis/{opportunity_id}`**
  - **Hook:** `useEligibilityGapAnalysisQuery(opportunityId)`
  - **Query Key:** `['eligibility', 'gap-analysis', opportunityId]`
  - **Response:**
    ```typescript
    export interface GapAnalysisDTO {
      opportunityId: string;
      missingPrerequisites: string[];
      learningResources: Array<{ title: string; url: string; estimatedHours: number }>;
      alternativeMatches: Opportunity[];
    }
    ```

### 2.5 Resume Studio (ATS & Grounded Tailoring)
- **`GET /api/v1/resumes`**
  - **Hook:** `useResumesListQuery()`
  - **Query Key:** `['resumes', 'list']`
  - **Response:** `ResumeSummaryDTO[]`
- **`POST /api/v1/resumes/{id}/tailor`**
  - **Hook:** `useTailorResumeMutation()`
  - **Request Body:** `{ targetOpportunityId: string; focusSkills?: string[] }`
  - **Response:** `GroundedResumeDTO`
  - **Invalidations:** `['resumes', 'list']`, `['resumes', id]`
- **`GET /api/v1/resumes/{id}/pdf`**
  - **Direct Download / Stream URL:** Returns `application/pdf` with pre-signed authorization token.

### 2.6 Agent Approvals & Human-in-the-Loop Gate
- **`GET /api/v1/agents/approvals/pending`**
  - **Hook:** `usePendingApprovalsQuery()`
  - **Query Key:** `['approvals', 'pending']`
  - **Polling / Refetch:** Refetch on window focus or 15-second background interval.
  - **Response:** `ApprovalRequestDTO[]`
- **`POST /api/v1/agents/approvals/{id}/decision`**
  - **Hook:** `useApprovalDecisionMutation()`
  - **Request Body:**
    ```typescript
    export interface ApprovalDecisionRequest {
      approved: boolean;
      rejectionReason?: string;
      clientTimestamp: string;
    }
    ```
  - **Invalidations:** `['approvals', 'pending']`, `['applications']`

### 2.7 Multilingual Voice WebSocket Gateway
- **`WSS /api/v1/voice/stream?token={jwt}`**
  - **Protocol:** Bidirectional JSON + 16kHz PCM Int16 binary frames (detailed in `FRONTEND_VOICE_LIFECYCLE.md`).

---

## 3. RFC 7807 Error Handling Standard

When an API request fails, the backend returns `Content-Type: application/problem+json`:

```typescript
export interface ApiProblemDetails {
  type: string;          // e.g. 'urn:problem:eligibility_disqualified'
  title: string;         // 'Student Graduation Batch Ineligible'
  status: number;        // 422
  detail: string;        // 'This opportunity requires 2025/2026 graduation batch, but profile indicates 2027.'
  instance?: string;     // 'req_01HJ89XAB12...'
  invalidParams?: Array<{
    name: string;
    reason: string;
  }>;
}
```

### 3.1 Client Error Mapping Matrix

| Problem Type URI | HTTP Status | Frontend User Interface Action |
| :--- | :--- | :--- |
| `urn:problem:unauthorized` | 401 | Trigger silent token refresh; if failed, redirect to `/[locale]/auth/login` |
| `urn:problem:forbidden` | 403 | Display permission denied alert banner |
| `urn:problem:opportunity_expired` | 410 | Display "Opportunity closed" badge, disable "Apply" button |
| `urn:problem:validation_failed` | 422 | Map `invalidParams` directly into form input helper text errors |
| `urn:problem:rate_limit_exceeded` | 429 | Display toast: *"Too many requests. Please wait 30 seconds."* |
| `urn:problem:internal_server_error` | 500 | Trigger React error boundary with error report ID |

---

## 4. Open Architectural Questions for Ramaraju (Backend Lead)

To ensure smooth sprint execution and zero integration friction, the following questions are submitted for backend confirmation:

1. **JWT Verification in FastAPI:** Does the backend verify Supabase JWTs locally using `SUPABASE_JWT_SECRET` (HS256) or by calling the Supabase Auth REST endpoint on every request?  
   *Frontend Recommendation:* Local verification using PyJWT to keep P95 API response times under $25\text{ms}$.
2. **WebSocket Authentication:** Should the voice WebSocket pass the JWT in the query string (`?token=...`) or via standard WebSocket connection protocols/headers?  
   *Frontend Recommendation:* Query parameter `?token=...` during WebSocket handshake, as browser `new WebSocket(url)` does not support custom request headers in standard Web APIs.
3. **Cursor Format for Opportunity Pagination:** Is the pagination cursor an opaque Base64 encoded string of `(created_at, id)` or an integer offset?  
   *Frontend Recommendation:* Opaque Base64 string for resilient infinite scrolling without offset drift when new opportunities are ingested concurrently.
4. **Agent Approval Payload Screenshots:** Will `ApprovalRequestDTO.dryRunScreenshotUrl` point to an ephemeral Supabase Storage pre-signed URL or a base64 inline image?  
   *Frontend Recommendation:* Supabase Storage pre-signed URL (1-hour expiry) to keep approval list payload size $< 5\text{KB}$.
