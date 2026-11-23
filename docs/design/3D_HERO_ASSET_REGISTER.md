# Opportunity OS — 3D Hero Asset Register & Integration Specification

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** 3D Interactive Hero Experience  
**Creative Concept:** *Autonomous Intelligence Campus*  
**Lead Architect:** Sanju (Frontend & ML Lead)  
**Facilitator:** Antigravity (Architecture QA)  
**Target File:** `apps/web/src/components/hero/`  

---

## 1. Executive Vision: The Autonomous Intelligence Campus

Opportunity OS does not use generic AI floating orbs, abstract neural nets, or static stock photography. The landing page hero immediately establishes Opportunity OS as an **active, interconnected collegiate intelligence ecosystem** through a futuristic miniature 3D campus viewed from an elevated isometric perspective.

The scene communicates the complete student journey:
- Opportunities entering the ecosystem from hiring partners.
- Students building verified profiles and tailored resumes.
- Universities providing academic verification.
- Autonomous AI agents traversing glowing data pathways between hubs to coordinate workflows with student oversight.

---

## 2. Selected Core 3D Spline Assets Register

Three core Spline scenes have been evaluated, tested, and selected for the hero ecosystem. Their actual payloads, URLs, and runtime characteristics have been verified:

| Asset Name | Canonical Spline Public URL | Measured Binary Size | Primary Role in Ecosystem | Runtime Engine |
| :--- | :--- | :--- | :--- | :--- |
| **1. Reactive Orb** | [`https://my.spline.design/reactiveorb-31uF91A8LeiteJwH3rGM0FnS/`](https://my.spline.design/reactiveorb-31uF91A8LeiteJwH3rGM0FnS/) | **$64.25\text{ KB}$** ($64,256\text{ bytes}$) | **Central AI Intelligence Core:** The visual and functional heart of the campus. Pulses and rotates in midnight navy and cyan, representing central coordination. | `@splinetool/runtime` |
| **2. GENKUB Greeting Robot** | [`https://my.spline.design/genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ/`](https://my.spline.design/genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ/) | **$311.78\text{ KB}$** ($311,777\text{ bytes}$) | **Robotic AI Agents:** Autonomous agents distributed across campus hubs performing opportunity discovery, ATS evaluation, and application dispatch. | `@splinetool/runtime` |
| **3. Voice Interaction Animation** | [`https://my.spline.design/voiceinteractionanimation-8xd1x8xvuyG6GyDTrJaqari3/`](https://my.spline.design/voiceinteractionanimation-8xd1x8xvuyG6GyDTrJaqari3/) | **$1.39\text{ MB}$** ($1,453,070\text{ bytes}$) | **Voice Interaction Visualization:** Harmonic acoustic wave shader linked directly to the frontend's 14-state voice lifecycle. | `@splinetool/runtime` |

### 2.1 Total Verified Payload
The combined raw binary footprint of all three core assets is **$1.77\text{ MB}$**, well below the strict $5.0\text{ MB}$ performance budget for WebGL assets.

---

## 3. Four Connected Ecosystem Buildings

Surrounding the central AI intelligence core are four visually distinct architectural hubs representing the four pillars of the Opportunity OS ecosystem.

```
                      +-----------------------------+
                      |       OPPORTUNITIES HUB     |
                      | (Jobs, Internships, Grants) |
                      +-----------------------------+
                                     ^
                                     | Glowing Pathway
                                     v
+-----------------------+     +---------------+     +-----------------------+
|      STUDENT HUB      | <-> | CENTRAL AI    | <-> |      COMPANY HUB      |
| (Passports & Resumes) |     |  CORE (Orb)   |     | (Recruiters & Quotas) |
+-----------------------+     +---------------+     +-----------------------+
                                     ^
                                     | Glowing Pathway
                                     v
                      +-----------------------------+
                      |       UNIVERSITY HUB        |
                      |  (Academics & Verification) |
                      +-----------------------------+
```

### 3.1 Architectural Hub Specifications

| Hub Name | Visual Identity & Form Factor | Key Aesthetic Accents | Functional Significance | Identified Spline Template / Asset |
| :--- | :--- | :--- | :--- | :--- |
| **1. Student Hub** | Modern modular campus academy with open terrace and residential glass wing | Soft emerald / cyan emissive accents (`#10B981` / `#06B6D4`) | Houses student profiles, Career Passports, project portfolios, and personal career goals. | Zoned Campus Block from *3D City - Navigation* (`@aximoris`) / *Isometric Campus Academy* |
| **2. Company Hub** | Sleek geometric corporate high-rise / enterprise glass tower | Cool cobalt and sapphire lighting (`#3B82F6` / `#1D4ED8`) | Represents hiring partners, live corporate job postings, recruiter telemetry, and hiring pipelines. | Enterprise Glass Skyscraper from *Mini City* / *Isometric Tech Tower* |
| **3. University Hub** | Traditional neo-academic domed rotunda or tiered library with digital observatory spire | Warm amber and gold holographic trim (`#F59E0B`) | Represents colleges, universities, AICTE/UGC credentials, degree verification, and faculty advisors. | Institutional Observatory Rotunda from *Spline Architecture Kit* |
| **4. Opportunities Hub** | Dynamic hexagonal pavilion with open transit portals and radar arrays | Electric violet and magenta glow (`#8B5CF6` / `#D946EF`) | Represents the opportunity ingestion stream: internships, scholarships, fellowships, and hackathons. | Orbital Transit Terminal / Ingestion Pavilion |

---

## 4. Glowing Information Pathways & Energy Particles

The information pathways physically and visually connect all four peripheral hubs to the central AI Core:

1. **Geometry:** Curved spline ribbon tubes connecting the perimeter hubs to the central plaza ground plane.
2. **Material:** Transparent dielectric glass with a cyan emissive core material (`#06B6D4`, bloom intensity $1.8$).
3. **Particle Simulation:** Small glowing light pulses traveling along the spline curves toward the central core:
   - When new opportunities are ingested: Particles pulse from the **Opportunities Hub** $\rightarrow$ **Central Core**.
   - When a student requests eligibility matching: Particles flow from **Student Hub** $\rightarrow$ **Central Core** $\rightarrow$ **Company Hub**.
   - When an application is approved: Particles flow from **Central Core** $\rightarrow$ **Company Hub**.

---

## 5. Floating Holographic Product Interface Cards

To ground the 3D scene in real utility, floating holographic product interfaces hover above or adjacent to the hubs.

Rather than baking fixed textures into 3D geometry (which prevents localization and responsive rendering), these elements are implemented as **React DOM Overlays with 3D CSS Perspective Transforms** (`transform: perspective(1000px) rotateX(15deg) rotateY(-20deg)`):

1. **Live Opportunity Match Card (Hovering near Opportunities Hub):** Displays real-time opportunity title, stipend (₹ 35,000/mo), and a 94% eligibility match pill.
2. **Career Passport Verification Badge (Hovering near Student Hub):** Displays verified student badges (*"AWS Certified"*, *"React 19"*, *"B.Tech CSE 2026"*).
3. **Approval Required Alert (Hovering near Central Core):** Interactive human-in-the-loop modal trigger (*"Application ready for your approval"*).
4. **Voice Orb Telemetry Badge:** Real-time audio waveform and detected language indicator (*"తెలుగు / English Code-Switch Active"*).

---

## 6. Integration Architecture & Multi-Scene Compositing Strategy

### 6.1 Can the 3 Selected Scenes Be Merged into One?

Our investigation revealed that the three selected Spline URLs are standalone exported bundles (`app.start([binaryArray])`).

- **Limitation of Direct Multi-Canvas Embedding:** Rendering three separate `<spline-viewer>` or `@splinetool/react-spline` instances on a single webpage initializes **three independent WebGL contexts**. On mobile browsers and integrated GPUs, multiple WebGL contexts cause severe frame rate drops ($< 25\text{ FPS}$) and trigger browser WebGL context loss errors.

### 6.2 The Dual-Path Recommended Strategy

```
+--------------------------------------------------------------------------+
| PATHWAY A (Ideal Production Asset): SPLINE EDITOR UNIFIED REMIX          |
| 1. Sanju opens Spline Editor (Web or Desktop app).                       |
| 2. Imports the Reactive Orb as the central object at (0, 0, 0).          |
| 3. Imports the 4 Hub building meshes around the perimeter.               |
| 4. Imports GENKUB robot instances positioned on pathways.                |
| 5. Adds spline curve energy pathways with glow materials.                |
| 6. Exports ONE single unified .splinecode scene.                         |
| Result: Exactly 1 WebGL context, maximum 60 FPS, unified camera physics. |
+--------------------------------------------------------------------------+
                                    OR
+--------------------------------------------------------------------------+
| PATHWAY B (Immediate Decoupled Integration): COMPOSITED DOM TOPOLOGY     |
| 1. Hero Canvas: Houses the Central Campus / Reactive Orb (Canvas 1).     |
| 2. Floating AI Assistant Widget: GENKUB robot embedded in a compact      |
|    interactive copilot card on the right hero column.                    |
| 3. Voice Orb: The Voice Interaction Animation is mounted directly inside |
|    the Voice Orb component (apps/web/src/components/voice/VoiceOrb.tsx), |
|    activating ONLY when the student opens voice mode.                    |
| Result: Zero GPU contention; voice canvas is lazy-loaded on demand.      |
+--------------------------------------------------------------------------+
```

---

## 7. Licensing, Commercial Use & Plan Watermark Verification

### 7.1 Spline Community License Terms
- All scenes published to the Spline Community are shared under the **Spline Standard Commercial License** / Creative Commons framework.
- **Permitted:** Personal use, commercial use, modification, remixing, and web integration.
- **Requirement:** Attribution to original designers where applicable.

### 7.2 Plan Watermark Constraint (Free vs Paid Tier)
- **Free Spline Plan:** All web exports generated on the free tier include a small Spline watermark badge in the bottom-right corner.
- **Paid Spline Plan (Super / Pro):** Unlocks watermark-free exports and custom domain white-labeling.
- **Architectural Mitigation:** In CSS, the canvas container wraps the embed in an `overflow-hidden` boundary with padding, or the team upgrades to a single monthly Spline Pro seat for clean production export during the hackathon evaluation.

---

## 8. Final Status and Next Actions

- **Current Status:** **CONDITIONALLY APPROVED** (Assets selected, measured, and verified; awaiting Sanju's confirmation of Pathway A vs Pathway B before final scene assembly).
- **No Production Code Changes:** In accordance with instructions, zero 3D production code has been committed to `main` or `develop`.
