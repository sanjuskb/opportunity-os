# Opportunity OS — Frontend Implementation Readiness Checklist

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Frontend Sprint Implementation Readiness  
**Owner & Lead:** Sanju (Frontend & ML Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Target App:** `apps/web/`  

---

## 1. Verified Core Package Matrix

All core packages have been audited against the monorepo root and `apps/web/package.json`. No conflicting state managers or redundant CSS frameworks are present.

| Technology / Library | Target Version | Current Installation Status | Verification & Role |
| :--- | :--- | :--- | :--- |
| **Next.js** | `15.2.1` | **Installed & Verified** | App Router, Server Actions, Standalone Docker output (`apps/web/.next/standalone`). |
| **React & React DOM** | `19.0.0` | **Installed & Verified** | Modern hooks (`useActionState`, `useOptimistic`), concurrent rendering. |
| **TypeScript** | `^5.8.2` | **Installed & Verified** | Strict type-checking, composite project references to workspace packages. |
| **Tailwind CSS** | `^3.4.17` | **Installed & Verified** | Design tokens, midnight navy theme, dark mode utilities. |
| **Zustand** | `^5.0.3` | **Installed & Verified** | Client UI state (`useAuthStore`, `useOpportunityFiltersStore`, `useVoiceOrbStore`). |
| **TanStack Query** | `^5.66.0` | **Phase 6 Sprint Install** | Server-state caching, optimistic updates, query invalidation. |
| **next-intl** | `^3.26.0` | **Phase 6 Sprint Install** | 7 Indic language message catalogs (EN, HI, TE, TA, KN, ML, BN). |
| **Spline React Runtime** | `@splinetool/react-spline` | **Phase 6 Sprint Install** | Autonomous Intelligence Campus 3D hero rendering (`ssr: false`). |
| **Supabase Auth SDK** | `@supabase/supabase-js` | **Phase 6 Sprint Install** | Student authentication, JWT refresh lifecycle. |
| **Forms & Validation** | `react-hook-form` + `zod` | **Phase 6 Sprint Install** | Accessible form control and schema validation for student onboarding. |
| **Lucide Icons** | `^1.16.0` | **Installed & Verified** | Accessible navigation and action icons. |
| **Vitest & RTL** | `vitest` + `@testing-library/react` | **Phase 6 Sprint Install** | Unit, component, and Zustand store test harnesses. |
| **Playwright** | `@playwright/test` | **Phase 6 Sprint Install** | End-to-end browser user journey testing across 360px, 768px, and 1280px. |

---

## 2. Sprint Implementation Checklist

This checklist provides Sanju with an unambiguous, step-by-step roadmap for Phase 6 implementation:

### Phase 6A: Foundations & Layout Shell
- [ ] **Step 1: Install Sprint Dependencies in `apps/web/`**
  ```bash
  pnpm --filter @opportunity-os/web add @tanstack/react-query@^5.66.0 next-intl@^3.26.0 @supabase/supabase-js@^2.48.0 react-hook-form@^7.54.0 zod@^3.24.0
  pnpm --filter @opportunity-os/web add -D vitest @testing-library/react @testing-library/user-event jsdom @playwright/test
  ```
- [ ] **Step 2: Theme & Global Styles Validation**
  - Verify CSS custom properties in `apps/web/src/app/globals.css` match `@opportunity-os/design-tokens`.
  - Ensure dark mode background (`#090D16`) and surface colors are active by default.
- [ ] **Step 3: Indic Typography Setup**
  - Configure `next/font/google` for Inter and the 6 Noto Sans Indic scripts in `apps/web/src/app/fonts.ts`.
- [ ] **Step 4: Authenticated Dashboard Shell**
  - Implement `apps/web/src/app/[locale]/(dashboard)/layout.tsx` with responsive Sidebar (desktop) and Bottom Navigation Bar (mobile).
  - Verify Voice Orb collision boundary ($80\text{px}$ clearance on mobile screens).

---

### Phase 6B: State Management & Hardware Service Layer
- [ ] **Step 5: Zustand Store Instantiation**
  - Implement `useAuthStore.ts` with session token, student ID, and reset actions.
  - Implement `useOpportunityFiltersStore.ts` with batch, domain, and stipend filters.
  - Implement `useVoiceOrbStore.ts` with the canonical 14-state machine enum.
- [ ] **Step 6: Audio Hardware Service (`AudioStreamingService`)**
  - Create `apps/web/src/services/audio/AudioStreamingService.ts`.
  - Encapsulate `AudioContext`, `MediaStream`, `AudioWorkletNode`, and `WebSocket`.
  - Ensure zero browser audio hardware instances enter Zustand stores.
- [ ] **Step 7: Voice Orb Visualizer Component**
  - Create `apps/web/src/components/voice/VoiceOrb.tsx` with HTML5 Canvas FFT analyser.
  - Add keyboard navigation (`Space` to talk, `Esc` to cancel).
  - Wire instant text-fallback button when mic permission is denied.

---

### Phase 6C: Core Workspaces & Human-in-the-Loop Gate
- [ ] **Step 8: Opportunities Feed & Search**
  - Implement `OpportunityCard.tsx` with deterministic eligibility badge.
  - Connect `useInfiniteQuery` with cursor-based pagination.
- [ ] **Step 9: Opportunity Detail & Gap Analysis Drawer**
  - Implement slide-over drawer showing missing skills and suggested quick learning paths.
- [ ] **Step 10: Career Passport Workspace**
  - Implement verified skills, academic records, and coursework management.
- [ ] **Step 11: Grounded ATS Resume Editor**
  - Implement split-screen editor linking every bullet point to a Career Passport ID.
  - Integrate live PDF preview.
- [ ] **Step 12: Human-in-the-Loop Approval Modal**
  - Implement `ApprovalCheckpointModal.tsx` displaying dry-run screenshot and field diffs.
  - Enforce accessible keyboard focus trap and explicit student consent checkbox.

---

### Phase 6D: 3D Hero & Multi-Language Synchronization
- [ ] **Step 13: 3D Hero Dynamic Wrapper**
  - Implement `CampusSceneWrapper.tsx` with dynamic import (`ssr: false`) and loading skeleton.
  - Add viewport gating: Render WebGL on desktop ($\ge 1024\text{px}$); render optimized WebP poster on mobile ($< 1024\text{px}$).
- [ ] **Step 14: Localization Catalogs**
  - Populate initial translations in `apps/web/messages/` (`en.json`, `hi.json`, `te.json`, etc.).
  - Implement currency formatting in Indian Lakhs/Crores (`₹ 1,50,000`).
