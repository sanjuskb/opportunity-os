# Opportunity OS — 3D Hero Scene Recommendation (Adopted Direction)

**Document ID:** `DOC-ARCH-3D-002`  
**Revision:** `2.0.0` (Adopted ADR-006 Direction)  
**Status:** Approved & Locked  
**Approved Direction:** Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)  
**Implementation Engine:** Custom React Three Fiber (R3F) + Selective Downstream Spline Scenes

---

## 1. Approved Creative Direction

Following extensive evaluation, Opportunity OS officially adopts:

**Concept 4 (Neural Transit Atlas) + Concept 1 (Architectural Maquette)**

Rather than embedding a monolithic, opaque third-party Spline template as the hero, the landing page hero is built as an elevated, procedural architectural maquette using **React Three Fiber**.

### Why This Combination Wins
1. **Communicates System Connectivity:** Four distinct perimeter hubs (Students, Companies, Universities, Opportunities) physically and optically connect to a central AI Intelligence Core.
2. **Restrained Architectural Aesthetic:** Replaces generic neon cyberpunk tropes with dark anodised obsidian, satin titanium, dark slate, subtle glass, and fine metallic accents.
3. **Full React & DOM Integration:** Camera waypoints, hub highlights, and floating cards (`CampusHUD`) are native React components, guaranteeing 100% semantic accessibility and screen-reader compatibility.
4. **Instant Usability:** Fast initial load (< 80 KB static fallback) ensuring the landing page is interactive and responsive within milliseconds on both desktop and mobile.

---

## 2. Role of Selected Spline Assets in the Ecosystem

The three previously researched Spline assets are assigned to dedicated, isolated roles outside the hero:

| Asset Name | Canonical Spline Public URL | Ecosystem Role | Integration Policy |
| :--- | :--- | :--- | :--- |
| **Reactive Orb** | [`https://my.spline.design/reactiveorb-31uF91A8LeiteJwH3rGM0FnS/`](https://my.spline.design/reactiveorb-31uF91A8LeiteJwH3rGM0FnS/) | **Visual Inspiration for AI Core** | Not embedded monolithically. Inspires R3F procedural shader and pulsing geometry. |
| **GENKUB Greeting Robot** | [`https://my.spline.design/genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ/`](https://my.spline.design/genkubgreetingrobot-WnLawN2hMwCXR1W70N5A2TsZ/) | **AI Agent Workforce Section** | Lazy-loaded in dedicated lower section when scrolled into view. |
| **Voice Interaction Animation** | [`https://my.spline.design/voiceinteractionanimation-8xd1x8xvuyG6GyDTrJaqari3/`](https://my.spline.design/voiceinteractionanimation-8xd1x8xvuyG6GyDTrJaqari3/) | **Dedicated Voice AI Section** | Lazy-loaded in lower voice section, linked to Web Audio API / WebSocket telemetry. |

> [!IMPORTANT]
> The three Spline scenes are NEVER mounted simultaneously in the hero. The hero is exclusively powered by the custom R3F Architectural Maquette.

---

## 3. Fallback & Accessibility Strategy
- **Reduced Motion:** If `prefers-reduced-motion: reduce` is active, animations are disabled and a pristine isometric camera is locked.
- **Mobile Devices:** Automatically switches to high-DPI static fallback with interactive 2D hub selector to conserve battery and GPU bandwidth.
