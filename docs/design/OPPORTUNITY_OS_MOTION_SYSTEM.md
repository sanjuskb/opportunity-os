# Opportunity OS — Motion System & Animation Architecture

**Guiding Principle:** Motion is a first-class product feature that communicates state, direction, and spatial depth. It is never decorative distraction.

---

## 1. Timing, Curves & Motion Tokens

### 1.1 Easing Curves
- **Editorial Decelerate (Natural Entrances):** `cubic-bezier(0.16, 1, 0.3, 1)` (snappy start, luxurious smooth landing).
- **Standard UI Response:** `cubic-bezier(0.4, 0, 0.2, 1)` (standard Material/Next).
- **Tactile Micro-Spring:** `cubic-bezier(0.34, 1.56, 0.64, 1)` (subtle button presses and toggle snaps).

### 1.2 Durations
- **Micro-interactions:** `150ms - 200ms` (hover, active press, focus ring).
- **Component Transitions:** `300ms - 400ms` (tab switches, dropdown reveals, modal entrance).
- **Section Reveals & Sticky Storytelling:** `600ms - 800ms` (chapter headings, card elevation).
- **Route Transitions:** `250ms - 350ms` (opacity fade and 12px vertical drift).

---

## 2. Scroll Choreography & Pinned Chapters

1. **Chapter Pinning:** Pinned scene containers remain fixed for 100vh while scroll track advances.
2. **Text Staggering:** Letter/word stagger with initial `opacity: 0; transform: translateY(20px)`.
3. **Card Presentation:** Showcase cards enter with gentle perspective tilt (`rotateX(4deg)`) and settle to `rotateX(0deg)`.
4. **Transit Lines:** SVG and WebGL pathway conduits ignite sequentially as chapters come into view.

---

## 3. Accessibility & Reduced Motion

- `@media (prefers-reduced-motion: reduce)`:
  - All large 3D rotations, sticky perspective transforms, and floating particle motes are replaced with clean instant opacity states.
  - Three.js camera transitions jump directly to target coordinates.
  - Essential content is never hidden behind un-triggered motion states.
