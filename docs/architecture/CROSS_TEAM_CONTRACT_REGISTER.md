# Opportunity OS — Cross-Team Contract Register

**Status:** Proposed Architecture Draft for Joint Engineering Review  
**Owners:** Sanju (Frontend & ML Lead) & Ramaraju (Backend & Database Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Governance Standard:** Ramaraju owns final backend API routes and database schemas; Sanju owns frontend component contracts and ML model evaluation contracts. Changes to shared contracts require mutual review.

---

## 1. Authentication & Session Lifecycle Contract

### Proposed Standard
- **Transport:** Standard HTTP `Authorization: Bearer <JWT>` header on all protected REST endpoints.
- **Provider:** Supabase Auth (GoTrue).
- **Token Refresh:** Frontend manages silent refresh via Supabase JavaScript SDK before expiry.
- **Session Expiration:** Standard 3600-second access token expiry. 401 Unauthorized responses trigger client-side re-authentication or token refresh.

### WebSocket Authentication Hardening (Ticket-Based Handshake)
Passing long-lived JWTs in URL query parameters (`?token=...`) exposes them to proxy server logs, reverse proxy caches, and browser history. To guarantee enterprise-grade security:
1. **Ticket Request:** Prior to initiating a WebSocket connection, the client makes an authenticated HTTP request:
   `POST /api/v1/voice/tickets` with `Authorization: Bearer <JWT>`.
2. **Ephemeral Ticket Issuance:** The backend verifies the JWT and generates a single-use, cryptographically secure ticket UUID (stored in Redis or RAM with a strict **30-second TTL**).
3. **Connection Handshake:** The client connects:
   `wss://api.opportunityos.in/api/v1/voice/stream?ticket=<TICKET_UUID>`.
4. **Immediate Invalidation:** The backend validates and immediately destroys the ticket upon successful connection upgrade. If intercepted or logged, it cannot be reused.
5. **Subprotocol Fallback:** As an alternative, clients supporting WebSocket subprotocols may pass `new WebSocket(url, ['Bearer', token])`, keeping the token inside the HTTP `Sec-WebSocket-Protocol` header.

### Questions for Joint Sign-Off
1. *For Ramaraju:* Does FastAPI authenticate tokens directly using `SUPABASE_JWT_SECRET` (HS256) locally, or via Supabase Auth Admin REST API? *(Recommended: Local verification using python-jose or PyJWT for $< 2\text{ms}$ latency).*
2. *For Ramaraju:* Confirm whether the ephemeral ticket handshake (`POST /api/v1/voice/tickets`) is approved for implementation in Phase 6.

---

## 2. Universal API Error Response Format

To ensure consistent error boundaries across React components and FastAPI handlers, all error responses must adhere to the **RFC 7807 Problem Details** standard.

```typescript
// Proposed TypeScript Type: @opportunity-os/shared-types
export interface ApiProblemDetails {
  type: string;          // URI reference identifying problem type (e.g. 'urn:problem:eligibility_disqualified')
  title: string;         // Short human-readable summary
  status: number;        // HTTP status code (e.g. 400, 404, 422, 500)
  detail: string;        // Detailed explanation of specific error instance
  instance?: string;     // Request ID or trace ID for backend debugging
  invalidParams?: Array<{
    name: string;
    reason: string;
  }>;
}
```

```python
# Matching Pydantic Schema: apps/api/app/schemas/common.py
from pydantic import BaseModel
from typing import Optional, List

class InvalidParam(BaseModel):
    name: str
    reason: str

class ProblemDetails(BaseModel):
    type: str = "urn:problem:generic"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
    invalid_params: Optional[List[InvalidParam]] = None
```

---

## 3. Pagination, Sorting & Filtering Conventions

- **Default Pagination Mode:** Cursor-based pagination for high-throughput opportunity feeds; offset/limit allowed for simple admin lists.
- **Query Parameter Names:**
  - `cursor`: Base64-encoded string representing `(created_at, id)`.
  - `limit`: Integer, default `20`, maximum `100`.
  - `sort_by`: Field name (e.g. `deadline`, `created_at`, `stipend`).
  - `order`: `asc` or `desc` (default `desc`).
- **Response Wrapper:**
  ```typescript
  export interface PaginatedResponse<T> {
    items: T[];
    nextCursor: string | null;
    hasMore: boolean;
    totalCount?: number;
  }
  ```

---

## 4. Opportunity & Eligibility Response Contracts

### Proposed Opportunity DTO
```typescript
export interface OpportunityDTO {
  id: string;
  title: string;
  organization: string;
  location: string;
  type: 'internship' | 'full_time' | 'scholarship' | 'fellowship';
  description: string;
  stipendOrSalary?: string;
  deadline?: string;
  sourceUrl: string;
  sourceProvider: 'olostep' | 'crustdata' | 'direct_portal';
  retrievalTimestamp: string;
  requiredSkills: string[];
  eligibleBatches: number[];
  eligibleDegrees: string[];
  minCgpa?: number;
  companyTelemetry?: {
    headcount?: string;
    verifiedDomain?: string;
    fundingStage?: string;
  };
}
```

### Proposed Eligibility Evaluation Contract
```typescript
export interface EligibilityEvaluationDTO {
  opportunityId: string;
  isEligible: boolean;
  matchScore: number; // 0 to 100
  deterministicChecks: {
    batchMatched: boolean;
    degreeMatched: boolean;
    cgpaMatched: boolean;
    branchMatched: boolean;
  };
  skillAnalysis: {
    matchedSkills: string[];
    missingSkills: string[];
    suggestedQuickLearnings: string[];
  };
  explanation: string; // Regional language string if requested
}
```

---

## 5. Resume Editor Data Contract (Zero-Hallucination Schema)

Resumes must be structured JSON trees that link every bullet point directly to a `passport_item_id`:

```typescript
export interface GroundedResumeDTO {
  id: string;
  studentId: string;
  title: string;
  targetRole?: string;
  contactInfo: {
    fullName: string;
    email: string;
    phone?: string;
    githubUrl?: string;
    linkedinUrl?: string;
  };
  sections: Array<{
    type: 'education' | 'experience' | 'projects' | 'skills' | 'certifications';
    heading: string;
    items: Array<{
      passportSourceId: string; // Must map to a valid record in career_passports
      title: string;
      subtitle?: string;
      dateRange?: string;
      bulletPoints: string[];
    }>;
  }>;
  compiledPdfUrl?: string;
}
```

---

## 6. Approval Request & Execution Status Contract

```typescript
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'timed_out';

export interface ApprovalRequestDTO {
  id: string;
  sessionId: string;
  opportunityId: string;
  opportunityTitle: string;
  organization: string;
  actionType: 'portal_submission' | 'email_outreach';
  dryRunScreenshotUrl: string;
  fieldDiff: Record<string, {
    label: string;
    proposedValue: string;
    source: string;
  }>;
  status: ApprovalStatus;
  createdAt: string;
  expiresAt: string; // Defaults to 15 minutes post-creation
}
```

---

## 7. Voice Session Lifecycle & WebSocket Event Types

Bidirectional communication over `/api/v1/voice/stream` follows a typed JSON envelope protocol:

| Event Type | Origin | Payload Description |
| :--- | :--- | :--- |
| `session_init` | Client $\rightarrow$ Server | Initial language code (`hi`, `te`, etc.), user JWT |
| `audio_chunk` | Client $\rightarrow$ Server | Base64-encoded or binary 16kHz linear PCM audio buffer |
| `vad_signal` | Server $\rightarrow$ Client | Voice Activity status (`speech_started`, `speech_ended`) |
| `transcript` | Server $\rightarrow$ Client | Real-time incremental ASR text + detected language |
| `tool_start` | Server $\rightarrow$ Client | Indicates agent is executing a tool (e.g. `searching_opportunities`) |
| `audio_output`| Server $\rightarrow$ Client | Audio buffer of synthesized regional voice response |
| `interrupted` | Client $\rightarrow$ Server | Student interrupted spoken response; cancel audio stream |

---

## 8. Notification Event Structure

```typescript
export interface NotificationEventDTO {
  id: string;
  userId: string;
  type: 'opportunity_match' | 'deadline_approaching' | 'approval_required' | 'application_submitted';
  title: string;
  message: string;
  actionUrl?: string;
  isRead: boolean;
  createdAt: string;
}
```

---

## 9. Shared TypeScript & Python Type Mapping Matrix

| Domain Concept | TypeScript (`@opportunity-os/shared-types`) | Python (`apps/api/app/schemas/`) | Serialization Standard |
| :--- | :--- | :--- | :--- |
| **Language Code** | `IndianLanguage = 'en' \| 'hi' \| ...` | `enum LanguageCode(str, Enum)` | Exact lowercase string |
| **Opportunity** | `interface Opportunity` | `class OpportunityResponse(BaseModel)` | `alias_generator = to_camel`, `populate_by_name = True` |
| **Eligibility** | `interface EligibilityResult` | `class EligibilityCheckResponse(BaseModel)` | `alias_generator = to_camel` |
| **Approval** | `interface ApprovalRequest` | `class ApprovalRequestDTO(BaseModel)` | `alias_generator = to_camel` |
| **Student** | `interface StudentProfile` | `class StudentProfileDTO(BaseModel)` | `alias_generator = to_camel` |

### Serialization Convention
- **Backend Convention:** Python internal code uses idiomatic `snake_case` (e.g. `source_url`, `stipend_or_salary`, `eligible_batches`).
- **Pydantic Configuration:** All response schemas define `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- **Wire Representation:** JSON over HTTP REST and WebSocket always delivers `camelCase` keys (e.g. `sourceUrl`, `stipendOrSalary`), eliminating manual field renaming in frontend React code.

---

## 10. File Upload & Download Contract
- **Resume Uploads:** Accepted formats: `.pdf`, `.docx`. Maximum file size: `5MB`. Sent as `multipart/form-data` to `/resumes/upload`.
- **Rendered PDF Downloads:** Generated as stream or pre-signed URL with `Content-Type: application/pdf` and `Content-Disposition: inline; filename="OpportunityOS_Resume.pdf"`.

---

## 11. External Integrations & Model Context Protocol (MCP) Governance

To accelerate development without compromising security, Antigravity and the engineering team utilize standardized MCP servers:

| MCP Server | Integration Purpose | Scope & Access Control | Credential Isolation |
| :--- | :--- | :--- | :--- |
| **GitHub MCP** | Repository administration, PR management, issue tracking | Read/Write to `sanjuskb/opportunity-os` | Handled via authenticated GitHub CLI (`gh`) |
| **Supabase MCP** | Database schema exploration, migration checks, RLS validation | Development database instance | `SUPABASE_ACCESS_TOKEN` stored in local tooling |
| **Context7 MCP** | Codebase indexation, semantic search, cross-file tracking | Read-only workspace inspection | Local AST indexing |
| **Playwright MCP** | Browser automation & E2E verification | Local headless execution | Sandbox environment |
| **Google Developer Knowledge MCP** | Gemini Live WebSocket API docs, Web Audio references | Read-only documentation lookups | Official public documentation |
| **Sentry / Vercel (Optional)** | Deployment status & telemetry error monitoring | Monitoring read access | CI/CD environment secrets |

### Secret Isolation Rule
> [!CAUTION]
> Production API keys for external services (**Olostep**, **Crustdata**, **Gemini Live**, and **Supabase Service Role**) are owned exclusively by Ramaraju and reside strictly inside backend `.env.secrets` on deployment infrastructure. They are never committed to Git or exposed via frontend bundles.
