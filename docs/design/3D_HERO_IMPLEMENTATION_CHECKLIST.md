# Opportunity OS — 3D Hero Implementation Readiness Checklist

**Target Asset:** `3D City - Navigation`  
**Creator:** Max Borisov (`@aximoris`)  
**Lead Reviewer:** Sanju (Frontend & UX Lead)  
**Status:** Architecture Ready for Review  

---

## 1. Asset Verification & Legal Due Diligence

- [x] **Best Asset Selected:** `3D City - Navigation` identified as the closest existing match to the *Autonomous Intelligence Campus* concept.
- [x] **Original Creator Verified:** Confirmed creator is Max Borisov (`@aximoris` on Spline Community).
- [x] **Asset Access Verified:** Verified publicly accessible and remixable on Spline Community.
- [x] **Visual Preview Inspected:** Verified elevated isometric camera, midnight navy background, cyan emissive pathway accents, and modular building zones.
- [x] **License Verified:** Creative Commons Attribution 4.0 International (**CC BY 4.0**).
- [x] **Commercial Use Permitted:** Confirmed under CC BY 4.0 terms (commercial use permitted with attribution).
- [x] **Zero Paid Assets:** Verified 100% free; no subscription or purchase required.

---

## 2. Technical Feasibility & Next.js Compatibility

- [x] **Export & Embedding Verified:** Direct `.splinecode` export supported; compatible with `@splinetool/react-spline`.
- [x] **Next.js Integration Path Confirmed:** Dynamic Client Component (`ssr: false`) with hybrid HTML overlay cards.
- [x] **Runtime Dependencies Identified:** `@splinetool/react-spline` (`~45 KB`) and `@splinetool/runtime`.
- [x] **Loading Fallback Designed:** `HeroSceneFallback.tsx` with zero-JS static WebP + CSS ambient pulse animation.
- [x] **Mobile Behavior Planned:** Touch-orbit locked to prevent interference with vertical scrolling; DPR capped at `1.0`.
- [x] **Reduced-Motion Behavior Planned:** Automatically disables camera parallax and locks to neutral isometric angle when `prefers-reduced-motion: reduce` is active.
- [x] **Performance Budget Set:** Polygon ceiling $\le 45,000$ tris; compressed binary $\le 3.5\text{ MB}$; 60 FPS target.

---

## 3. Team Sign-Off & Approval Gates

- [ ] **Scene Selection Approved by Sanju:** Sanju reviews `docs/design/3D_HERO_SCENE_RECOMMENDATION.md` and confirms creative match.
- [ ] **Remix Customizations Confirmed:** Decide whether to apply minor emissive tweaks in Spline Editor or use the scene as-is with HTML badges.
- [ ] **Production Integration Approved:** Approval to install `@splinetool/react-spline` in `apps/web/package.json` and implement `apps/web/src/features/landing/`.
