# Opportunity OS — Master Frontend Engineering Blueprint & Architecture Index

**Document Version:** 2.0.0 (Comprehensive Architecture Blueprint)  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Comprehensive Frontend System Architecture  
**Owner:** Sanju (Frontend & ML Lead)  
**Backend Partner:** Ramaraju (Backend & Database Lead)  
**Quality Assurance:** Antigravity (Architecture QA)  
**Target Repository:** `https://github.com/sanjuskb/opportunity-os`  
**Active Working Branch:** `antigravity/frontend-architecture` $\rightarrow$ `develop`  

---

## 1. Executive Summary & Product Mission

**Opportunity OS** is an autonomous, voice-first AI career and internship intelligence platform engineered specifically for Indian college students. 

Across India's $40,000+$ colleges and universities, students frequently face systemic barriers: opaque job eligibility criteria, fragmented application portals, English-language intimidation, and generic ATS resume rejections. Opportunity OS dismantles these barriers by combining:
1. **Multilingual Voice Interaction (7 Indic Languages):** English, Hindi, Telugu, Tamil, Kannada, Malayalam, and Bengali.
2. **Deterministic & Explainable Eligibility Matching:** Clear, audit-grade checks on graduation batch, degree, branch, and CGPA with actionable skill gap roadmaps.
3. **Career Passport & Grounded Resume Studio:** Zero-hallucination resume tailoring grounded exclusively in verified student achievements.
4. **Autonomous Opportunity Discovery & Human-in-the-Loop Execution:** Multi-source web discovery (Olostep, Crustdata) coupled with mandatory student approval checkpoints before any external application action is taken.

---

## 2. Non-Negotiable Team Ownership Matrix

Engineering ownership is strictly demarcated to ensure velocity and accountability across the two-developer team:

| Engineering Domain | Primary Lead | Supporting Role | Scope & Non-Negotiable Boundaries |
| :--- | :--- | :--- | :--- |
| **Frontend Architecture & UI/UX** | **Sanju** | Antigravity | Next.js 15 App Router, Tailwind CSS design system, responsive layouts, Radix primitives, animations. |
| **Voice Frontend & Audio Hardware** | **Sanju** | Antigravity | Web Audio API, AudioWorklets, Voice Orb visualizer, canvas particles, audio state synchronization. |
| **Machine Learning (ML)** | **Sanju** | Antigravity | **ALL ML model selection, training experiments, fine-tuning, embeddings, and evaluation.** (ML ownership is strictly held by Sanju). |
| **Backend Architecture & APIs** | **Ramaraju** | Antigravity | FastAPI REST endpoints, Pydantic schemas, dependency injection, authentication verification. |
| **Database & Migrations** | **Ramaraju** | Antigravity | PostgreSQL, Supabase schema definitions, Alembic / SQL migrations, indexing, Row-Level Security (RLS). |
| **Agentic Workflows & Tool Execution** | **Ramaraju** | Antigravity | LangGraph state machines, Gemini Live WebSocket proxy, Olostep / Crustdata ingestion, Playwright headless execution. |
| **Cross-Team Integration & Security** | **Shared** (Sanju + Ramaraju) | Antigravity | API DTO contracts, JWT lifecycle, RFC 7807 problem details, deployment topology, secret isolation. |
| **Repository QA & Architecture Standards** | **Antigravity** | Sanju & Ramaraju | CI pipelines, architecture audits, test planning, documentation quality, developer tooling. |

---

## 3. Master Architectural Documentation Index

This blueprint coordinates and links ten dedicated, in-depth architectural specifications:

| Deliverable | Specification Title | File Path & Link | Core Scope & Responsibilities |
| :--- | :--- | :--- | :--- |
| **D1** | **Page & Component Catalog** | [`FRONTEND_PAGE_COMPONENT_CATALOG.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_PAGE_COMPONENT_CATALOG.md) | Exhaustive component breakdown across Public, Onboarding, and Workspace routes; data dependencies, loading/empty/error states. |
| **D2** | **Navigation & Layout Architecture** | [`FRONTEND_NAVIGATION_AND_LAYOUT.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_NAVIGATION_AND_LAYOUT.md) | Breakpoint layouts (360px mobile to 1024px+ desktop), shell wireframes, persistent Voice Orb non-occlusion/collision rules. |
| **D3** | **Frontend State Architecture** | [`FRONTEND_STATE_ARCHITECTURE.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_STATE_ARCHITECTURE.md) | Zustand stores, TanStack Query v5 server caching, and the **Critical Voice Hardware Rule** banning AudioContext in React state. |
| **D4** | **Design System Specification** | [`DESIGN_SYSTEM_SPECIFICATION.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/design/DESIGN_SYSTEM_SPECIFICATION.md) | Midnight navy `#090D16`, cyan `#06B6D4`, indigo `#4F46E5` color tokens, typography scales, Indic script font fallbacks, UI components. |
| **D5** | **Voice Orb & Web Audio Lifecycle** | [`FRONTEND_VOICE_LIFECYCLE.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/voice/FRONTEND_VOICE_LIFECYCLE.md) | 14-state lifecycle state machine, AudioWorklet 16kHz PCM downsampling, WebSocket handshake, interruption handling, fallback flow. |
| **D6** | **Seven-Language Localization** | [`LOCALIZATION_ARCHITECTURE.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/i18n/LOCALIZATION_ARCHITECTURE.md) | `next-intl` App Router integration, 7 Indian language namespaces, font subsetting, text expansion rules, Lakhs/Crores formatting. |
| **D7** | **API Integration & Contracts** | [`FRONTEND_API_INTEGRATION_SPEC.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/architecture/FRONTEND_API_INTEGRATION_SPEC.md) | Typed `@opportunity-os/api-client` endpoints, TanStack Query keys, cache invalidation rules, RFC 7807 error mapping, backend questions. |
| **D8** | **Quality, a11y & Performance** | [`FRONTEND_QUALITY_ACCEPTANCE.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/qa/FRONTEND_QUALITY_ACCEPTANCE.md) | WCAG 2.1 AA checklist, contrast ratios, keyboard navigation matrix, Core Web Vitals targets, JS bundle budget $\le 180\text{KB}$. |
| **D9** | **Frontend Test Architecture** | [`FRONTEND_TEST_ARCHITECTURE.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/qa/FRONTEND_TEST_ARCHITECTURE.md) | Vitest unit/store tests, React Testing Library, MSW v2 network mocking, Web Audio simulation, Playwright E2E browser test matrix. |
| **D10** | **Deployment & Observability** | [`FRONTEND_DEPLOYMENT_AND_MONITORING.md`](file:///D:/ai%20career%20intelligence%20autonomous%20system/docs/deployment/FRONTEND_DEPLOYMENT_AND_MONITORING.md) | Vercel & Next.js standalone Docker containerization, environment variable matrix, Sentry error telemetry, Web Vitals reporting. |

---

## 4. Frontend Route & Component Topology

Opportunity OS leverages the Next.js 15 App Router with localized internationalized path routing (`/[locale]/...`):

```
apps/web/src/app/
├── layout.tsx                               # Root HTML, font preloads, theme script
├── [locale]/
│   ├── layout.tsx                           # Localized layout, next-intl provider, Voice Context
│   ├── page.tsx                             # High-impact Landing Page & Autonomous Intelligence Campus Hero
│   ├── (auth)/
│   │   ├── login/page.tsx                   # Supabase Auth Login
│   │   ├── register/page.tsx                # Multi-step Student Onboarding Wizard
│   │   └── callback/route.ts                # Auth exchange handler
│   └── (dashboard)/
│       ├── layout.tsx                       # Authenticated Shell (Sidebar, TopNav, Floating Voice Orb)
│       ├── overview/page.tsx                # Student Dashboard Overview & Application Funnel
│       ├── opportunities/
│       │   ├── page.tsx                     # Infinite Scroll Opportunity Feed & Filters
│       │   └── [id]/page.tsx                # Opportunity Deep-Dive, Eligibility Breakdown Drawer
│       ├── passport/
│       │   └── page.tsx                     # Career Passport: Verified Skills, Coursework & Projects
│       ├── resumes/
│       │   ├── page.tsx                     # Master Resume & Tailored Versions List
│       │   └── [id]/editor/page.tsx         # Grounded ATS Resume Editor & Live PDF Preview
│       ├── applications/
│       │   └── page.tsx                     # Kanban Application Tracker & Human Approval Checkpoint
│       ├── interview/
│       │   └── page.tsx                     # Real-time Voice Interview Practice Simulator
│       ├── analytics/
│       │   └── page.tsx                     # Indic Market Intelligence & Skill Gap Trends
│       └── settings/
│           └── page.tsx                     # Language Selection, Voice Preferences, Privacy Controls
```

---

## 5. 3D Hero Integration Boundary: "Autonomous Intelligence Campus"

The landing page features an interactive 3D miniature campus ("Autonomous Intelligence Campus") visualizing the interconnected AI ecosystem (Central AI Core, connected Student/Company/University hubs, and floating UI interfaces).

Extensive asset research has been conducted and preserved on branch `antigravity/3d-hero-asset-research` (identifying Spline CC BY 4.0 scene *"3D City - Navigation"* by aximoris as the leading base asset).

### 5.1 Architecture Boundary & Encapsulation Specification

To guarantee that 3D rendering never delays landing page interactivity or breaks low-end devices:

1. **Strict DOM/Canvas Wrapper Encapsulation (`CampusSceneWrapper.tsx`):**
   - The 3D scene is strictly encapsulated in `@/components/hero/CampusSceneWrapper.tsx`.
   - The wrapper accepts abstract event callbacks (`onHubClick(hubId: string)`, `onCameraMove(step: number)`) and exposes zero internal Three.js or Spline runtime objects to the rest of the application.
2. **Lazy Dynamic Loading (`ssr: false`):**
   ```typescript
   // apps/web/src/components/hero/CampusHeroSection.tsx
   const CampusSceneWrapper = dynamic(
     () => import('@/components/hero/CampusSceneWrapper'),
     {
       ssr: false,
       loading: () => <CampusHeroSkeleton />,
     }
   );
   ```
3. **Viewport Gating & Responsive Fallback:**
   - **Desktop ($\ge 1024\text{px}$):** Renders the full interactive WebGL canvas.
   - **Mobile & Tablet ($< 1024\text{px}$):** The WebGL canvas is completely omitted. Instead, a lightweight WebP vector illustration poster ($< 65\text{KB}$) is displayed with layered HTML text overlays, ensuring instant load times and zero battery drain on mobile phones.
4. **Reduced Motion Adaptation:**
   - If `window.matchMedia('(prefers-reduced-motion: reduce)').matches` is true, camera fly-through animations and spinning particle rings are disabled, freezing the scene in an elegant static isometric angle.
5. **GPU Lifecycle & Memory Hygiene:**
   - When the hero section scrolls out of the viewport, the render loop is paused via `cancelAnimationFrame`.
   - On component unmount, all geometries, textures, and WebGL render targets are explicitly destroyed via `.dispose()`.

---

## 6. Frontend State Management Architecture

Client state is strictly partitioned into three specialized domains to eliminate re-render cascades:

```
+--------------------------------------------------------------------------+
| SERVER CACHE & DATA SYNCHRONIZATION (TanStack Query v5)                  |
| - Opportunities feed, filters, search queries, and pagination cursors    |
| - Student profile records & Career Passport verified achievements        |
| - Grounded resume JSON schemas & PDF download URLs                       |
| - Pending human-in-the-loop approval requests                            |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
| CLIENT UI & NAVIGATION STATE (Zustand 5)                                 |
| - useAuthStore: Session token, student ID, isAuthenticated               |
| - useOpportunityFiltersStore: Active filters, batch year, search string  |
| - useVoiceOrbStore: Lifecycle enum (14 states), volumes, transcripts     |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
| NON-REACTIVE HARDWARE SERVICE LAYER (Encapsulated Singletons / Refs)     |
| - window.AudioContext & MediaStream (Microphone input)                   |
| - AudioWorkletNode (16kHz downsampling engine)                           |
| - WebSocket connection (`/api/v1/voice/stream`)                          |
| - AnalyserNode (FFT audio visualization spectrum data)                   |
+--------------------------------------------------------------------------+
```

### 6.1 The Non-Reactive Audio Boundary Rule
> [!IMPORTANT]
> Browser audio objects (`AudioContext`, `MediaStream`, `AudioWorkletNode`, and `WebSocket`) **MUST NEVER** be placed inside React state or Zustand stores. They are encapsulated strictly inside `AudioStreamingService` and accessed via React refs or imperative service commands. Zustand stores only light serializable state (state enum, transcript text, volume numbers).

---

## 7. Voice Interaction & Seven-Language Architecture

### 7.1 14-State Voice Lifecycle
The Voice Orb operates as a deterministic 14-state machine:
$$\text{IDLE} \rightarrow \text{PERMISSION\_REQUESTED} \rightarrow \text{MIC\_GRANTED} \rightarrow \text{LISTENING} \rightarrow \text{SPEECH\_DETECTED} \rightarrow \text{STREAMING\_AUDIO} \rightarrow \text{PROCESSING} \rightarrow \text{RECEIVING\_RESPONSE} \rightarrow \text{PLAYING\_RESPONSE} \rightarrow \text{IDLE}$$
Supporting full-duplex user interruptions (`USER_INTERRUPTION`), network retries (`RECONNECTING`), and zero-friction text fallback (`isTextFallbackActive`).

### 7.2 Seven Supported Indic Languages
Complete localization is delivered for:
1. `en` — English (Latin)
2. `hi` — Hindi (Noto Sans Devanagari)
3. `te` — Telugu (Noto Sans Telugu)
4. `ta` — Tamil (Noto Sans Tamil)
5. `kn` — Kannada (Noto Sans Kannada)
6. `ml` — Malayalam (Noto Sans Malayalam)
7. `bn` — Bengali (Noto Sans Bengali)

Typography ensures no vowel matra diacritic clipping (`leading-relaxed`), flexible UI containers accommodate $20\text{--}35\%$ text expansion, and financial stipends are displayed in the Indian numbering system (Lakhs & Crores: e.g. ₹ 1,50,000).

---

## 8. Quality, Performance & Verification Gates

All pull requests into `develop` must pass four strict automated quality gates:

1. **TypeScript Type Safety:** `pnpm --filter @opportunity-os/web type-check` with zero errors.
2. **Next.js Production Build:** `pnpm --filter @opportunity-os/web build` generating standalone output with First Load JS $\le 180\text{KB}$.
3. **Accessibility Audit:** Automated `axe-core` tests ensuring zero WCAG 2.1 AA violations on all interactive components.
4. **Backend Contract Alignment:** All request/response types match `@opportunity-os/shared-types` and Pydantic schemas in `apps/api/app/schemas/`.

---

## 9. Sprint Kickoff Implementation Checklist for Sanju

Sanju can immediately proceed with Phase 6 frontend implementation following this prioritized roadmap:

- [ ] **Step 1: Design Tokens & Layout Shell**
  - Verify Tailwind 3.4 configuration and CSS variables in `apps/web/src/app/globals.css`.
  - Implement `DashboardLayout` shell with responsive sidebar and mobile bottom navigation tab bar.
- [ ] **Step 2: Localization Setup**
  - Configure `next-intl` routing and create namespace files under `apps/web/messages/`.
  - Add Google Indic Fonts in `apps/web/src/app/fonts.ts`.
- [ ] **Step 3: Zustand Stores & AudioStreamingService**
  - Implement `useVoiceOrbStore.ts` and `useOpportunityFiltersStore.ts`.
  - Create `AudioStreamingService.ts` encapsulating `AudioContext`, `MediaStream`, and `AudioWorkletNode`.
- [ ] **Step 4: Voice Orb Component**
  - Implement `VoiceOrb.tsx` with Canvas FFT visualizer and keyboard accessibility (`Space` to talk).
- [ ] **Step 5: Opportunities Feed & Eligibility Drawer**
  - Implement `OpportunityCard.tsx`, infinite scroll query, and deterministic eligibility score badge.
- [ ] **Step 6: Human-in-the-Loop Approval Modal**
  - Implement `ApprovalCheckpointModal.tsx` with dry-run screenshot diff viewer and accessible focus trap.
- [ ] **Step 7: ATS Resume Editor**
  - Implement split-screen grounded resume editor with live PDF download preview.
- [ ] **Step 8: 3D Hero Scene Integration**
  - Integrate `CampusSceneWrapper.tsx` dynamically with desktop/mobile viewport gating.
