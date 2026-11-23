# Opportunity OS — Performance Budget & Latency Targets

## 1. Latency & Responsiveness Budget

*Note: Values below represent Proposed Targets vs. Current Baseline Measurements.*

| Operation / Interaction | Proposed Target | Current Measured Result | Status |
| :--- | :---: | :---: | :---: |
| **Voice Round-Trip (Spoken Query $\rightarrow$ Audio Byte)** | $< 650\text{ ms}$ | *Pending Voice Stream Deployment* | Target Set |
| **FastAPI Health Check Response** | $< 25\text{ ms}$ | $14\text{ ms}$ | **PASSED** |
| **Opportunity Feed First Page Load (SSR)** | $< 1.2\text{ s}$ | *Pending DB Connection* | Target Set |
| **pgvector Semantic Search (Top 20 Matches)** | $< 50\text{ ms}$ | *Pending DB Connection* | Target Set |
| **Resume Tailoring Generation** | $< 4.0\text{ s}$ | *Pending LangGraph Deployment* | Target Set |
| **Playwright Dry-Run Form Extraction** | $< 8.0\text{ s}$ | *Pending Worker Deployment* | Target Set |

---

## 2. Asset & Network Payload Budget

| Asset Type | Maximum Budget Size | Strategy |
| :--- | :---: | :--- |
| **Initial JavaScript Bundle (Compressed)** | $< 180\text{ KB}$ | Next.js code splitting, dynamic imports for Three.js |
| **Voice Orb 3D Bundle (Three.js / Shaders)** | $< 250\text{ KB}$ | Lazy loaded only when student activates voice mode |
| **Global CSS (Tailwind)** | $< 35\text{ KB}$ | Purged via Tailwind content scanning |
| **Font Assets** | $< 60\text{ KB}$ | Variable fonts with subsetting for Indic glyphs |
| **Opportunity Image Thumbnails** | $< 40\text{ KB}$ | WebP formatted, lazy-loaded via Next/Image |

---

## 3. Concurrency & Throughput Targets

- **API Throughput:** Baseline support for 100 requests/sec with P99 latency $< 200\text{ms}$.
- **Concurrent Voice Streams:** Up to 25 simultaneous full-duplex WebSocket audio sessions per worker instance before horizontal container autoscaling triggers.
