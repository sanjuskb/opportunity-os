# Opportunity OS — Monorepo Architecture & Dependency Boundaries

## 1. Top-Level Directory Taxonomy

```text
opportunity-os/
├── .github/              # Continuous Integration, Issue templates, Code ownership
│   ├── workflows/        # ci.yml, frontend-checks.yml, backend-checks.yml, security-checks.yml
│   └── CODEOWNERS        # Explicit file review ownership between Sanju and Ramaraju
├── apps/
│   ├── web/              # Next.js 15+ frontend application (Sanju)
│   └── api/              # FastAPI backend, LangGraph agents, and ML core (Ramaraju)
├── packages/
│   ├── shared-types/     # Shared TypeScript domain models & DTOs
│   ├── api-client/       # Typed HTTP & WebSocket client
│   ├── design-tokens/    # Design system palette, typography, and constants
│   └── shared-config/    # Shared language metadata and constants
├── supabase/             # PostgreSQL database migrations, seeds, and configs
├── infra/                # Multi-stage Dockerfiles and container orchestration
├── scripts/              # Developer environment setup & verification scripts
├── docs/                 # Full 13 architecture blueprints, ADRs, and guidelines
└── experiments/          # Research notebooks, LoRA fine-tuning, and voice evaluation
```

---

## 2. Dependency Boundaries & Import Conventions

1. **Shared Packages First:** Shared types, constants, and API interfaces must live in `packages/*` and be imported via `@opportunity-os/<package>` aliases.
2. **No Circular Imports:**
   - `apps/web` imports from `packages/*`. It never imports directly from `apps/api`.
   - `apps/api` communicates with `apps/web` strictly via REST endpoints, WebSocket streams, and Pydantic-validated contracts.
3. **Module Ownership:**
   - Frontend and UI design system files are owned by **Sanju**.
   - Backend routes, agent workflows, database migrations, and integrations are owned by **Ramaraju**.
   - Changes to `packages/*`, database schemas, and shared contracts require mutual review.
