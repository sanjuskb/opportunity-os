# Opportunity OS — System Architecture Blueprint

## 1. High-Level System Architecture

Opportunity OS is designed as an agentic, voice-first career intelligence operating system for Indian college students. The architecture decouples client presentation from agentic planning, deterministic verification, and asynchronous browser execution.

```mermaid
flowchart TD
    subgraph ClientLayer["Client & Interaction Layer"]
        User(["Indian College Student"])
        WebClient["Next.js 15+ Web Application (React 19 / TypeScript)"]
        VoiceOrb["Voice Orb (Web Audio API / WebSockets)"]
        User <-->|Audio / Touch / Text| WebClient
        WebClient --- VoiceOrb
    end

    subgraph GatewayLayer["API & Communication Gateway"]
        FastApi["FastAPI REST & WebSocket Gateway"]
        AuthMiddleware["Supabase JWT Auth Middleware"]
        VoiceGateway["Gemini Live Multilingual WebSocket Proxy"]
        FastApi --> AuthMiddleware
        VoiceOrb <-->|Bidi Audio Stream| VoiceGateway
        WebClient <-->|REST Requests| FastApi
    end

    subgraph AgentCore["Agentic Core (LangGraph)"]
        Orchestrator["Supervisor & Intent Router Node"]
        DiscoveryAgent["Opportunity Discovery Agent"]
        EligibilityAgent["Eligibility Engine (Deterministic + Probabilistic)"]
        ResumeAgent["ATS Resume Customization Agent"]
        BrowserAgent["Playwright Form Execution Agent"]
        ApprovalNode{"Human-in-the-Loop Approval Gate"}

        Orchestrator --> DiscoveryAgent
        Orchestrator --> EligibilityAgent
        Orchestrator --> ResumeAgent
        Orchestrator --> BrowserAgent
        BrowserAgent --> ApprovalNode
    end

    subgraph DataLayer["Persistence & Caching Layer"]
        Postgres[("Supabase PostgreSQL (Tables & Relations)")]
        PgVector[("pgvector (768-dim Opportunity Embeddings)")]
        RedisCache[("Redis 7 (Session State & Task Broker)")]
        ArqWorkers["ARQ Background Workers"]
    end

    subgraph IntelligenceLayer["AI & Intelligence Providers"]
        GeminiFlash["Google Gemini 2.0 Flash (Reasoning & Function Calling)"]
        GeminiLive["Gemini Live Multilingual Audio API"]
        OlostepAPI["Olostep (Web Discovery, Scrape & Monitor)"]
        CrustdataAPI["Crustdata (Company Firmographics & Recruiter Intel)"]
    end

    FastApi <--> AgentCore
    VoiceGateway <--> GeminiLive
    DiscoveryAgent <--> OlostepAPI
    DiscoveryAgent <--> CrustdataAPI
    EligibilityAgent <--> GeminiFlash
    ResumeAgent <--> GeminiFlash
    AgentCore <--> RedisCache
    FastApi <--> Postgres
    EligibilityAgent <--> PgVector
    ArqWorkers <--> RedisCache
    ArqWorkers --> BrowserAgent
```

---

## 2. Voice Request Lifecycle

The platform prioritizes real-time, low-latency multilingual voice interaction across 7 Indian regional languages (Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and English).

```mermaid
sequenceDiagram
    autonumber
    actor Student as Indian Student
    participant Browser as Web Browser (Voice Orb)
    participant Gateway as FastAPI Voice Gateway
    participant Gemini as Gemini Live Audio API
    participant LangGraph as LangGraph Agent Core
    participant DB as Supabase PostgreSQL

    Student->>Browser: Speaks query (e.g., in Telugu/Hinglish)
    Browser->>Gateway: Streams PCM 16kHz audio chunks via WebSocket
    Gateway->>Gemini: Bidi streaming session (Real-time VAD & ASR)
    Gemini-->>Gateway: Transcribed text & detected language ('te' / 'hi')
    
    alt Needs Tool Execution / Opportunity Search
        Gemini->>LangGraph: Emits Function Call (e.g. `search_opportunities`)
        LangGraph->>DB: Query opportunities matching filters & vector similarity
        DB-->>LangGraph: Return verified opportunities
        LangGraph-->>Gemini: Tool response payload
        Gemini-->>Gateway: Synthesizes spoken regional voice audio
    else Conversational Advice
        Gemini-->>Gateway: Synthesizes spoken regional voice audio
    end

    Gateway-->>Browser: Audio buffer stream + transcript sync
    Browser-->>Student: Plays native voice response + renders UI card
```

---

## 3. Opportunity Discovery & Ingestion Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as Background Monitor / User Query
    participant Worker as ARQ Task Worker
    participant Olostep as Olostep API (/v1/searches, /v1/scrapes)
    participant Crustdata as Crustdata API (/company/enrich)
    participant Embedder as Gemini Embedding Engine
    participant DB as Supabase (PostgreSQL + pgvector)

    Scheduler->>Worker: Trigger opportunity ingestion task
    Worker->>Olostep: POST /v1/searches (Indian college internships 2026)
    Olostep-->>Worker: Candidate URLs and metadata
    Worker->>Olostep: POST /v1/scrapes (Markdown & structured extraction)
    Olostep-->>Worker: Raw eligibility criteria, stipends, deadlines
    Worker->>Crustdata: POST /company/enrich (Validate company legit, size, tech)
    Crustdata-->>Worker: Verified firmographic telemetry
    Worker->>Embedder: Generate 768-dim embeddings from job requirements
    Embedder-->>Worker: Dense vector representation
    Worker->>DB: Store in `opportunities`, `opportunity_eligibility`, and `opportunity_embeddings`
```

---

## 4. Application Execution Lifecycle & Approval Gate

Under no circumstances does an agent submit external applications without explicit user approval.

```mermaid
flowchart TD
    Start([User Requests Application Assistance]) --> Prep[LangGraph Application Node]
    Prep --> FetchProfile[Fetch Career Passport & Resume]
    FetchProfile --> Tailor[Tailor Resume via Resume Customization Agent]
    Tailor --> DryRun[Playwright Headless Form Extraction & Dry-Run Fill]
    DryRun --> CaptureScreenshot[Capture Full-Page Screenshot & Extracted Field Diffs]
    CaptureScreenshot --> CreateApproval[Create Row in `approval_requests` with Status: PENDING]
    CreateApproval --> NotifyUser[Notify User in Dashboard & Voice Orb]
    NotifyUser --> HumanChoice{User Approves Action?}
    
    HumanChoice -- "REJECTED" --> Cancel[Mark Approval REJECTED; Abort Action; Log Audit]
    HumanChoice -- "APPROVED" --> Execute[Playwright Final Submission with Audit Trail]
    Execute --> CaptureReceipt[Capture Submission Confirmation & Timestamp]
    CaptureReceipt --> UpdateStatus[Update `applications` table to SUBMITTED]
    UpdateStatus --> Complete([User Notified of Successful Submission])
```

---

## 5. Data Flow and Trust Boundaries

| Zone | Boundary | Authentication & Validation |
| :--- | :--- | :--- |
| **Zone 1: Public Web / Client** | User Browser to Frontend | HTTPS / WSS, CSP, CORS headers, Content Sanitization |
| **Zone 2: Application Gateway** | Frontend to FastAPI Gateway | Supabase JWT Bearer Tokens, Rate Limiting (Redis-backed token bucket) |
| **Zone 3: Internal Agent Network** | FastAPI to LangGraph / Workers | In-memory / Private Redis network, strict Pydantic schema validation |
| **Zone 4: Data Layer** | Backend to PostgreSQL / pgvector | SSL required, Row Level Security (RLS) enforcement per user session |
| **Zone 5: External Providers** | Backend to Olostep / Crustdata / Gemini | Outbound HTTPS with secret API keys managed via environment variables |
| **Zone 6: Browser Sandbox** | Playwright Worker to Target Job Portals | Isolated ephemeral browser context; never bypasses CAPTCHA; Human approval mandatory |
