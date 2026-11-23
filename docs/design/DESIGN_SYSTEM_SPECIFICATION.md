# Opportunity OS — Design System & Tokens Specification

**Role & Standard:** Senior Frontend Architecture Specification  
**Designated Owner:** Sanju (Frontend Lead) & `@opportunity-os/design-tokens`  
**Aesthetic:** *Autonomous Intelligence Campus* — Premium Futuristic Collegiate Tech Operating System  

---

## 1. Color Palette & Semantic Tokens

All colors are defined as CSS variables with semantic mapping in Tailwind CSS to ensure theme consistency and dark-theme contrast.

```css
:root {
  /* Surface Layers (Deep Midnight Navy) */
  --surface-base: #090D16;          /* Deepest canvas background */
  --surface-raised: #0E1526;        /* Sidebar and topnav elevation */
  --surface-card: #111827;          /* Cards and content tiles */
  --surface-overlay: #1A233A;       /* Modals, popovers, dropdowns */
  --surface-border: #1F2937;        /* Subtle divider borders */
  --surface-border-subtle: #374151; /* High-contrast borders */

  /* Brand Accents */
  --brand-primary: #4F46E5;         /* Electric Indigo (Primary CTAs) */
  --brand-primary-hover: #4338CA;   /* Pressed state */
  --brand-cyan: #06B6D4;            /* Neon Cyan (AI & Intelligence highlights) */
  --brand-violet: #8B5CF6;          /* Violet (Voice orb & agent streams) */
  --brand-glow: rgba(99, 102, 241, 0.25); /* Ambient drop shadows */

  /* Semantic Status */
  --status-eligible: #10B981;       /* Emerald Green (Qualified / Match) */
  --status-eligible-bg: rgba(16, 185, 129, 0.1);
  --status-warning: #F59E0B;        /* Amber (Approaching deadline / Skill gap) */
  --status-warning-bg: rgba(245, 158, 11, 0.1);
  --status-danger: #EF4444;         /* Coral Red (Disqualified / Aborted) */
  --status-danger-bg: rgba(239, 68, 68, 0.1);
  --status-info: #3B82F6;           /* Sky Blue (Application in progress) */

  /* Text Hierarchy */
  --text-primary: #F8FAFC;          /* Slate 50 (Headlines, titles) */
  --text-secondary: #94A3B8;        /* Slate 400 (Body, descriptions) */
  --text-muted: #64748B;            /* Slate 500 (Timestamps, captions) */
  --text-disabled: #475569;         /* Slate 600 */
}
```

---

## 2. Typography & Indian Script Font Fallback Strategy

Students across India read English, Hindi (Devanagari), Telugu, Tamil, Kannada, Malayalam, and Bengali. The typography system guarantees uniform x-height, proper ligatures, and zero layout shift across all seven scripts.

### Font Family Hierarchy
```css
font-family:
  var(--font-sans),
  /* Indic Script Fallbacks (High Quality Open Source Fonts) */
  'Noto Sans Devanagari', /* Hindi */
  'Noto Sans Telugu',     /* Telugu */
  'Noto Sans Tamil',      /* Tamil */
  'Noto Sans Kannada',    /* Kannada */
  'Noto Sans Malayalam',  /* Malayalam */
  'Noto Sans Bengali',    /* Bengali */
  system-ui,
  -apple-system,
  sans-serif;
```

### Type Scale (Fluid Rem Scale)
| Level | Font Size | Line Height | Weight | Usage |
| :--- | :---: | :---: | :---: | :--- |
| **Hero H1** | `3.0rem - 4.5rem` | `1.1` | `800 (ExtraBold)` | Landing Page Hero |
| **Section H2**| `2.0rem - 2.5rem` | `1.2` | `700 (Bold)` | Major Page Headings |
| **Card H3** | `1.25rem` | `1.4` | `600 (SemiBold)` | Opportunity Cards, Modals |
| **Body Large**| `1.125rem` | `1.6` | `400 (Regular)` | Lead text, summary paragraphs |
| **Body Base** | `1.0rem` | `1.5` | `400 (Regular)` | Standard text, inputs, buttons |
| **Caption** | `0.75rem` | `1.4` | `500 (Medium)` | Badges, tags, timestamps |

---

## 3. Core Component Variants & States

### 3.1 Button Variants (`Button.tsx`)
- **Primary:** `bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 active:scale-95`.
- **Secondary / Glass:** `bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 backdrop-blur-md`.
- **Ghost:** `hover:bg-slate-800 text-slate-300`.
- **Voice Trigger:** `bg-gradient-to-r from-indigo-600 via-cyan-500 to-violet-600 hover:opacity-90 text-white animate-glow`.
- **States:** `default`, `hover`, `active`, `focused` (`ring-2 ring-indigo-400`), `disabled` (`opacity-50 cursor-not-allowed`), `loading` (embedded spinner with accessible label).

### 3.2 Opportunity Card (`OpportunityCard.tsx`)
- **Container:** `bg-[#111827] border border-[#1F2937] hover:border-indigo-500/50 transition-all duration-300 rounded-xl p-5 hover:shadow-xl hover:shadow-indigo-500/5`.
- **Eligibility Pill:**
  - Eligible: `bg-emerald-500/10 text-emerald-400 border border-emerald-500/20` (`✓ Eligible`).
  - Ineligible: `bg-rose-500/10 text-rose-400 border border-rose-500/20` (`✕ 2024 Batch Disqualified`).

### 3.3 Approval Checkpoint Modal (`ApprovalModal.tsx`)
- **Container:** `z-[100] max-w-4xl bg-[#0E1526] border-2 border-amber-500/50 shadow-2xl rounded-2xl p-8 backdrop-blur-xl`.
- **Dry-Run Diff Table:** Clear split displaying what the agent extracted vs what it proposes to input into the employer portal.
- **Action Buttons:** High-contrast `Approve & Submit` (Emerald) vs `Reject & Abort` (Rose).
