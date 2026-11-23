# Opportunity OS — 3D Asset Register & Licensing Verification

**Document ID:** `DOC-ARCH-3D-003`  
**Revision:** `2.0.0` (Adopted ADR-006 Direction)  
**Status:** Verified & Updated  
**Creative Direction:** Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)  
**Subsystems:** React Three Fiber Hero + Downstream Spline Showcases

---

## 1. Asset Register & Role Mapping

| Asset Identifier | Asset Name & Source | Technology / Format | Assigned Ecosystem Role | Licensing & Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **HERO-R3F-CORE** | Architectural Maquette & Neural Transit Atlas | Three.js / React Three Fiber / Drei | **Landing Page Hero Campus:** 4 peripheral hubs, central AI core, recessed optical pathways, agent shuttles. | **Internal Code (Apache 2.0).** Fully owned and authored. |
| **SPLINE-REF-01** | Reactive Orb (`reactiveorb-31uF91A8LeiteJwH3rGM0FnS`) | Spline Public URL | **Visual Reference:** Visual inspiration for procedural R3F central AI core pulse and materials. | **Public Reference.** Not directly redistributed or bundled. |
| **SPLINE-SEC-02** | GENKUB Greeting Robot (`genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ`) | Spline Cloud Export | **AI Agent Workforce Section:** Downstream lazy-loaded demonstration of autonomous execution. | **Community Asset.** Commercial use and remix permissions to be verified prior to production distribution. |
| **SPLINE-SEC-03** | Voice Interaction Animation (`voiceinteractionanimation-8xd1x8xvuyG6GyDTrJaqari3`) | Spline Cloud Export | **Voice AI Section:** Downstream lazy-loaded demonstration of real-time multilingual voice feedback. | **Community Asset.** Commercial use and remix permissions to be verified prior to production distribution. |

---

## 2. Licensing Guardrails
1. **Zero Unverified Claims:** Assets sourced from Spline Community are treated as references or prototypes until explicit creator licensing (e.g., CC BY 4.0 or custom commercial license) is documented and confirmed.
2. **No Proprietary Font/Texture Redistribution:** All textures and geometry for the primary hero campus are authored internally via Three.js procedural shaders and open-source geometries, eliminating legal third-party licensing dependencies for the primary hero experience.
3. **Downstream Isolation:** Because the Spline assets are segregated to mid-page and lower-page showcase sections, the primary product hero is 100% license-safe and independent.
