# Opportunity OS — Master Visual Refinement & 3D Recovery Log

**Repository:** `sanjuskb/opportunity-os`  
**Branch:** `sanju`  
**Execution Timestamp:** 2026-11-24  
**Primary Reference:** `https://homingo.co.in/` (Smooth motion, breathing room, non-congested layout)

---

## 1. Executive Summary & Problems Resolved

| Issue Identified | Root Cause | Permanent Resolution | Verification Status |
| :--- | :--- | :--- | :--- |
| **GENKUB Robot Stuck on Awakening** | Dead/unauthorized Spline slug `WnLawN2hMwCXR1W70N5A2TsZ` caused WebGL embed to never fire load event. | Switched to verified live embed URL `https://my.spline.design/genkubgreetingrobot-EOlN5of6xh4LRe3SwQPBBHXH/`. Added non-blocking skeleton with a 2.8s safety fallback timer. Removed clutter badges. | **VERIFIED:** Robot renders smiling & waving cleanly in WebGL canvas. |
| **Mid-Word Breaking ("continuou" / "sly")** | `SplitTextReveal` split characters directly into individual `inline-block` spans, allowing browser line-breaking mid-word. | Refactored `SplitTextReveal` to tokenize text by words first, wrapping each word in `<span className="inline-block whitespace-nowrap">` before splitting characters internally. | **VERIFIED:** "continuously" is kept completely intact on a single line. |
| **Broken "System." Word at Page Bottom** | "Operating S" / "ystem." broke across lines due to character splitting. | Explicitly formatted `FinalCTASection` heading into two deliberate lines: `"Enter the Connected Operating"` and an italicized bottom line `"System."`. | **VERIFIED:** "System." is positioned whole at the bottom of the sentence. |
| **Scroll Animations Playing Only Once** | `useScrollReveal` called `observer.unobserve(el)` on the first intersection, locking `isRevealed=true` permanently. | Removed `unobserve(el)` and added viewport exit logic to reset `isRevealed=false` when offscreen. Added rapid exit transitions (`0.35s ease-out`) and staggered entrance transitions (`0.75s cubic-bezier(0.16, 1, 0.3, 1)`). | **VERIFIED:** Tested down $\rightarrow$ up $\rightarrow$ down scroll cycle via Playwright; animations replay every time. |
| **Presentation Slide Aesthetic** | Giant background numbers (`02` through `08`, `AI`) and slide labels (`Chapter 02 / The Fragmentation`) gave the app a slide deck feel. | Removed all `BackgroundChapterNo` elements and "Chapter 0X /" slide labels. Introduced `SpatialBackground.tsx` with 6 lightweight SVG/CSS retrofuturist perspective wireframes (`fragmented`, `transit`, `journey`, `pipeline`, `institutional`, `harmonic`). | **VERIFIED:** Clean, spacious, international-grade aesthetic with zero heavy WebGL context leaks. |
| **Navbar Slide Deck Counter** | Navbar showed `06 / 07 — For Universities`, reinforcing the presentation-slide feeling. | Replaced numeric counter with an ambient pulsing cyan indicator and clean section name. | **VERIFIED:** Sleek navigation indicator without slide numbers. |

---

## 2. Component Refactoring Details

### 2.1 `apps/web/src/components/ui/ScrollReveal.tsx`
- **Replayability Engine:**
  ```tsx
  export function useScrollReveal(threshold = 0.1, replay = true) {
    // In view: setIsRevealed(true)
    // Out of view: if (replay) setIsRevealed(false)
  }
  ```
- **Word-Level Tokenization:**
  ```tsx
  const words = text.split(' ');
  return (
    <span>
      {words.map((word, wIdx) => (
        <span key={wIdx} className="inline-block whitespace-nowrap mr-[0.28em]">
          {/* Internal character split */}
        </span>
      ))}
    </span>
  );
  ```

### 2.2 `apps/web/src/components/landing/GenkubRobot.tsx`
- Embed updated to `https://my.spline.design/genkubgreetingrobot-EOlN5of6xh4LRe3SwQPBBHXH/`.
- Non-blocking skeleton loader with 2.8s safety fallback timer.
- Replaced header clutter with discrete interaction footer (`Interactive 3D • Click & drag to orbit`).

### 2.3 `apps/web/src/components/landing/SpatialBackground.tsx`
- New dedicated component implementing 6 architectural wireframe perspectives.
- Pure SVG + CSS animations (`stroke-dasharray`, subtle perspective gradients).
- Zero GPU memory overhead and zero interference with main-thread scroll performance.

### 2.4 Sections Modernized
- **`HeroCopy.tsx`:** Removed slide indicators; activated replaying split text.
- **`ProblemSection.tsx`:** Swapped number for `SpatialBackground variant="fragmented"`.
- **`UnifiedPlatformSection.tsx`:** Swapped number for `SpatialBackground variant="transit"`.
- **`StudentSection.tsx`:** Swapped number for `SpatialBackground variant="journey"`.
- **`CompanySection.tsx`:** Swapped number for `SpatialBackground variant="pipeline"`.
- **`UniversitySection.tsx`:** Swapped number for `SpatialBackground variant="institutional"`.
- **`AgentWorkforceSection.tsx`:** Removed "AI" number, embedded working GENKUB robot, and structured unbroken headline.
- **`VoiceAISection.tsx`:** Swapped number for `SpatialBackground variant="harmonic"`.
- **`FinalCTASection.tsx`:** Structured headline with whole "System." on bottom line; removed "08" background number.

---

## 3. Automated Verification & QA Results

1. **Type Safety & Build:**
   - `pnpm -r run type-check`: 0 errors across all 6 workspace packages.
   - `pnpm --filter @opportunity-os/web test`: 8/8 unit tests passing.
   - `pnpm --filter @opportunity-os/web build`: 30 static & dynamic routes compiled cleanly.
2. **Browser Execution & Visual Evidence (Playwright):**
   - Verified GENKUB 3D canvas loads and displays the active robot model.
   - Verified Agent Workforce headline displays unbroken "continuously working for you."
   - Verified Final CTA displays `"Enter the Connected Operating"` with `"System."` intact at the bottom.
   - Verified scroll replay test:
     - `down1_revealed`: `[true, true]`
     - `top_hidden`: `[false, false]`
     - `down2_replayed`: `[true, true]`
