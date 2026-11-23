# Opportunity OS — Frontend 3D Hero Integration Architecture

## 1. Architectural Philosophy: The Hybrid Canvas-DOM Pattern

To ensure high performance, cinematic immersion, and uncompromised accessibility, we employ the **Hybrid Canvas-DOM Pattern**:
- **Background Layer (WebGL Canvas):** Hosts the interactive 3D miniature campus (`3D City - Navigation`), rendering camera parallax, illuminated pathways, and building reflections.
- **Foreground Layer (Accessible HTML / React DOM):** Hosts the primary H1 headline, multilingual voice trigger CTA, and floating glassmorphism product badges (`Career Passport`, `ATS Score: 94%`, `Eligibility: Verified`).

This guarantees that:
1. Search engine crawlers (SEO) read pure semantic HTML.
2. Screen readers navigate clean accessible headers and buttons without WebGL occlusion.
3. The 3D scene loads asynchronously without delaying First Contentful Paint (FCP).

---

## 2. Proposed Component Directory Structure

Adapting to our Next.js 15+ App Router architecture, the hero feature is isolated under `apps/web/src/features/landing/`:

```text
apps/web/src/features/landing/
├── components/
│   ├── HeroSection.tsx              # Main Hero Section orchestrator
│   ├── HeroScene.tsx                # Dynamic Client-only WebGL Spline container
│   ├── HeroSceneFallback.tsx        # Zero-JS static WebP + CSS pulse placeholder
│   ├── HeroContent.tsx              # Semantic H1, tagline, and regional language pills
│   ├── HeroFloatingBadges.tsx       # Floating glassmorphism UI cards over the 3D scene
│   └── HeroCTA.tsx                  # Voice Orb trigger & "Explore Opportunities" button
├── config/
│   └── hero-scene.config.ts         # Scene URL, camera defaults, breakpoint overrides
├── hooks/
│   └── useHeroScene.ts              # IntersectionObserver, WebGL check, reduced-motion hook
├── services/
│   └── scene-loader.ts              # Preloading and caching utility for .splinecode
└── types/
    └── hero-scene.types.ts          # State definitions (loading, ready, degraded, error)
```

---

## 3. Evaluation of Technical Integration Paths

| Integration Option | Technical Mechanism | Dependencies | Interaction Fidelity | Bundle / Payload Overhead | Recommendation |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Option A: `@splinetool/react-spline`** | Native React 19 Client Component wrapper | `@splinetool/react-spline`, `@splinetool/runtime` | **100% (Complete)** | `~45 KB` runtime + `.splinecode` | **PRIMARY RECOMMENDATION** |
| **Option B: Vanilla `<spline-viewer>`** | Custom HTML Web Component via script tag | CDN script tag | **100%** | Loads unbundled via CDN | High viability, but less idiomatic in Next.js SSR |
| **Option C: Three.js / R3F (GLTF/GLB)** | Export from Spline to GLTF $\rightarrow$ `@react-three/fiber` | `three`, `@react-three/fiber`, `@react-three/drei` | **40% (Loss of Spline event triggers)** | `~600 KB` Three.js bundle | Rejected (Breaks event graph & camera physics) |
| **Option D: Static WebP + CSS Animation** | Pre-rendered high-res isometric render with CSS glow | Zero dependencies | **Static (No 3D mouse look)** | `< 120 KB` WebP image | **OFFICIAL ACCESSIBILITY FALLBACK** |

---

## 4. Implementation Code Blueprint

### 4.1 Dynamic Scene Wrapper (`HeroScene.tsx`)
```tsx
'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { HeroSceneFallback } from './HeroSceneFallback';
import { useHeroScene } from '../hooks/useHeroScene';
import { HERO_SCENE_CONFIG } from '../config/hero-scene.config';

// Lazy-load Spline without SSR
const Spline = dynamic(() => import('@splinetool/react-spline'), {
  ssr: false,
  loading: () => <HeroSceneFallback />,
});

export function HeroScene() {
  const { isSupported, prefersReducedMotion } = useHeroScene();
  const [isSceneLoaded, setIsSceneLoaded] = useState(false);

  // Instant fallback for low-power devices or reduced motion preference
  if (!isSupported || prefersReducedMotion) {
    return <HeroSceneFallback />;
  }

  return (
    <div className="relative w-full h-[600px] lg:h-[750px] overflow-hidden">
      {!isSceneLoaded && <HeroSceneFallback />}
      <Spline
        scene={HERO_SCENE_CONFIG.sceneUrl}
        onLoad={() => setIsSceneLoaded(true)}
        className={`w-full h-full transition-opacity duration-700 ${
          isSceneLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />
    </div>
  );
}
```

### 4.2 Accessibility & Capabilities Hook (`useHeroScene.ts`)
```typescript
'use client';

import { useState, useEffect } from 'react';

export function useHeroScene() {
  const [isSupported, setIsSupported] = useState(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // 1. Check for reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(motionQuery.matches);

    // 2. Check for WebGL hardware support
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      setIsSupported(Boolean(gl));
    } catch {
      setIsSupported(false);
    }
  }, []);

  return { isSupported, prefersReducedMotion };
}
```

---

## 5. Non-Blocking Loading & Responsive Layout Guardrails

1. **Zero Cumulative Layout Shift (CLS):** The container reserves fixed dimensions (`h-[600px] lg:h-[750px]`) via CSS, preventing layout jank when the 3D canvas finishes hydrating.
2. **Intersection Throttling:** When the visitor scrolls down past the hero into the feature sections, the WebGL render loop is paused via `IntersectionObserver` to save student laptop battery and GPU cycles.
3. **Responsive Breakpoints:**
   - **Desktop ($\ge 1024\text{px}$):** Full interactive 3D canvas positioned behind split-screen content.
   - **Mobile ($< 768\text{px}$):** Canvas is centered with touch-orbit locked to prevent interfering with vertical page scrolling.
