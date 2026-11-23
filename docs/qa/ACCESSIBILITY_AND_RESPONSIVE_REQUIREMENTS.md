# Opportunity OS — Accessibility & Responsive Requirements

**Standard:** WCAG 2.1 Level AA Compliance  
**Target User Demographics:** Indian undergraduate students using low-to-mid tier Android smartphones, variable cellular networks (3G/4G/5G), and varying English language literacy.

---

## 1. Responsive Viewport Specifications

| Device Tier | Breakpoint Width | Primary UX Consideration | Status |
| :--- | :--- | :--- | :--- |
| **Mobile Compact** | $360\text{px} - 414\text{px}$ | Single-column opportunity feed; fixed bottom Voice Orb | Proposed Standard |
| **Mobile Standard** | $415\text{px} - 767\text{px}$ | Stacked layout; touch targets $\ge 48\text{px} \times 48\text{px}$ | Proposed Standard |
| **Tablet / Foldable** | $768\text{px} - 1023\text{px}$ | Two-column grid; collapsible sidebar navigation | Proposed Standard |
| **Desktop / Laptop** | $\ge 1024\text{px}$ | Multi-pane workspace (Resume Editor + Live PDF preview) | Proposed Standard |

---

## 2. Accessibility (a11y) Acceptance Criteria

1. **Contrast Ratio:** Text and interactive elements must maintain a minimum contrast ratio of `4.5:1` against the dark background (`#090D16`). Large text ($\ge 18\text{pt}$ or bold $\ge 14\text{pt}$) must maintain `3:1`.
2. **Keyboard Navigation:** Every actionable element (buttons, filters, cards, modals) must be operable via `Tab`, `Shift+Tab`, `Enter`, and `Space`. Focus outlines must be distinctly visible (`focus:ring-2 focus:ring-indigo-500`).
3. **Screen Reader Support:**
   - The 3D Voice Orb must include an `aria-label="Interactive Voice Assistant"` and announce status changes (`aria-live="polite"`: "Listening", "Processing", "Speaking").
   - Opportunity cards must have accessible names combining title and organization.
4. **Text Scaling:** Interface layout must remain fully readable and operable when user text zoom is increased up to `200%` without clipping or horizontal overflow.
5. **No Sole Color Coding:** Eligibility status cannot rely on green/red color alone; must include textual icons and badges (e.g. `✓ Eligible` / `✕ Ineligible`).
