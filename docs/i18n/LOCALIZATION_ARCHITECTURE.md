# Opportunity OS — Seven-Language Localization Architecture Specification

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Frontend Internationalization (i18n) & Localization (l10n)  
**Owner:** Sanju (Frontend & ML Lead)  
**Supporting Architect:** Antigravity (Architecture QA)  
**Implementation Target:** `apps/web/src/i18n/`, `apps/web/messages/`, and `apps/web/src/app/[locale]/`  

---

## 1. Multilingual Mission for Indian Higher Education

Opportunity OS is designed specifically to dismantle language and accessibility barriers for college students across India. In tier-2 and tier-3 colleges, talented students are frequently disadvantaged by English-only job portals, complex corporate jargon, and rigid application interfaces.

Opportunity OS delivers first-class support for **7 major Indian languages**:

1. **English (`en`)** — Default universal interface & technical reference
2. **Hindi (`hi`)** — हिन्दी (Devanagari script)
3. **Telugu (`te`)** — తెలుగు (Telugu script)
4. **Tamil (`ta`)** — தமிழ் (Tamil script)
5. **Kannada (`kn`)** — ಕನ್ನಡ (Kannada script)
6. **Malayalam (`ml`)** — മലയാളം (Malayalam script)
7. **Bengali (`bn`)** — বাংলা (Bengali script)

Localization in Opportunity OS is not just static string translation: it synchronizes **UI typography**, **voice speech recognition and synthesis**, **currency and date formatting**, and **code-switching comprehension**.

---

## 2. Localization Framework Selection: `next-intl`

### 2.1 Technology Evaluation & Decision

We evaluated three potential frameworks for Next.js 15 App Router localization:
1. `react-i18next` / `next-i18next`
2. `next-intl` (Selected)
3. Custom React context dictionary loader

| Evaluation Criterion | `next-intl` (Selected) | `react-i18next` | Custom Context Loader |
| :--- | :--- | :--- | :--- |
| **Next.js 15 App Router Support** | Native, first-class Server & Client Component support | Complex SSR wrappers required | Requires manual hydration plumbing |
| **Bundle Impact** | Minimal ($< 12\text{KB}$ gzipped) | Heavy ($> 45\text{KB}$ with plugins) | Zero dependency ($< 3\text{KB}$), but lacks ICU |
| **ICU Message Syntax** | Full support (plurals, gender, select, variables) | Supported via separate plugin | Not supported (raw string replace) |
| **Server Component Translation** | Async `getTranslations()` without client JS | Requires client hydration boundary | Can be built, but error-prone |
| **Type Safety** | Autocomplete and compile-time key validation | Manual type augmentation | None without custom generator |

**Architecture Decision:** Standardize on **`next-intl`** across `@opportunity-os/web`.

---

## 3. Directory Structure & Namespace Architecture

All localization message files are stored under `apps/web/messages/` structured by language code. To prevent massive single files and support lazy loading, strings are organized into coherent functional namespaces.

```
apps/web/
├── messages/
│   ├── en.json
│   ├── hi.json
│   ├── te.json
│   ├── ta.json
│   ├── kn.json
│   ├── ml.json
│   └── bn.json
├── src/
│   ├── app/
│   │   ├── [locale]/
│   │   │   ├── layout.tsx             # Root localized layout with Indic font injection
│   │   │   ├── page.tsx               # Localized landing page
│   │   │   ├── (auth)/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── opportunities/
│   │   │   │   ├── passport/
│   │   │   │   ├── resumes/
│   │   │   │   └── approvals/
│   │   │   └── not-found.tsx
│   ├── i18n/
│   │   ├── routing.ts                 # Locale prefixes & path configuration
│   │   ├── request.ts                 # Server-side request configuration
│   │   ├── navigation.ts              # Localized Link, useRouter, usePathname
│   │   └── formatters.ts              # Indian Lakhs/Crores, dates, currencies
```

### 3.1 Message Namespaces & Key Conventions

Each message JSON file contains the following primary top-level namespaces:

- `common`: Global actions (`save`, `cancel`, `loading`, `back`, `confirm`, `retry`).
- `navigation`: Sidebar and bottom bar labels (`dashboard`, `opportunities`, `passport`, `resumes`, `approvals`, `interviews`, `settings`).
- `auth`: Login, registration, OTP verification, onboarding prompts.
- `opportunities`: Opportunity feed filters, card attributes, match score labels, deadline warnings.
- `eligibility`: Deterministic eligibility checks, CGPA match, skill match, gap explanations.
- `passport`: Career passport section headers, verification badges, achievement forms.
- `resume`: Resume studio tools, bullet point generator, ATS score gauge, PDF download.
- `approvals`: Human-in-the-loop modal, dry-run inspection, diff explanation, consent checkbox.
- `voice`: Voice Orb status pills (`listening`, `processing`, `playing`, `interrupted`, `retry_mic`).
- `errors`: RFC 7807 problem translations, network error fallback messages.

---

## 4. Typography & Indic Font Loading Strategy

Indic scripts have unique typographic characteristics: taller vertical ascenders and descenders (vowel matras/diacritics), complex conjunct ligatures, and distinct baseline alignments. Incorrect font fallbacks cause glyph clipping ("tofu" boxes $\square$) or illegible rendering.

### 4.1 Font Configuration via `next/font/google`

Opportunity OS configures dedicated Google Fonts with font display swapping and preload optimizations:

```typescript
// apps/web/src/app/fonts.ts
import { 
  Inter, 
  Noto_Sans_Devanagari, 
  Noto_Sans_Telugu, 
  Noto_Sans_Tamil, 
  Noto_Sans_Kannada, 
  Noto_Sans_Malayalam, 
  Noto_Sans_Bengali 
} from 'next/font/google';

export const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ['devanagari'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-devanagari',
});

export const notoTelugu = Noto_Sans_Telugu({
  subsets: ['telugu'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-telugu',
});

export const notoTamil = Noto_Sans_Tamil({
  subsets: ['tamil'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-tamil',
});

export const notoKannada = Noto_Sans_Kannada({
  subsets: ['kannada'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-kannada',
});

export const notoMalayalam = Noto_Sans_Malayalam({
  subsets: ['malayalam'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-malayalam',
});

export const notoBengali = Noto_Sans_Bengali({
  subsets: ['bengali'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-noto-bengali',
});
```

### 4.2 Dynamic Script Font Class Mapping

In `apps/web/src/app/[locale]/layout.tsx`, the root HTML element is tagged with the corresponding font class and language attribute:

```typescript
export function getFontFamilyForLocale(locale: string): string {
  switch (locale) {
    case 'hi': return `${notoDevanagari.variable} font-devanagari`;
    case 'te': return `${notoTelugu.variable} font-telugu`;
    case 'ta': return `${notoTamil.variable} font-tamil`;
    case 'kn': return `${notoKannada.variable} font-kannada`;
    case 'ml': return `${notoMalayalam.variable} font-malayalam`;
    case 'bn': return `${notoBengali.variable} font-bengali`;
    default:   return `${inter.variable} font-sans`;
  }
}
```

---

## 5. Layout & UI Adaptations for Indic Scripts

### 5.1 Text Expansion Rules
Indic translations typically require **20% to 35% more horizontal width** than equivalent English strings:
- *English:* "Apply Now" (9 characters)
- *Hindi:* "अभी आवेदन करें" (16 characters)
- *Telugu:* "ఇప్పుడే దరఖాస్తు చేసుకోండి" (27 characters)

**Layout Invariants:**
1. **No Fixed Width Buttons:** Buttons must use `px-4 py-2 w-auto min-w-[120px]` rather than hardcoded widths like `w-28`.
2. **Flexible Cards:** Cards in the opportunity grid use auto-flow wrapping and flexbox `min-h-[...]` rather than rigid fixed height containers.
3. **Ellipsis Safeguards:** Truncation (`truncate` / `line-clamp-2`) must always include an accessible tooltip (`title={fullText}`) so students reading in regional scripts can read full sentences.

### 5.2 Line Height & Diacritic Preservation
Indic scripts feature complex top and bottom matras (e.g., Telugu ఒ/ఓ/ౌ, Hindi ि/ी/ु). Standard English line heights (`leading-none` or `leading-tight`) will clip these characters.
- **Rule:** For non-English locales, default body line-height must be at least `leading-relaxed` (1.625) or `leading-loose` (2.0).

---

## 6. Indian Numbering, Currency & Date Formatting

Opportunity OS displays financial stipends and salaries using the **Indian Numbering System (Lakhs & Crores)** rather than Western Millions/Billions.

```typescript
// apps/web/src/i18n/formatters.ts

/**
 * Formats monetary amounts in Indian Rupees (₹) with Lakh/Crore grouping.
 * Example: 150000 -> "₹1,50,000" | 1200000 -> "₹12,00,000"
 */
export function formatIndianCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Formats stipend ranges for opportunity cards.
 * Example: formatStipendRange(25000, 35000, 'te') -> "నెలకు ₹25,000 - ₹35,000"
 */
export function formatStipendRange(
  min: number, 
  max: number, 
  locale: string, 
  perMonthText: string
): string {
  const minStr = formatIndianCurrency(min);
  const maxStr = formatIndianCurrency(max);
  return `${minStr} - ${maxStr} ${perMonthText}`;
}

/**
 * Formats dates according to Indian academic standard (DD/MM/YYYY or DD MMM YYYY).
 */
export function formatIndianDate(date: string | Date, locale: string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale === 'en' ? 'en-IN' : locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(d);
}
```

---

## 7. Synchronization Between UI Language and Voice Session

When a student selects a language from the UI header language switcher:

1. **URL Navigation:** Next.js navigates to the localized route: `/[locale]/opportunities`.
2. **Zustand Voice Sync:** `useVoiceOrbStore.getState().setLanguage(locale)` updates the default speech recognition and synthesis target.
3. **Session Persistence:** The selected locale is saved to the student's profile via `PATCH /api/v1/students/me` and persisted locally in `localStorage.setItem('preferred_locale', locale)`.
4. **WebSocket Voice Handshake:** The next voice session automatically initializes with `session_init { language: locale }`, ensuring seamless alignment between what the student reads on screen and what the AI agent speaks into their headphones.

---

## 8. Translation Fallback & Zero-Missing-Key Strategy

To ensure stability during rapid hackathon feature updates:
- **Fallback Chain:** If a specific translation key is missing in a regional JSON file (e.g., `kn.json`), `next-intl` automatically falls back to the canonical English string in `en.json`.
- **CI Key Audit:** A build-time script (`scripts/audit-i18n.ts`) compares all regional message files against `en.json` and flags missing keys as warnings or errors before deployment.
- **Code-Switching Support:** Technical keywords like *"Python"*, *"Docker"*, *"Git"*, *"AWS"*, *"CGPA"*, and *"ATS"* are preserved in Latin script across all regional JSON files to mirror natural student conversation in Indian universities.
