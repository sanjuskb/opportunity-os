# Opportunity OS — Engineering Responsibility Matrix & Team Allocation

## 1. Team Composition & Core Ownership

| Developer | Primary Role | Branch | Core Subsystems Owned |
| :--- | :--- | :--- | :--- |
| **Sanju** | Frontend Lead & UX Architect | `sanju` | Next.js 15+, TypeScript architecture, Tailwind & shadcn/ui, Three.js / React Three Fiber Voice Orb, Career Passport UI, Resume Studio, Application Dashboard. |
| **Ramaraju** | Backend Lead & AI / Data Engineer | `ramaraju` | FastAPI REST & WebSockets, PostgreSQL & pgvector schema, LangGraph agent state machines, Gemini Live integration, Olostep & Crustdata integrations, Playwright automation. |

---

## 2. Responsibility Allocation Matrix (RACI)

| Deliverable / Subsystem | Sanju | Ramaraju | Review Requirement |
| :--- | :---: | :---: | :--- |
| **Frontend Web Architecture (`apps/web`)** | **A / R** | C | Ramaraju reviews API integration |
| **Design Tokens & UI (`packages/design-tokens`)** | **A / R** | I | Sanju autonomous |
| **Backend REST & WS Core (`apps/api`)** | C | **A / R** | Sanju reviews endpoint contracts |
| **LangGraph Agent Workflows** | C | **A / R** | Both test user flow |
| **Database Migrations (`supabase/migrations`)** | C | **A / R** | Both must approve before merge |
| **Shared Types & DTOs (`packages/shared-types`)** | **R** | **R** | Mutual sign-off mandatory |
| **Browser Execution Approval Gate** | **R (UI)** | **R (Agent)** | Critical joint verification |

*R = Responsible, A = Accountable, C = Consulted, I = Informed.*

---

## 3. Parallel Development & Conflict Prevention

To prevent Git merge conflicts and enable seamless concurrent development:
1. **Contract-First Development:** Shared types in `packages/shared-types` are finalized first. Sanju mocks backend responses locally via `@opportunity-os/api-client` while Ramaraju implements the underlying endpoints.
2. **Dedicated Branching:** Sanju works on `sanju` (or `feature/sanju-*`); Ramaraju works on `ramaraju` (or `feature/ramaraju-*`).
3. **Integration on `develop`:** Pull requests always target `develop`. `main` is reserved exclusively for production-ready releases.

---

## 4. Proposed Sprint 1 Milestones

- **Sprint 1A (Days 1–2):** 
  - Sanju: Setup Next.js App shell, Navigation, 3D Voice Orb Canvas, Mock Opportunity Cards.
  - Ramaraju: Setup FastAPI database connection, run initial Supabase migration, implement Olostep search adapter.
- **Sprint 1B (Days 3–4):**
  - Sanju: Integrate live voice streaming over WebSocket to FastAPI Voice Gateway.
  - Ramaraju: Build Gemini Live proxy and LangGraph Opportunity Discovery workflow.
- **Sprint 1C (Days 5–6):**
  - Joint: End-to-end integration of Opportunity Discovery $\rightarrow$ Eligibility Check $\rightarrow$ Approval Gate $\rightarrow$ Playwright Dry-Run.
