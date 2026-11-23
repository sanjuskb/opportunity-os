# Opportunity OS — Frontend Test Architecture & Verification Matrix

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Frontend Testing & Quality Verification  
**Owner:** Sanju (Frontend & ML Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Implementation Target:** `apps/web/` Test Suites & CI Test Matrix  

---

## 1. Quality Strategy & Testing Pyramid

To ensure that Opportunity OS delivers flawless stability, accessibility, and voice interaction during live hackathon demos and production usage, the frontend implements a multi-tiered testing strategy structured around the classic testing pyramid:

```
                  / \
                 / E2E \              Playwright Browser Tests (Critical User Journeys)
                / Tests \             - Viewport tests (360px, 768px, 1280px)
               /---------\            - Voice Orb fallback & Approval gate
              / Integration\          MSW Network Mocking & TanStack Query Hooks
             /  & a11y Tests\         - axe-core automated accessibility audits
            /----------------\        - Route shell & component state transitions
           /    Unit & Store  \       Vitest + React Testing Library
          /     Specifications \      - Zustand store state machines (14 voice states)
         /----------------------\     - Pure formatters (Lakhs/Crores, Indic dates)
```

---

## 2. Testing Levels & Tooling Selection

| Test Tier | Technology Stack | Scope & Execution Frequency | Execution Speed |
| :--- | :--- | :--- | :--- |
| **1. Unit Tests** | Vitest | Formatters, Zod schemas, calculations | $< 2\text{s}$ (Local & Pre-commit) |
| **2. State Store Tests** | Vitest | Zustand stores (`useAuthStore`, `useVoiceOrbStore`) | $< 3\text{s}$ (Local & Pre-commit) |
| **3. Component Tests** | Vitest + React Testing Library | UI components, loading/error states, a11y | $< 15\text{s}$ (CI on all PRs) |
| **4. API Mock Tests** | Mock Service Worker (MSW) v2 | API client hooks, query invalidations, retries | $< 10\text{s}$ (CI on all PRs) |
| **5. Accessibility** | `vitest-axe` / `axe-core` | WCAG 2.1 AA violations on all components | $< 5\text{s}$ (CI on all PRs) |
| **6. End-to-End (E2E)** | Playwright | Full user journeys in Chromium, Firefox, WebKit | $< 90\text{s}$ (CI on merge to `develop`) |
| **7. Voice Simulation** | Custom Web Audio Mock + WS | Mock `AudioContext`, `MediaStream`, & WS frames | $< 5\text{s}$ (CI on all PRs) |

---

## 3. Zustand State Store Test Specifications

All client state machines must be tested for deterministic transitions and resets.

### 3.1 Voice Orb Store Test (`apps/web/src/stores/__tests__/useVoiceOrbStore.test.ts`)
Must verify:
1. Initial state is `IDLE` with volume `0` and empty transcript.
2. `setLifecycleState` transitions through the valid 14-state cycle:
   `IDLE` $\rightarrow$ `PERMISSION_REQUESTED` $\rightarrow$ `MIC_GRANTED` $\rightarrow$ `LISTENING` $\rightarrow$ `STREAMING_AUDIO` $\rightarrow$ `PROCESSING` $\rightarrow$ `RECEIVING_RESPONSE` $\rightarrow$ `PLAYING_RESPONSE` $\rightarrow$ `IDLE`.
3. Interruption transitions: Calling `setLifecycleState('USER_INTERRUPTION')` immediately mutes output volume and transitions state.
4. Error handling: Calling `setError(message)` sets error string and allows `resetVoiceState()` to restore clean `IDLE`.

### 3.2 Opportunity Filters Store Test (`apps/web/src/stores/__tests__/useOpportunityFiltersStore.test.ts`)
Must verify:
1. Default filters: batch matches current year, all opportunity types enabled, stipend `0`.
2. Setting search query, domain filters, or toggling remote updates state immutably.
3. `resetFilters()` restores canonical default filters.

---

## 4. Web Audio & Voice Lifecycle Simulation

Testing Web Audio and WebSocket communication in Node/JSDOM environments requires a deterministic mocking strategy.

### 4.1 Web Audio Mock Fixture
```typescript
// apps/web/src/test/mocks/mockWebAudio.ts
export class MockAudioContext {
  state: 'suspended' | 'running' | 'closed' = 'suspended';
  currentTime = 0;
  sampleRate = 48000;

  async resume() {
    this.state = 'running';
  }

  async close() {
    this.state = 'closed';
  }

  createMediaStreamSource() {
    return { connect: vi.fn(), disconnect: vi.fn() };
  }

  createAnalyser() {
    return {
      fftSize: 256,
      smoothingTimeConstant: 0.8,
      frequencyBinCount: 128,
      getByteFrequencyData: vi.fn(),
      getByteTimeDomainData: vi.fn(),
      connect: vi.fn(),
      disconnect: vi.fn(),
    };
  }
}
```

### 4.2 Simulated Voice Interruption Test Case
The test suite verifies:
1. When in `PLAYING_RESPONSE`, sending simulated incoming speech event triggers `USER_INTERRUPTION`.
2. The mock `AudioBufferSourceNode.stop()` is called immediately.
3. An `interrupted` event is emitted through the mock WebSocket.
4. The orb transitions back to `STREAMING_AUDIO`.

---

## 5. Playwright End-to-End (E2E) Test Plan

Playwright validates critical end-to-end user journeys against actual browser engines.

### 5.1 Critical Test Scenarios (`apps/web/e2e/`)

1. **`onboarding.spec.ts` — New Student Registration & Career Passport Setup:**
   - Visits landing page $\rightarrow$ clicks *"Get Started"* $\rightarrow$ enters college name, degree, graduation year, and top skills.
   - Verifies dashboard redirects and renders tailored welcome banner in selected Indian language.
2. **`opportunities-feed.spec.ts` — Discovery & Filtering:**
   - Navigates to `/opportunities` $\rightarrow$ types "React" into search bar $\rightarrow$ selects "Internship" chip $\rightarrow$ verifies filtered results update without full page reload.
3. **`eligibility-check.spec.ts` — Deterministic Eligibility Modal:**
   - Clicks on an opportunity $\rightarrow$ clicks *"Check My Eligibility"* $\rightarrow$ verifies 3-item checklist (Batch, Degree, CGPA) displays green checks and plain-language explanation.
4. **`approval-gate.spec.ts` — Human-in-the-Loop Approval Action:**
   - Navigates to pending approvals $\rightarrow$ inspects proposed application dry-run screenshot $\rightarrow$ clicks *"Approve Submission"* $\rightarrow$ verifies modal confirmation and status updates to "Submitted".
5. **`voice-fallback.spec.ts` — Microphone Denial Graceful Fallback:**
   - Denies microphone permission in browser context $\rightarrow$ clicks Voice Orb $\rightarrow$ verifies permission error modal appears $\rightarrow$ clicks *"Use Text Mode"* $\rightarrow$ verifies chat input opens cleanly.

### 5.2 Multi-Viewport Responsive Matrix

Every E2E test runs across three standardized viewports:
- **Mobile:** $375 \times 667$ (iPhone SE / Typical Indian Android device).
- **Tablet:** $768 \times 1024$ (iPad / Android Tablet).
- **Desktop:** $1280 \times 800$ (Standard laptop).

---

## 6. Continuous Integration (CI) Commands

```bash
# Run unit & component tests with coverage
pnpm --filter @opportunity-os/web test --coverage

# Run TypeScript type verification
pnpm --filter @opportunity-os/web type-check

# Run Next.js production build verification
pnpm --filter @opportunity-os/web build

# Run Playwright E2E browser test suite (headless)
pnpm --filter @opportunity-os/web test:e2e
```
