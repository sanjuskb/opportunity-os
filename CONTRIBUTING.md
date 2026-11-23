# Contributing to Opportunity OS

We follow a structured Git workflow for the Homingo Hackathon:

## Branch Strategy & Workflow
1. Base branches:
   - `main`: Production release baseline. No direct commits.
   - `develop`: Integration branch where all peer-reviewed PRs land.
2. Developer branches:
   - `sanju`: Sanju's active development branch (Frontend, UI/UX, Voice).
   - `ramaraju`: Ramaraju's active development branch (Backend, Agents, ML).
3. Pull Request Requirements:
   - Work on your designated branch or a short-lived `feature/*` branch.
   - Submit PRs targeting `develop`.
   - Ensure all type checks and linters pass before opening a PR.
   - Peer review is required before merging into `develop`.
   - Verified changes are promoted from `develop` to `main` via release PRs.

## Quality Standards
- Strict TypeScript (`apps/web`, `packages/*`).
- Type-annotated Python with Pydantic validation (`apps/api`).
- Keep all secrets in `.env` (never commit real credentials).
- Human-in-the-loop approval is mandatory for external browser submissions.
