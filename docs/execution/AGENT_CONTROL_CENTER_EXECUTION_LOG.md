# OPPORTUNITY OS — AGENT CONTROL CENTER (VORTEX COGNITION LAB)
## EXECUTION LOG & SYSTEM SPECIFICATION

**Author:** Autonomous Agent Architecture Team  
**Date:** 24 November 2026  
**Repository:** `sanjuskb/opportunity-os`  
**Branch:** `sanju`  
**Route:** `/agent-control-center`  
**Visual Reference:** VORTEX — COGNITION LAB (`media_1795527367882_60454da5.jpg`)

---

## 1. EXECUTIVE SUMMARY & OBJECTIVE

Opportunity OS is an intelligent operating system orchestrating an autonomous multi-agent workforce across students, companies, universities, and live opportunities.

To provide operators with complete visibility into this distributed ecosystem, we built the **Agent Control Center** (`/agent-control-center`). Inspired by the provided **VORTEX — COGNITION LAB** architectural interface, this module serves as the central nervous system of Opportunity OS, featuring:

1. **Interactive Agent Network Topology:** A real-time SVG network canvas rendering orbital rings, glowing halo nodes, cubic Bezier connection lines, animated traveling packets (`<animateMotion>`), pulsating core supervisors, and dynamic selection halos.
2. **Real-time Event Stream & Telemetry:** A live telemetry feed on the left displaying streaming agent events, execution timestamps, severity levels, active quality stages, and human-in-the-loop approval gates.
3. **Deep Agent Inspector & Phase 5 Surface:** A dual-mode right panel providing granular agent telemetry (success rate, latency, execution counts, access tools, connected peers) alongside external service bridge monitors (LangGraph cyclic state machine, Gemini Live WebSockets, Olostep scraper engine, Crustdata API, and DigiLocker NAD gateway).
4. **Natural Query & Command Dispatch Bar:** An operator dispatch bar supporting keyboard-driven synthetic test dispatches, category filter shortcuts, and voice interaction hooks.
5. **Structured Inventory Grid:** A bidirectional tabular view of all 14 ecosystem agents with instant filtering, search, and direct focus capabilities.
6. **Workspace Integration:** Positioned directly before `Settings` across all authenticated role sidebars (Student, Company, University).

---

## 2. AGENT WORKFORCE CATALOG (14 ECOSYSTEM AGENTS + 7 BRIDGES)

| Code | Agent Name | Category | Tier | Role & Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **M01** | **Supervisor Intent Agent** | Orchestration | Implemented | Master coordinator parsing multimodal user intent and routing context to downstream LangGraph pipelines. |
| **M02** | **Workflow State Coordinator** | Orchestration | Implemented | Maintains cyclic execution state, LangGraph checkpointing, and agent-to-agent state transitions. |
| **M03** | **Opportunity Discovery Agent** | Discovery | Implemented | Scrapes institutional placement feeds, alumni portals, and job boards. |
| **M04** | **Deduplication & Vector Indexer** | Discovery | Implemented | Computes BGE embeddings, deduplicates opportunities, and indexes vectors into Supabase pgvector. |
| **M05** | **Portal Monitoring Shuttle** | Discovery | Implemented | Autonomous background cron detecting career site updates and salary/deadline revisions. |
| **M06** | **Deterministic Eligibility Agent** | Verification | Implemented | Computes strict boolean gates (CGPA, backlog, graduation year, AICTE guidelines) without hallucination. |
| **M07** | **DigiLocker Institutional Gateway** | Verification | Implemented | Cryptographically verifies academic transcripts, degrees, and national academic depository credentials. |
| **M08** | **ATS Resume Intelligence Agent** | Resume Intel | Implemented | Synthesizes tailored resume sections strictly from verified student records with 94%+ ATS alignment. |
| **M09** | **Hallucination NLI Gate** | Resume Intel | Implemented | Natural Language Inference premise-hypothesis verifier ensuring 0% fabricated facts on resumes. |
| **M10** | **Application Form Mapper** | Execution | Implemented | Deterministically maps student profiles to complex multi-step corporate job application forms. |
| **M11** | **Human-in-the-Loop Safety Gate** | Execution | Implemented | Strict approval gate requiring operator or student confirmation prior to outbound submission. |
| **M12** | **Playwright Sandbox Executor** | Execution | Implemented | Headless browser executor automating portal submissions within isolated cloud containers. |
| **M13** | **Multilingual Voice Copilot** | Voice & Interview | Implemented | Real-time speech copilot streaming across 7 Indian regional languages via Gemini Live audio. |
| **M14** | **Mock Interview Intelligence Agent** | Voice & Interview | Implemented | Conducts adaptive technical/behavioral mock interviews with real-time feedback and transcripts. |

### External Service Bridges (Phase 5 Surface)
- **M91: LangGraph State Engine** (Status: `RUNNING`)
- **M92: Gemini Live Voice WS** (Status: `STREAMING`)
- **M93: Supabase DB & Auth** (Status: `CONNECTED`)
- **M94: Olostep Scraper Engine** (Status: `RUNNING`)
- **M95: Crustdata Enrichment API** (Status: `CONNECTED`)
- **M96: DigiLocker NAD Gateway** (Status: `STANDBY`)
- **M97: Playwright Chromium Sandbox** (Status: `STANDBY`)

---

## 3. ARCHITECTURE & CODE INVENTORY

```
apps/web/src/
├── app/
│   └── agent-control-center/
│       └── page.tsx                     # Main layout & responsive orchestrator
├── components/
│   ├── agent-control/
│   │   ├── types.ts                     # TypeScript schemas & contracts
│   │   ├── agentData.ts                 # Workforce inventory & network node coordinates
│   │   ├── useAgentControlStore.ts      # Zustand state store with interactive actions
│   │   ├── AgentNetworkGraph.tsx        # High-performance SVG network graph
│   │   ├── AgentControlHeader.tsx       # VORTEX header, status pills, speed toggles
│   │   ├── AgentCategoryFilterPills.tsx # Category filters & active workflow pills
│   │   ├── AgentEventStream.tsx         # Live telemetry feed & approval gates
│   │   ├── AgentInspector.tsx           # Selected agent deep-dive & test dispatch
│   │   ├── Phase5IntegrationSurface.tsx # Service bridges & synthetic upload routing
│   │   ├── AgentCommandBar.tsx          # Operator dispatch query bar
│   │   └── AgentInventoryView.tsx       # Bidirectional tabular inventory
│   └── dashboard/
│       └── DashboardLayout.tsx          # Workspace sidebar with Agent Control Center
```

---

## 4. VERIFICATION & QUALITY ASSURANCE

1. **Static Analysis & Next.js Build:**
   - Full monorepo build succeeded via `pnpm --filter @opportunity-os/web build`.
   - All 31 app routes compiled statically with zero TypeScript or ESLint errors.
   - Bundle size for `/agent-control-center`: 19 kB (148 kB First Load JS).

2. **Interactive Testing via Headless Browser (Playwright):**
   - **Network Graph Rendering:** Verified node rendering, SVG radial gradients, and animated data packets traveling across connecting edges.
   - **Click-to-Focus:** Clicking node `M08` (ATS Resume Intelligence Agent) instantly focused the camera, dimmed non-connected nodes, and refreshed the right-hand Agent Inspector.
   - **Synthetic Test Dispatch:** Dispatched synthetic test payload to `M01` Supervisor Intent Agent; verified instant transition to `busy`, automatic return to `active`, and dispatch logs registered in the live event stream.
   - **Workflow Quick Filters:** Executed "Trace Resume Pipeline"; verified graph isolation to M08 and M09, category filter update to `[R] RESUME INTEL`, and query bar confirmation.
   - **Panel Drawer Toggles:** Verified smooth collapsing of both the left Event Stream drawer and right Inspector drawer, allowing the network graph to span 100% of the viewport width.
   - **Inventory View:** Verified bidirectional synchronization between table selection and graph focus.

---

## 5. REPOSITORY SYNCHRONIZATION

- **Branch:** `sanju`
- **Remote:** `origin/sanju`
- All changes staged, documented, and committed cleanly under standard conventional commit conventions.
