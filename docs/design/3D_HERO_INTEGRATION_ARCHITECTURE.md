# Opportunity OS — 3D Hero Integration Architecture (R3F + Selective Spline Hybrid)

**Document ID:** `DOC-ARCH-3D-001`  
**Revision:** `2.0.0` (Adopted ADR-006 Direction)  
**Status:** Approved & Locked  
**Concept:** Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)  
**Engine:** React Three Fiber (R3F) Core Campus + Selective Spline Sections

---

## 1. Architectural Philosophy: The Neural Transit Maquette

Opportunity OS adopts a **hybrid 3D architecture** pairing a lightweight, custom React Three Fiber interactive hero campus with selectively loaded Spline scenes for dedicated downstream landing page sections.

```
+-----------------------------------------------------------------------------------------+
|                                    LANDING PAGE ARCHITECTURE                            |
|                                                                                         |
|  [ Section 1: Hero (Top of Page) ]                                                      |
|  +-----------------------------------------------------------------------------------+  |
|  | Left 38%: Accessible DOM Overlay (Headline, Multilingual Pills, Role Switcher)   |  |
|  | Right 62%: Interactive Ecosystem Campus (React Three Fiber / Three.js / Drei)     |  |
|  |   - 4 Ecosystem Hubs: Students (Cyan), Companies (Sapphire),                       |  |
|  |                       Universities (Emerald), Opportunities (Amber)              |  |
|  |   - Central AI Intelligence Core (Violet/Indigo, Reactive Orb inspired)          |  |
|  |   - Recessed Optical Pathways & Autonomous Agent Shuttles (Instanced Meshes)     |  |
|  |   - Instant Static Greybox Fallback (< 80 KB) for Reduced-Motion & Mobile         |  |
|  +-----------------------------------------------------------------------------------+  |
|                                                                                         |
|  [ Section 2: AI Agent Workforce (Mid Page) ]                                           |
|  +-----------------------------------------------------------------------------------+  |
|  | - Autonomous Agent Orchestration Showcase                                         |  |
|  | - Dedicated GENKUB Greeting Robot Spline Scene (Lazy-loaded via Observer)         |  |
|  +-----------------------------------------------------------------------------------+  |
|                                                                                         |
|  [ Section 3: Multilingual Voice AI (Lower Page) ]                                      |
|  +-----------------------------------------------------------------------------------+  |
|  | - Real-time Multilingual Audio Interaction (7 Indian Languages)                    |  |
|  | - Dedicated Voice Interaction Spline Scene (Lazy-loaded, connected to Audio/WS)   |  |
|  +-----------------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Component Hierarchy & File Structure

```text
apps/web/src/components/
├── landing/
│   ├── navigation/
│   │   └── LandingNavbar.tsx            # Responsive glass navigation with language selector
│   ├── hero/
│   │   ├── HeroSection.tsx              # Main orchestrator (Left 38% Copy + Right Campus)
│   │   ├── HeroCopy.tsx                 # Headline, value prop, badges, regional pills
│   │   ├── HeroActions.tsx              # Primary CTA & voice exploration buttons
│   │   ├── RoleSwitcher.tsx             # Accessible role toggle (Student, Recruiter, University)
│   │   ├── EcosystemCampus.tsx          # Dynamic R3F Canvas container with fallback
│   │   ├── CampusFallback.tsx           # High-DPI zero-JS static canvas fallback
│   │   └── CampusHUD.tsx                # Accessible React/Tailwind hub information overlay
│   ├── ecosystem/
│   │   ├── EcosystemScene.tsx           # R3F scene graph, lighting, camera controls
│   │   ├── StudentHub.tsx               # Cyan architectural hub geometry & glow
│   │   ├── CompanyHub.tsx               # Sapphire/indigo corporate high-rise
│   │   ├── UniversityHub.tsx            # Emerald academic rotunda
│   │   ├── OpportunityHub.tsx           # Amber transit portal
│   │   ├── AIIntelligenceCore.tsx       # Violet/indigo pulsing central core
│   │   ├── OpticalPathways.tsx          # Recessed illuminated channels between hubs
│   │   └── AgentShuttles.tsx            # Instanced geometric shuttles traversing pathways
│   └── sections/
│       ├── AgentWorkforceSection.tsx    # Downstream section hosting GENKUB Robot
│       └── VoiceAISection.tsx           # Downstream section hosting Voice Spline
├── 3d/
│   ├── lifecycle/
│   │   └── SceneLifecycleProvider.tsx   # Strict 1-active-context WebGL manager
│   ├── hooks/
│   │   ├── useSceneLifecycle.ts         # Viewport intersection & WebGL context monitor
│   │   └── useReducedMotion.ts          # Media query hook for accessibility
│   └── lib/
│       ├── performance.ts               # Device pixel ratio clamping & tier detection
│       └── scene-config.ts              # Lighting, palette, and camera waypoints
```

---

## 3. Strict WebGL Context & Lifecycle Management

To prevent mobile crashes and GPU throttling:
1. **One-Active-Context Rule:** Only one heavy 3D WebGL context is mounted and active at any given time.
2. **IntersectionObserver Activation:** Downstream Spline scenes (`GENKUB`, `Voice Interaction`) remain unmounted until scrolled within 200px of the viewport.
3. **Explicit Teardown:** When a 3D component unmounts, Three.js geometries, materials, and textures are explicitly disposed of (`geometry.dispose()`, `material.dispose()`), and animation frames are cancelled.
4. **Context Loss Recovery:** WebGL canvas listens for `webglcontextlost` and `webglcontextrestored` to gracefully fall back to `CampusFallback`.

---

## 4. Ecosystem Palette & Architectural Materials

| Element | Hex Code | Material Direction | Visual Significance |
| :--- | :--- | :--- | :--- |
| **Students** | `#06B6D4` | Satin titanium + Cyan emissive trim | Student profiles, Career Passports, resume intelligence |
| **Companies** | `#3B82F6` | Dark slate + Sapphire enterprise glass | Hiring partners, verified job listings, recruiter pipeline |
| **Universities** | `#10B981` | Slate structure + Emerald holographic ring | Academic verification, UGC/AICTE degree credentials |
| **Opportunities** | `#F59E0B` | Obsidian faceted pavilion + Amber portal | Live internships, fellowships, hackathons, and grants |
| **Central AI Core** | `#8B5CF6` | Dark obsidian sphere + Violet/Indigo pulse | Central coordination, agent matching, orchestrator |
| **Baseplate** | `#0B0F19` | Dark anodised obsidian | Monolithic base maquette with recessed channels |
| **Optical Channels** | `#020617` / `#38BDF8` | Recessed groove with glowing cyan spline | Data transit conduits between hubs and core |
