# ADR-001: Adoption of pnpm Monorepo Structure

## Status
Accepted

## Context
Opportunity OS consists of a Next.js 15+ frontend, a FastAPI Python backend, shared domain contracts, design tokens, and infrastructure definitions. The engineering team consists of two developers collaborating under hackathon timeframes.

## Decision
Adopt a single pnpm monorepo structure housing `apps/web`, `apps/api`, and `packages/*` with a unified root Makefile and GitHub Actions matrix.

## Consequences
- **Positive:** Single PRs can update shared types, frontend components, and backend schemas simultaneously. Zero multi-repository synchronization overhead.
- **Negative:** Requires dual Node.js and Python toolchains in CI/CD and developer environments.
