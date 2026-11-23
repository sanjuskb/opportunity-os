# Opportunity OS — MCP Servers & CLI Development Setup

## 1. Official MCP Server Tooling Strategy

Opportunity OS integrates strictly with verified, official Model Context Protocol (MCP) servers and command-line interfaces to support developer workflows, CI/CD, and repository maintenance.

---

## 2. Configured & Recommended Official Tooling

### 2.1 GitHub MCP & CLI
- **Tool:** GitHub CLI (`gh`) & Official GitHub MCP Server.
- **Verification:** `gh auth status` (Authenticated as `sanjuskb`).
- **Capabilities:** Repository creation, issue triage, PR review automation, branch ruleset inspection.

### 2.2 Supabase CLI
- **Tool:** Supabase CLI (`supabase`).
- **Installation:**
  ```bash
  # Via pnpm / npm
  pnpm add -D supabase
  # Verify installation
  npx supabase --version
  ```
- **Local Dev Database:** `npx supabase start` (spins up local Postgres, Auth, Storage, and Studio).
- **Migration Verification:** `npx supabase db lint` / `npx supabase db diff`.

### 2.3 Gemini Developer CLI & Python SDK
- **Tool:** Official Google GenAI SDK (`google-genai`) & Python CLI.
- **Installation:** Configured via `uv sync` in `apps/api/pyproject.toml`.
- **Security Boundary:** API keys are never stored in versioned JSON or committed configs. Loaded strictly from `.env` or system environment variables.

### 2.4 Playwright Browser Automation CLI
- **Tool:** Playwright (`@playwright/test` and `playwright` Python).
- **Driver Installation:**
  ```bash
  # Inside apps/api
  uv run playwright install --with-deps chromium
  ```

---

## 3. Tool Verification Matrix

| Tool | Source | Verification Command | Security Boundary |
| :--- | :--- | :--- | :--- |
| `gh` | Official GitHub CLI | `gh --version` | User keyring storage |
| `supabase` | Official Supabase CLI | `npx supabase status` | Local Docker network |
| `uv` | Official Astral uv | `uv --version` | Virtual environment isolation |
| `playwright` | Official Microsoft Playwright | `uv run playwright --version` | Sandboxed headless browser |

Do not install unofficial, unverified third-party MCP servers. All external tool calls must execute within verified sandboxes.
