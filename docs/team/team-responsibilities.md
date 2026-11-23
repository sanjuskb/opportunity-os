# Opportunity OS — Engineering Responsibility Matrix & Team Allocation

## 1. Team Composition & Core Ownership

| Developer | Primary Role | Branch | Core Subsystems Owned |
| :--- | :--- | :--- | :--- |
| **Sanju** | Frontend Lead, UX Architect & Machine Learning Lead | `sanju` | Next.js 15+ frontend, TypeScript architecture, Tailwind & shadcn/ui, Three.js / React Three Fiber Voice Orb, Career Passport UI, Resume Studio, Application Dashboard. **All Machine Learning (ML)** model selection, embeddings evaluation, training experiments under `experiments/`, ranking and offline evaluation. |
| **Ramaraju** | Backend Lead & Agent / Automation Engineer | `ramaraju` | Entire FastAPI REST & WebSocket backend gateway, PostgreSQL & pgvector schema architecture and migrations, LangGraph agent state machines, Gemini Live backend proxy, Olostep & Crustdata integrations, Playwright browser automation execution. |
| **Shared** | Architecture, Contracts & Deployment | `develop` / `main` | System architecture, cross-team contracts, end-to-end integration, security decisions, deployment coordination, PR reviews. |
| **Antigravity** | Architecture QA & Engineering Readiness | `antigravity/*` | Repository QA, architecture consistency audits, documentation quality, test planning, developer tooling, CI/CD hardening. |

---

## 2. Responsibility Allocation Matrix (RACI)

| Deliverable / Subsystem | Sanju | Ramaraju | Review Requirement |
| :--- | :---: | :---: | :--- |
| **Frontend Web Architecture (`apps/web`)** | **A / R** | C | Ramaraju reviews API integration |
| **Design Tokens & UI (`packages/design-tokens`)** | **A / R** | I | Sanju autonomous |
| **Machine Learning & Models (`experiments/`, `docs/machine-learning`)** | **A / R** | C | Ramaraju reviews inference API contracts |
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

## 4. Proposed Sprint 1 Milestones (Corrected Allocation)

- **Sprint 1A (Days 1–2):** 
  - Sanju: Setup Next.js App shell, Navigation, 3D Voice Orb Canvas, Mock Opportunity Cards, Baseline ML embedding model evaluation notebook under `experiments/model-training/`.
  - Ramaraju: Wire FastAPI database connection, run initial Supabase migration, implement Olostep search adapter (`POST /v1/searches`).
- **Sprint 1B (Days 3–4):**
  - Sanju: Integrate live voice streaming over WebSocket to FastAPI Voice Gateway; evaluate speech recognition WER on Indic sample audio.
  - Ramaraju: Build Gemini Live proxy and LangGraph Opportunity Discovery workflow.
- **Sprint 1C (Days 5–6):**
  - Joint: End-to-end integration of Opportunity Discovery $\rightarrow$ Eligibility Check $\rightarrow$ Approval Gate $\rightarrow$ Playwright Dry-Run.
