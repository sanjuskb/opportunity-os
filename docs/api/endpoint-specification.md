# Opportunity OS — FastAPI Endpoint Specifications

## 1. REST API Standards & Convention

- **Base URL:** `/api/v1`
- **Authentication:** Bearer JWT in the `Authorization` header (`Bearer <supabase_jwt>`).
- **Validation:** Strict Pydantic v2 schemas for all requests and responses.
- **Error Format:** RFC 7807 compliant problem details JSON with `status`, `title`, `detail`, and `error_code`.
- **Idempotency:** Non-safe operations (`POST /applications`, `POST /agents/approval/{id}`) support `Idempotency-Key` headers.

---

## 2. Endpoint Catalog

### 2.1 Authentication & Profile
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/users/me` | Fetch authenticated user profile | Yes |
| `PUT` | `/users/me` | Update personal info & language preference | Yes |
| `GET` | `/users/me/student-profile` | Fetch student academic records | Yes |
| `PUT` | `/users/me/student-profile` | Update academic records (college, CGPA, branch) | Yes |

### 2.2 Career Passport
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/career-passport` | Get verified student achievements & coursework | Yes |
| `POST` | `/career-passport/items` | Add verified project, certification, or badge | Yes |
| `DELETE` | `/career-passport/items/{id}` | Remove item from Career Passport | Yes |

### 2.3 Opportunity Discovery & Ingestion
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/opportunities` | Filterable list of vetted opportunities | Yes |
| `GET` | `/opportunities/{id}` | Fetch detailed opportunity information | Yes |
| `POST` | `/opportunities/discover` | Trigger agentic search via Olostep/Crustdata | Yes |
| `POST` | `/opportunities/{id}/save` | Bookmark an opportunity | Yes |

### 2.4 Deterministic & Semantic Eligibility Engine
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/eligibility/evaluate` | Run deterministic + semantic eligibility match | Yes |
| `GET` | `/eligibility/gap-analysis/{opportunity_id}` | Detailed skill gap and prerequisite report | Yes |

### 2.5 Resume Studio (ATS & Grounded Tailoring)
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/resumes` | List user resumes | Yes |
| `POST` | `/resumes` | Create new master resume from Career Passport | Yes |
| `POST` | `/resumes/{id}/tailor` | Synthesize job-specific tailored version | Yes |
| `GET` | `/resumes/{id}/pdf` | Download rendered ATS-friendly PDF | Yes |

### 2.6 Agent Orchestration & Human Approval Gate
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/agents/sessions` | Initialize new LangGraph agent session | Yes |
| `GET` | `/agents/sessions/{id}/state` | Fetch current execution state & step events | Yes |
| `GET` | `/agents/approvals/pending` | List pending actions requiring human approval | Yes |
| `POST` | `/agents/approvals/{id}/decision` | Approve or reject browser/submission action | Yes |

### 2.7 Multilingual Voice Interaction Gateway
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `WebSocket` | `/voice/stream` | Full-duplex PCM audio stream to Gemini Live | Yes (Token query/header) |
| `POST` | `/voice/sessions` | Record telemetry & duration of voice interaction | Yes |

---

## 3. Representative Pydantic Request & Response Models

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class LanguageCode(str, Enum):
    EN = "en"
    HI = "hi"
    TE = "te"
    TA = "ta"
    KN = "kn"
    ML = "ml"
    BN = "bn"

class OpportunityDTO(BaseModel):
    id: str
    title: str
    organization: str
    location: str
    type: str
    description: str
    stipend_or_salary: Optional[str] = None
    deadline: Optional[datetime] = None
    source_url: HttpUrl
    source_provider: str
    required_skills: List[str]
    eligible_batches: List[int]
    min_cgpa: Optional[float] = None

class EligibilityCheckResponse(BaseModel):
    opportunity_id: str
    is_eligible: bool
    overall_match_score: float = Field(ge=0.0, le=100.0)
    deterministic_checks: Dict[str, bool]
    matched_skills: List[str]
    missing_skills: List[str]
    plain_language_explanation: str

class ApprovalDecisionRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None
    client_timestamp: datetime = Field(default_factory=datetime.utcnow)
```
