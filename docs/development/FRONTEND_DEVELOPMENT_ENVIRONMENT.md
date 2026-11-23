# Opportunity OS — Frontend Development Environment, MCP Setup & Toolchain Readiness

**Document ID:** `DOC-DEV-002`  
**Revision:** `1.0.0`  
**Date:** `2026-11-23`  
**Author:** Senior Frontend DevOps Engineer & Antigravity MCP Configuration Specialist  
**Owner / Lead Engineer:** Sanju (Frontend & ML Architecture)  
**Target Machine:** Sanju's Primary Development Workstation (Frontend, UI/UX, 3D Hero, Voice Client)  
**Repository:** [sanjuskb/opportunity-os](https://github.com/sanjuskb/opportunity-os)  
**Active Working Branch:** `sanju` (synchronized with `develop`)

---

## 1. Executive Summary

This document specifies the exact state, configuration, and verification status of the development environment and Model Context Protocol (MCP) toolchains established for **Opportunity OS** frontend development.

All operations were executed autonomously with strict adherence to architectural boundaries, security policies, and zero-exposure credential handling.

```
+-----------------------------------------------------------------------------------------+
|                                    SANJU'S WORKSTATION                                  |
|                                                                                         |
|   +--------------------------+    +--------------------------+    +-----------------+   |
|   |   Frontend Toolchain     |    |   Container Toolchain    |    |   Git & GitHub  |   |
|   |  - Node.js 24.18.0       |    |  - Docker CLI 29.4.3     |    |  - Git 2.52.0   |   |
|   |  - pnpm 12.4.2           |    |  - Docker Compose 5.1.3  |    |  - gh CLI 2.101 |   |
|   |  - Next.js 15 / React 19 |    |  - Docker MCP v0.42.0    |    |  - 4 Branches   |   |
|   +--------------------------+    +--------------------------+    +-----------------+   |
|                                                                                         |
|   +---------------------------------------------------------------------------------+   |
|   |                               MCP SERVER INTEGRATIONS                           |   |
|   |  +------------------------+  +-----------------------+  +---------------------+ |   |
|   |  |      Context7 MCP      |  |     Playwright MCP    |  | Chrome DevTools MCP | |   |
|   |  |   Streamable HTTP      |  |      Local stdio      |  |  Protocol Injected  | |   |
|   |  |   Official Live Docs   |  |  Headless E2E / A11y  |  |  Runtime Profiling  | |   |
|   |  +------------------------+  +-----------------------+  +---------------------+ |   |
|   +---------------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Workstation & System Toolchain Status

### 2.1 Operating System & Hardware Profile
- **Operating System:** Microsoft Windows 11 Home Single Language (Version 10.0.26300, Build 26300, 64-bit)
- **Primary Shell:** Windows PowerShell 5.1 (`powershell.exe`)
- **Primary IDE / Agent Harness:** Google Antigravity 2.0
- **Path Resolution:** Windows paths supported with forward-slash convention in Markdown/Git.

### 2.2 Core Runtime & Development Binaries

| Component | Verified Version | Installation Path / Source | Status |
| :--- | :--- | :--- | :--- |
| **Node.js** | `v24.18.0` | `C:\Program Files\nodejs\node.exe` | **VERIFIED** |
| **npm** | `11.16.0` | `C:\Program Files\nodejs\npm.cmd` | **VERIFIED** |
| **pnpm** | `12.4.2` | Global pnpm binary | **VERIFIED** |
| **Python** | `3.13.6` | `C:\Program Files\Python313\python.exe` | **VERIFIED** |
| **uv** | `0.12.15` | Astral uv CLI | **VERIFIED** |
| **Git** | `2.52.0.windows.1` | `C:\Program Files\Git\cmd\git.exe` | **VERIFIED** |
| **GitHub CLI (`gh`)** | `2.101.0` | `C:\Program Files\GitHub CLI\gh.exe` | **VERIFIED** |

---

## 3. GitHub & Repository Infrastructure

### 3.1 Authentication & Scopes
- **Active User:** `sanjuskb`
- **Authentication Method:** Secure system keyring (zero cleartext token exposure)
- **Verified Scopes:** `gist`, `read:org`, `repo`, `workflow`
- **Protocol:** HTTPS (`github.com`)

### 3.2 Repository Consolidation & Branch Topology
The repository has been consolidated from historical feature branches into **exactly 4 permanent branches**:

| Branch | SHA Baseline | Purpose & Ownership | Protection Rules |
| :--- | :--- | :--- | :--- |
| `main` | `9cee065` | Production release candidate baseline. | Requires PR, 2 approvals, CI pass. |
| `develop` | `2242d24` | Shared engineering integration branch. | Requires PR, CI pass, merge commits. |
| `sanju` | `2242d24` | Frontend and ML lead contributor branch. | Protected direct-push for Sanju. |
| `ramaraju` | `2242d24` | Backend and scraper lead contributor branch. | Protected direct-push for Ramaraju. |

> [!NOTE]
> All obsolete experimental branches (`antigravity/architecture-qa`, `antigravity/frontend-architecture`, `antigravity/3d-hero-asset-research`, `antigravity/phase-5-finalization`) have been permanently deleted from `origin`. PR #1, PR #2, and PR #3 have been merged cleanly into `develop`.

---

## 4. Docker & Container Toolchain

### 4.1 Installed Components
- **Docker Engine CLI:** `Docker version 29.4.3, build 055a478`
- **Docker Compose:** `v5.1.3`
- **Docker Desktop MCP Plugin:** `Docker MCP Plugin Version v0.42.0` (Binary located at `C:\Program Files\Docker\cli-plugins\docker-mcp.exe`)

### 4.2 Daemon Status & Operating Instructions
- **Current Daemon Status:** **INACTIVE (OFFLINE)**.
- **Diagnostic Result:** Connection to named pipe `//./pipe/dockerDesktopLinuxEngine` failed (`The system cannot find the file specified`). Docker Desktop is installed, but the background engine is currently not running.
- **Developer Instructions:**
  1. For standalone Next.js container builds (`apps/web/Dockerfile`) or local multi-service testing, launch **Docker Desktop** from the Windows Start menu or run:
     ```powershell
     Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
     ```
  2. Wait 30 seconds for the Linux VM and socket to initialize.
  3. Validate daemon readiness with:
     ```powershell
     docker info
     ```
  4. Once Docker Desktop is running, Docker MCP and local container workflows become immediately available without configuration changes.

---

## 5. Model Context Protocol (MCP) Setup & Verification

Global MCP configuration is maintained at:  
`C:\Users\sanju\.gemini\config\mcp_config.json` (symbolically linked to `~/.gemini/antigravity/mcp_config.json`).

### 5.1 Context7 MCP (Official Live Documentation Retrieval)

- **Purpose:** Supplies live, version-accurate documentation, API schemas, and code recipes for Next.js 15, React 19, Tailwind CSS, and frontend ecosystem libraries directly into the agent context.
- **Protocol:** Streamable HTTP (MCP Specification `2024-11-05`).
- **Endpoint URL:** `https://mcp.context7.com/mcp`
- **Configuration in `mcp_config.json`:**
  ```json
  "context7": {
    "url": "https://mcp.context7.com/mcp"
  }
  ```
- **Discovered Capabilities:**
  1. `resolve-library-id`: Maps package names (e.g., `Next.js`, `Tailwind CSS`) to official Context7 library identifiers (`/vercel/next.js`, `/websites/nextjs`).
  2. `query-docs`: Queries scoped documentation and code examples with language-targeted relevance.
- **Live Verification Evidence:**
  - Initialized session successfully with server `Context7 v4.7.3`.
  - Executed `resolve-library-id` for `"Next.js"`, receiving canonical library ID `/vercel/next.js` with benchmark score 78.2 and 7,661 verified code snippets.
  - Executed `query-docs` for `App Router routing`, successfully returning official Next.js 15 routing documentation and `page.tsx` TypeScript examples.
- **Verification Status:** **VERIFIED & OPERATIONAL**.

### 5.2 Playwright MCP (Browser Automation & Accessibility Testing)

- **Purpose:** Autonomous end-to-end user-journey verification, accessibility tree inspection, DOM snapshots, form interactions, and cross-browser testing for the Opportunity OS web application.
- **Package:** `@playwright/mcp@latest` (Executed via Node `npx` with `--headless` flag).
- **Transport:** Local stdio JSON-RPC.
- **Configuration in `mcp_config.json`:**
  ```json
  "playwright": {
    "command": "npx",
    "args": [
      "-y",
      "@playwright/mcp@latest",
      "--headless"
    ]
  }
  ```
- **Discovered Tools (25 Total):**
  - Navigation & State: `browser_navigate`, `browser_navigate_back`, `browser_navigate_forward`, `browser_reload`, `browser_close`, `browser_resize`
  - User Interactions: `browser_click`, `browser_type`, `browser_hover`, `browser_press_key`, `browser_select_option`, `browser_fill_form`, `browser_drag`, `browser_mouse_down`, `browser_mouse_up`, `browser_mouse_move`
  - Inspection & Assertions: `browser_snapshot`, `browser_take_screenshot`, `browser_get_source`, `browser_handle_dialog`
  - Diagnostics: `browser_console_messages`, `browser_clear_console_messages`, `browser_network_requests`
- **Live Verification Evidence:**
  - Initialized Playwright MCP 1.66.0-alpha using cached Chromium browser binaries at `C:\Users\sanju\AppData\Local\ms-playwright\chromium-1243`.
  - Navigated to `https://example.com/` in headless Chromium.
  - Executed `browser_snapshot`, verifying accessibility tree and page title (`Example Domain`).
  - Executed clean browser teardown.
- **Verification Status:** **VERIFIED & OPERATIONAL**.

### 5.3 Chrome DevTools MCP (Coexistence Rationale)

- **Current State:** Pre-configured in `~/.gemini/antigravity/mcp/chrome_devtools` with 33 tools.
- **Functional Coexistence & Rationale:**
  - *Playwright MCP* operates at the **Application & User Journey Layer**: multi-step workflows, form submissions, accessibility tree verification, responsive viewport testing.
  - *Chrome DevTools MCP* operates at the **Engine & Runtime Layer**: CDP network interception, memory leak profiling, V8 CPU profiling, live CSS rule inspection, and console error streaming.
  - **Decision:** Both servers are retained. They serve strictly complementary purposes without namespace collision.
- **Status:** **ALREADY CONFIGURED & RETAINED**.

---

## 6. Architectural Boundaries & Excluded Tooling

To maintain strict hackathon role boundaries and prevent unnecessary bloat or security risks on Sanju's primary development workstation, the following tools are explicitly excluded from this machine:

| Excluded Tool | Designated Owner / Location | Exclusion Rationale | Status |
| :--- | :--- | :--- | :--- |
| **Supabase MCP** | Ramaraju / Backend Workspace | Database schema, RLS policies, and migrations belong to Ramaraju. Configured remotely; no local mutation on frontend machine. | **NOT REQUIRED** |
| **Olostep / Crustdata** | Ramaraju / Web Scraping Subsystem | Scraping workers and external ingestion APIs execute in backend pipelines. | **NOT REQUIRED** |
| **Kaggle CLI** | Sanju / Dedicated ML Laptop | Heavy model training, fine-tuning, and dataset ingestion are hosted on a separate machine. | **NOT REQUIRED (ON THIS MACHINE)** |
| **Hugging Face Training** | Sanju / Dedicated ML Laptop | Model checkpoint training and GPU offloading are isolated to avoid workstation throttling. | **NOT REQUIRED (ON THIS MACHINE)** |

---

## 7. Deployment Readiness: Vercel CLI Status

- **Status:** **DEFERRED**.
- **Rationale:** Installing Vercel CLI and creating remote project links at this stage would introduce unverified deployment credentials and trigger premature deployment attempts before the frontend component library, 3D Hero integration, and API client layers are completed and tested.
- **Activation Gate:** Vercel deployment will be configured in Phase 6 as soon as the Next.js frontend passes the local build, type-check, and Playwright verification gates.

---

## 8. Summary Status Matrix

| Subsystem / Tool | Target Scope | Current Status | Notes / Next Step |
| :--- | :--- | :--- | :--- |
| **Windows 11 & Shell** | Workstation OS | **VERIFIED** | PowerShell 5.1, Node 24.18, npm 11.16, pnpm 12.4.2, Git 2.52. |
| **GitHub CLI & Auth** | Developer Tooling | **VERIFIED** | Authenticated as `sanjuskb`, secure keyring storage. |
| **Repository Topology** | Git Architecture | **COMPLETED** | 4 permanent branches (`main`, `develop`, `sanju`, `ramaraju`). |
| **Context7 MCP** | Documentation Agent | **VERIFIED** | Configured and live-tested (`/vercel/next.js` docs retrieved). |
| **Playwright MCP** | QA & E2E Testing | **VERIFIED** | Configured and live-tested (headless navigation + a11y snapshot). |
| **Chrome DevTools MCP** | Runtime Profiling | **ALREADY CONFIGURED** | Retained for complementary CDP and performance diagnostics. |
| **Docker Desktop CLI** | Containerization | **ALREADY CONFIGURED** | CLI and MCP plugin ready; daemon is inactive until launched. |
| **Backend & DB MCPs** | Database / Scraping | **NOT REQUIRED** | Owned by Ramaraju on backend infrastructure. |
| **Heavy ML Tooling** | Training Pipeline | **NOT REQUIRED** | Hosted on dedicated ML machine. |
| **Vercel CLI** | Production Deploy | **DEFERRED** | Postponed until Phase 6 frontend preview readiness. |
