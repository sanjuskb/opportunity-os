# ADR-006: Hybrid 3D Hero Architecture — Neural Transit Atlas + Architectural Maquette (R3F + Selective Spline)

**Status:** Accepted  
**Date:** 2026-11-23  
**Deciders:** Sanju (Frontend & ML Architecture), Ramaraju (Backend & Systems), Opportunity OS Team  
**Consulted:** Creative Direction (Concept 4 + Concept 1), Homingo Hackathon Architecture Guidelines  
**Informed:** Repository Contributors, CI/CD Pipeline

---

## 1. Context and Problem Statement

The landing-page hero of Opportunity OS must immediately communicate that the product is a connected, autonomous collegiate career intelligence ecosystem connecting students, companies, universities, and opportunities—not merely another generic AI chatbot or traditional job portal.

Initial explorations evaluated embedding full pre-built Spline scenes (`3D City - Navigation`, `Reactive Orb`, `GENKUB Greeting Robot`, `Voice Interaction Animation`) directly in the hero. However:
1. Embedding a large multi-megabyte monolithic Spline scene in the hero limits programmatic control over dynamic camera paths, instanced agent shuttles, and accessible DOM overlays.
2. Running multiple heavy Spline runtime instances simultaneously on a single page exhausts mobile GPU memory and triggers WebGL context loss.
3. The hero requires a unified, restrained, architectural visual language rather than mixed visual styles from disconnected 3D templates.

How do we achieve an elevated, interactive 3D hero that runs smoothly across desktop and mobile while preserving accessible UI overlays, fast initial load times, and clean engineering boundaries?

---

## 2. Decision: Neural Transit Atlas + Architectural Maquette Hybrid Architecture

We officially adopt **Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)** powered by a **hybrid React Three Fiber (R3F) + selectively lazy-loaded Spline architecture**.

### 2.1 Core Architectural Principles

1. **Custom R3F Ecosystem Campus for the Hero:**
   - The primary interactive hero is implemented with **Three.js, React Three Fiber (`@react-three/fiber`), and Drei (`@react-three/drei`)**.
   - Features four distinct perimeter hubs arranged around a central AI intelligence core:
     - **Student Hub:** Cyan (`#06B6D4`)
     - **Company Hub:** Sapphire / Indigo (`#4F46E5` / `#3B82F6`)
     - **University Hub:** Emerald (`#10B981`)
     - **Opportunity Hub:** Amber (`#F59E0B`)
     - **Central AI Core:** Violet / Indigo (`#8B5CF6` / `#6366F1`)
   - Recessed optical pathways connect peripheral hubs to the central core.
   - Small geometric agent shuttles travel along pathways via lightweight instanced meshes.
   - Material palette: Dark anodised obsidian baseplate, satin titanium, dark slate architectural structures, subtle frosted glass, and controlled emissive glows.

2. **React DOM Overlay Layer (CampusHUD & HubCards):**
   - Readable text, metrics, and actionable controls are rendered exclusively in React / Tailwind DOM overlays.
   - Important product information is never baked into 3D textures.
   - Full keyboard navigation and screen-reader accessibility are preserved.

3. **Selective Lower-Page Spline Showcase (Isolated Lifecycle):**
   - **Reactive Orb:** Serves as visual inspiration for the R3F central AI core geometry and shaders.
   - **GENKUB Greeting Robot:** Dedicated to an autonomous AI Agent Workforce section lower on the landing page, loaded lazily only when scrolled into view.
   - **Voice Interaction Animation:** Dedicated to a Voice AI section lower on the landing page, linked to the voice state machine when active.
   - **Strict Restriction:** The hero contains NO monolithic Spline scenes. The three Spline scenes are never active simultaneously.

4. **Strict One-Active-WebGL-Context Policy:**
   - Visibility-aware mounting and unmounting using `IntersectionObserver`.
   - Complete disposal of Three.js geometry, materials, textures, and requestAnimationFrame loops when sections leave the viewport or switch modes.
   - Instant static image / CSS fallbacks for mobile, low-GPU devices, and users with `prefers-reduced-motion`.

---

## 3. Considered Alternatives

### Alternative A: Monolithic Spline Scene for Hero (`3D City - Navigation`)
- *Pros:* Quick visual prototype; interactive out of the box in Spline Viewer.
- *Cons:* Heavy download (~3.2 MB), rigid camera controls, difficult to bind to real-time React application state, lacks semantic DOM accessibility, limited instancing for autonomous agent shuttles.
- *Verdict:* Rejected as primary hero engine.

### Alternative B: Plain CSS / 2D Canvas Mockup
- *Pros:* Extremely lightweight (~50 KB), zero WebGL complexity.
- *Cons:* Lacks the spatial depth, interactive immersion, and technical sophistication expected of an autonomous intelligence operating system; does not meet hackathon product vision.
- *Verdict:* Rejected as primary experience (retained as static fallback).

### Alternative C: Hybrid R3F Maquette + Selective Spline (Adopted)
- *Pros:* Full programmatic control in React, minimal initial bundle, instanced geometry, DOM accessibility overlays, reliable WebGL lifecycle management, and seamless progressive enhancement.
- *Cons:* Requires engineering modular Three.js components and shaders rather than dropping in a pre-made file.
- *Verdict:* Accepted.

---

## 4. Consequences and Implementation Guardrails

### 4.1 Positive Consequences
- **Instant Usability:** Page renders hero copy, CTAs, and static fallback within milliseconds without waiting for heavy 3D assets.
- **Accessible by Design:** Screen readers and keyboard users interact with native HTML DOM buttons and role switchers.
- **GPU Safety:** No WebGL context crashes or mobile overheating caused by multiple competing render loops.
- **Modular Maintainability:** The 3D campus is composed of modular React components (`StudentHub`, `CompanyHub`, `UniversityHub`, `OpportunityHub`, `AIIntelligenceCore`, `OpticalPathways`, `AgentShuttles`).

### 4.2 Trade-offs and Risks
- **Asset Greybox Phase:** High-fidelity custom GLB models must be progressively introduced; initial sprint uses clean procedural architectural greybox geometry.
- **Bundle Management:** `@react-three/fiber` and `three` must be dynamically imported with `next/dynamic` (`ssr: false`) to avoid server-side window errors and unnecessary main-thread hydration overhead.

### 4.3 Implementation Strategy
- **Sprint 1 (Now):** Foundation, responsive navigation, hero layout (38% left column), accessible role switcher, procedural R3F campus greybox, and instant static fallback.
- **Sprint 2:** Interactive hub selection, camera tweening, and CampusHUD overlay card state.
- **Sprint 3:** Shaders, agent shuttles, and performance optimization.
- **Sprint 4:** Dedicated Spline sections (GENKUB robot, Voice interaction) with visibility-aware lifecycle management.
