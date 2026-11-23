# Opportunity OS — Frontend Quality, Accessibility & Performance Acceptance

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Quality Assurance, Accessibility (a11y) & Performance Budgets  
**Owner:** Sanju (Frontend & ML Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Implementation Target:** `apps/web/` CI Gates & Playwright Test Harness  

---

## 1. Executive Quality Commitment

Opportunity OS is engineered for Indian students who frequently access educational tools on budget Android smartphones, low-bandwidth 4G connections, and shared campus computer labs. High performance and uncompromising accessibility are not optional polish; they are fundamental requirements for educational equity.

This specification establishes **non-negotiable quality gates** enforced across all pull requests in CI and automated browser tests.

---

## 2. Accessibility (a11y) Acceptance Specification — WCAG 2.1 AA

All pages, dialogs, widgets, and form controls must strictly achieve **WCAG 2.1 Level AA** compliance.

### 2.1 Color Contrast Standards

In our dark-mode design system:
- **Normal Text ($< 18\text{pt}$ / $24\text{px}$):** Contrast ratio $\ge 4.5:1$ against adjacent backgrounds.
  - White `#FFFFFF` on Midnight Navy `#090D16`: $18.2:1$ (Passes AAA).
  - Slate-300 `#CBD5E1` on Card Background `#111827`: $9.8:1$ (Passes AAA).
  - Slate-400 `#94A3B8` on Surface Background `#1E293B`: $5.1:1$ (Passes AA).
- **Large Text ($\ge 18\text{pt}$ or $\ge 14\text{pt}$ bold):** Contrast ratio $\ge 3.0:1$.
- **Interactive UI Components & Borders:** Focus rings and active borders (`#06B6D4` Cyan) must achieve $\ge 3.0:1$ against adjacent surface colors.

### 2.2 Screen Reader & Semantic Structure

1. **Semantic Landmarks:** Every page must contain exactly one `<main>`, one `<header>`, one `<nav>`, and one `<footer>` (or contextual `<aside>`).
2. **Accessible Name Computation:**
   - All icon-only buttons (e.g. Voice Orb, notifications bell, bookmark heart, close dialog `X`) **MUST** have an explicit `aria-label` or visually hidden `<span className="sr-only">`.
3. **Live Regions for Dynamic Voice Updates:**
   - Real-time speech recognition transcripts and agent speech status must be wrapped in `<div aria-live="polite" aria-atomic="true" className="sr-only">` so non-sighted students using screen readers (TalkBack on Android, NVDA on Windows) receive immediate updates.
4. **Modal Focus Traps & ESC Dismissal:**
   - When the Human-in-the-Loop Approval Modal opens:
     - Focus automatically moves to the first interactive element.
     - Tab navigation is strictly trapped inside the dialog container.
     - Pressing `Escape` closes the modal without submitting.
     - Body scrolling is locked (`overflow: hidden`).

### 2.3 Keyboard Navigation Matrix

| Component | Key | Expected Action |
| :--- | :--- | :--- |
| **Voice Orb** | `Space` or `Enter` | Toggle voice recording on/off |
| **Voice Orb** | `Escape` | Cancel voice session & teardown |
| **Opportunity Cards** | `Tab` / `Shift+Tab` | Navigate through cards sequentially |
| **Opportunity Cards** | `Enter` | Open detail drawer/page |
| **Language Switcher** | `ArrowDown` / `ArrowUp` | Traverse Indian language options |
| **Modal Dialog** | `Escape` | Dismiss modal |

### 2.4 Mobile Touch Targets

In accordance with WCAG 2.5.5 and mobile ergonomics:
- All primary interactive elements (buttons, bottom bar tabs, Voice Orb, filter chips) must have a minimum interactive tap target of **$48 \times 48\text{px}$**.
- Adjacent touch targets must maintain a minimum spacing of **$8\text{px}$** to eliminate accidental taps on small mobile touchscreens.

### 2.5 Text Scaling up to 200%

The layout must tolerate a user-configured font scaling up to **200%** without text clipping, overlapping boxes, or broken flex containers. All font sizing uses relative `rem` units (`text-sm`, `text-base`, `text-lg`) rather than fixed `px` values.

---

## 3. Performance Acceptance Budgets

Performance budgets are evaluated against Google Chrome's Core Web Vitals on a simulated **Mid-Tier Mobile Device (Moto G4 / 4G Network)**.

### 3.1 Core Web Vitals Targets

| Metric | Target (Good) | CI Warning Threshold | CI Hard Failure |
| :--- | :--- | :--- | :--- |
| **Largest Contentful Paint (LCP)** | $\le 2.0\text{s}$ | $> 2.2\text{s}$ | $> 2.5\text{s}$ |
| **Interaction to Next Paint (INP)** | $\le 150\text{ms}$ | $> 180\text{ms}$ | $> 200\text{ms}$ |
| **Cumulative Layout Shift (CLS)** | $\le 0.05$ | $> 0.08$ | $> 0.10$ |
| **First Input Delay (FID)** | $\le 80\text{ms}$ | $> 100\text{ms}$ | $> 200\text{ms}$ |
| **Time to First Byte (TTFB)** | $\le 300\text{ms}$ | $> 500\text{ms}$ | $> 800\text{ms}$ |

### 3.2 JavaScript Bundle Budgets

| Target Route / Asset | Maximum Budget (Gzipped) | Current Measured Baseline |
| :--- | :--- | :--- |
| **Root Shared JS Chunk** | $\le 100\text{KB}$ | $78\text{KB}$ (Passes) |
| **Landing Page Route (`/`)** | $\le 180\text{KB}$ | $101\text{KB}$ (Passes) |
| **Dashboard Feed (`/opportunities`)**| $\le 160\text{KB}$ | Pending Implementation |
| **Resume Studio Route (`/resumes`)**| $\le 190\text{KB}$ | Pending Implementation |
| **Total First Load JS (All Pages)** | $\le 180\text{KB}$ | **Strict CI Budget** |

---

## 4. WebGL 3D Scene Lazy Loading & Mobile Optimization

To ensure the 3D Hero scene ("Autonomous Intelligence Campus") never compromises landing page load speed:

1. **Dynamic Import with SSR Disabled:**
   ```typescript
   const Campus3DScene = dynamic(() => import('@/components/hero/Campus3DScene'), {
     ssr: false,
     loading: () => <CampusHeroSkeleton />,
   });
   ```
2. **Viewport Gating:**
   - On screens $< 1024\text{px}$ (Mobile & Tablet): The WebGL canvas is **not loaded**. Instead, a high-density, pre-rendered WebP poster image ($< 65\text{KB}$) is displayed.
3. **Intersection Observer Activation:**
   - WebGL initialization does not begin until the hero section enters the viewport.
   - When the user scrolls past the hero section, the render loop pauses (`cancelAnimationFrame`) to conserve GPU and battery life.
4. **Context Loss Recovery:**
   - The canvas registers `webglcontextlost` and `webglcontextrestored` event listeners to safely clean up GPU textures and restore rendering without a page reload.

---

## 5. Resilience & Error Boundary Hierarchy

To protect against unexpected runtime errors during client execution:

```
+--------------------------------------------------------------------------+
| ROOT APPLICATION ERROR BOUNDARY (app/global-error.tsx)                   |
| Catches fatal top-level rendering exceptions; provides fallback recovery |
+--------------------------------------------------------------------------+
                                    |
+--------------------------------------------------------------------------+
| ROUTE SHELL ERROR BOUNDARY (app/[locale]/error.tsx)                      |
| Isolates page-level navigation failures; preserves sidebar and nav bar   |
+--------------------------------------------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-----------------------------+         +----------------------------------+
| WIDGET ERROR BOUNDARY       |         | VOICE ORB ERROR BOUNDARY         |
| (Opportunity Feed / Cards)  |         | (Microphone / Web Audio stream)  |
| Shows inline retry card     |         | Offers instant text-mode button  |
+-----------------------------+         +----------------------------------+
```
