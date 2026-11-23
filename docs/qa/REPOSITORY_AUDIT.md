# Repository Architecture Audit & Verification Report

**Project:** Opportunity OS  
**Repository:** `https://github.com/sanjuskb/opportunity-os`  
**Audit Date:** November 23, 2026  
**Auditor:** Antigravity (Continuous Architecture QA & Engineering Readiness Agent)  
**Target Integration Branch:** `develop`  
**Current Audit Branch:** `antigravity/architecture-qa`  

---

## 1. Executive Summary & Verification Matrix

An exhaustive line-by-line inspection and operational test was conducted across the Opportunity OS monorepo. The evaluation spanned all 13 architecture blueprints, 5 ADRs, source packages, database schemas, CI/CD pipelines, Docker manifests, lockfiles, and local execution environments.

### 1.1 Verification Status Summary

| Check Category | Total Checks | Passed | Failed | Blocked | Skipped | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Git & Branch Strategy** | 5 | 5 | 0 | 0 | 0 | **PASS** |
| **Package Manifests & Lockfiles** | 6 | 6 | 0 | 0 | 0 | **PASS** |
| **TypeScript / Frontend Build** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **Python / Backend Test & Lint** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **Database & Migration Consistency** | 3 | 2 | 1 | 0 | 0 | **NEEDS ALIGNMENT** |
| **CI / GitHub Actions Workflows** | 4 | 2 | 2 | 0 | 0 | **NEEDS UPDATE** |
| **Docker & Infrastructure** | 3 | 2 | 1 | 0 | 0 | **NEEDS FIX** |
| **Security & Secrets Hygiene** | 4 | 4 | 0 | 0 | 0 | **PASS** |
| **Architecture & Ownership Alignment** | 4 | 2 | 2 | 0 | 0 | **CONTRADICTION FOUND** |
| **TOTAL** | **37** | **31** | **6** | **0** | **0** | **83.8% Operational** |

---

## 2. Itemized Audit Findings

### Finding 1: Team Ownership Contradiction Regarding Machine Learning (ML)
- **Severity:** High
- **Affected Files:**
  - `docs/team/team-responsibilities.md`
  - `README.md`
  - `docs/architecture/repository-architecture.md`
- **Evidence:**
  `docs/team/team-responsibilities.md` lines 10-18 state:
  > *"Ramaraju: Primary ownership ... ML and recommendation services"*
  And in `README.md`:
  > *"Ramaraju: Backend Lead, FastAPI, LangGraph, Olostep/Crustdata, ML Matching"*
- **Why It Matters:**
  This directly contradicts the non-negotiable team charter:
  *“Sanju: Entire frontend architecture and implementation, voice frontend, ALL ML model selection, training experiments and evaluation. Do not transfer ML ownership to Ramaraju.”*
  Leaving this uncorrected will lead to role confusion, fragmented model pipelines, and duplicate work during Sprint 1.
- **Recommended Owner:** Antigravity (QA documentation correction) & Sanju / Ramaraju (Sign-off)
- **Recommended Correction:**
  Update `docs/team/team-responsibilities.md`, `README.md`, and `docs/architecture/repository-architecture.md` to explicitly assign all ML architecture, model selection, embedding fine-tuning, training experiments under `experiments/`, and offline evaluation to Sanju. Ramaraju integrates the models into FastAPI inference endpoints once Sanju specifies the model contracts.
- **Verification Method:** Grep across all markdown files to confirm ML ownership is unambiguously assigned to Sanju.

---

### Finding 2: Missing Standalone Output in Next.js Config for Docker Build
- **Severity:** Medium
- **Affected File:** `apps/web/next.config.ts`, `infra/docker/Dockerfile.web`
- **Evidence:**
  `infra/docker/Dockerfile.web` line 16 contains:
  ```dockerfile
  COPY --from=builder /app/apps/web/.next/standalone ./
  ```
  However, `apps/web/next.config.ts` currently contains:
  ```typescript
  const nextConfig: NextConfig = {
    reactStrictMode: true,
    transpilePackages: [...],
  };
  ```
- **Why It Matters:**
  Next.js does not generate the `.next/standalone` directory unless `output: 'standalone'` is explicitly defined in `next.config.ts`. Running `docker build -f infra/docker/Dockerfile.web .` will fail with `COPY failed: file not found in build context`.
- **Recommended Owner:** Sanju
- **Recommended Correction:**
  Add `output: 'standalone'` to `apps/web/next.config.ts`.
- **Verification Method:** Run `pnpm --filter @opportunity-os/web build` and verify that `apps/web/.next/standalone` is generated.

---

### Finding 3: CI pnpm Version and Build Permissions Mismatch
- **Severity:** Medium
- **Affected File:** `.github/workflows/frontend-checks.yml`, `package.json`
- **Evidence:**
  1. `package.json` specifies `"packageManager": "pnpm@12.4.2"`.
  2. `.github/workflows/frontend-checks.yml` line 21 specifies `version: 10`.
  3. In pnpm v12, packages with build scripts (such as `sharp@0.33.5`) trigger `ERR_PNPM_IGNORED_BUILDS` unless approved or configured in `.npmrc`.
- **Why It Matters:**
  The GitHub Actions CI pipeline will either fail on dependency resolution or install packages with a different lockfile layout than local developer machines.
- **Recommended Owner:** Shared / Antigravity
- **Recommended Correction:**
  Update `.github/workflows/frontend-checks.yml` to use pnpm version `12.4.2`, and ensure `.npmrc` is recognized during CI installation.
- **Verification Method:** Run local CI emulation check and verify `pnpm install --frozen-lockfile` succeeds cleanly.

---

### Finding 4: CI Backend Step Missing Dev Extra for Pytest & Ruff
- **Severity:** Medium
- **Affected File:** `.github/workflows/backend-checks.yml`, `apps/api/pyproject.toml`
- **Evidence:**
  `.github/workflows/backend-checks.yml` line 28 runs:
  ```yaml
  - name: Sync Backend Dependencies
    working-directory: apps/api
    run: uv sync
  ```
  However, in `apps/api/pyproject.toml`, `pytest`, `ruff`, and `mypy` are declared under `[project.optional-dependencies] dev`.
- **Why It Matters:**
  `uv sync` without flags only installs base dependencies (`fastapi`, `pydantic`, `sqlalchemy`, etc.). Subsequent steps running `uv run ruff check .` and `uv run pytest` will fail with `program not found: ruff` in CI.
- **Recommended Owner:** Ramaraju / Antigravity
- **Recommended Correction:**
  Update `.github/workflows/backend-checks.yml` to run `uv sync --extra dev`.
- **Verification Method:** Execute `uv sync --extra dev` in a clean Python container and confirm `uv run ruff` and `uv run pytest` succeed.

---

### Finding 5: Vanilla PostgreSQL Container vs. Supabase Auth Schema Reference
- **Severity:** Medium
- **Affected File:** `supabase/migrations/20261123000001_initial_schema.sql`, `docker-compose.yml`
- **Evidence:**
  `supabase/migrations/20261123000001_initial_schema.sql` lines 12-14 define:
  ```sql
  CREATE TABLE IF NOT EXISTS public.profiles (
      id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  ```
  In `docker-compose.yml`, the local database uses standard `pgvector/pgvector:pg16` and mounts `./supabase/migrations` into `/docker-entrypoint-initdb.d`.
- **Why It Matters:**
  When spinning up `docker compose up postgres`, a vanilla PostgreSQL container initializes with an empty database that does not have the `auth` schema or `auth.users` table pre-existing. This will cause initialization to fail with `ERROR: relation "auth.users" does not exist`.
- **Recommended Owner:** Ramaraju
- **Recommended Correction:**
  In the initial migration or a pre-migration script for local Docker Compose, create the `auth` schema and a stub `auth.users` table if not running within the full Supabase local stack (`supabase start`).
- **Verification Method:** Validate SQL syntax against a clean Docker Postgres container.

---

### Finding 6: Missing Pytest-Asyncio Default Loop Scope Configuration
- **Severity:** Low
- **Affected File:** `apps/api/pyproject.toml`
- **Evidence:**
  Running `pytest` produces:
  ```text
  PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
  The event loop scope for asynchronous fixtures will default to the fixture scope.
  ```
- **Why It Matters:**
  While currently non-fatal, future updates to `pytest-asyncio` will turn this into an error, causing test runs on newer CI runners to fail.
- **Recommended Owner:** Ramaraju / Antigravity
- **Recommended Correction:**
  Add `asyncio_default_fixture_loop_scope = "function"` to `[tool.pytest.ini_options]` in `apps/api/pyproject.toml`.
- **Verification Method:** Run `uv run pytest` and verify that the warning is eliminated.

---

## 3. Operational Verification Audit (Executed Commands & Results)

Every verification test documented below was actively executed by Antigravity in the local environment:

| Test ID | Command | Target Component | Observed Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **TEST-01** | `git status` | Git workspace | Clean working tree; tracking `antigravity/architecture-qa` | **PASS** |
| **TEST-02** | `gh repo view sanjuskb/opportunity-os` | Remote GitHub repo | Public repo verified; metadata matches | **PASS** |
| **TEST-03** | `gh api repos/sanjuskb/opportunity-os/branches/main/protection` | Branch Protection | `main` and `develop` protected with PR review required | **PASS** |
| **TEST-04** | `pnpm type-check` | TypeScript workspace | All 5 projects passed type check | **PASS** |
| **TEST-05** | `pnpm test` | Node test runner | Unit sanity test passed | **PASS** |
| **TEST-06** | `cd apps/api && uv run pytest` | Backend API tests | 2 passed in 4.53s | **PASS** |
| **TEST-07** | `cd apps/api && uv run ruff check .` | Backend linter | All checks passed, 0 errors | **PASS** |
| **TEST-08** | `docker compose config` | Docker Compose spec | Validated service syntax for postgres, redis, api, web | **PASS** |

---

## 4. Security & Environment Variable Audit

1. **Secret Scanning:**
   - No hardcoded API keys (`GEMINI_API_KEY`, `OLOSTEP_API_KEY`, `CRUSTDATA_API_KEY`) found in version control.
   - All references point to `.env.example` placeholders.
2. **Git Ignore Integrity:**
   - `.gitignore` properly excludes `.env*` files (except `.env.example`), `.venv/`, `node_modules/`, `*.pem`, `*.key`.
3. **Sensitive Data in Tables:**
   - Third-party portal passwords and student raw audio recordings are excluded from PostgreSQL table definitions.
