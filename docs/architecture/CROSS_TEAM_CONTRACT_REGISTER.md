# Opportunity OS — Cross-Team Contract Register

**Status:** Proposed Architecture Draft for Joint Engineering Review  
**Owners:** Sanju (Frontend & ML Lead) & Ramaraju (Backend & Database Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Governance Standard:** Ramaraju owns final backend API routes and database schemas; Sanju owns frontend component contracts and ML model evaluation contracts. Changes to shared contracts require mutual review.

---

## 1. Authentication & Session Lifecycle Contract

### Proposed Standard
- **Transport:** Standard HTTP `Authorization: Bearer <JWT>` header on all protected REST endpoints and initial WebSocket upgrade requests.
- **Provider:** Supabase Auth (GoTrue).
- **Token Refresh:** Frontend manages silent refresh via Supabase JavaScript SDK before expiry.
- **Session Expiration:** Standard 3600-second access token expiry. 401 Unauthorized responses trigger client-side re-authentication or token refresh.

### Questions for Joint Sign-Off
1. *For Ramaraju:* Does FastAPI authenticate tokens directly using `SUPABASE_JWT_SECRET` (HS256) locally, or via Supabase Auth Admin REST API? *(Recommended: Local verification using python-jose or PyJWT for $< 2\text{ms}$ latency).*
2. *For Sanju:* Does the voice WebSocket connection pass the JWT as a query param (`?token=...`) during the WS handshake, or in a subprotocol header?

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

| Domain Concept | TypeScript (`@opportunity-os/shared-types`) | Python (`apps/api/app/schemas/`) |
| :--- | :--- | :--- |
| **Language Code** | `IndianLanguage = 'en' \| 'hi' \| ...` | `enum LanguageCode(str, Enum)` |
| **Opportunity** | `interface Opportunity` | `class OpportunityResponse(BaseModel)` |
| **Eligibility** | `interface EligibilityResult` | `class EligibilityCheckResponse(BaseModel)` |
| **Approval** | `interface ApprovalRequest` | `class ApprovalRequestDTO(BaseModel)` |
| **Student** | `interface StudentProfile` | `class StudentProfileDTO(BaseModel)` |

---

## 10. File Upload & Download Contract
- **Resume Uploads:** Accepted formats: `.pdf`, `.docx`. Maximum file size: `5MB`. Sent as `multipart/form-data` to `/resumes/upload`.
- **Rendered PDF Downloads:** Generated as stream or pre-signed URL with `Content-Type: application/pdf` and `Content-Disposition: inline; filename="OpportunityOS_Resume.pdf"`.
