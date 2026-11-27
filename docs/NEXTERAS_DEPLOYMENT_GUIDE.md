# NexteRaS (Opportunity OS) — Deployment & Operations Guide

## 1. Local Non-Conflicting Docker Environment

The repository includes `docker-compose.local.yml` specifically isolated on host port **`54332`** (PostgreSQL 17 + `pgvector` HNSW) and **`6379`** (Redis 7) so local Supabase fintech stacks occupying ports `54321–54327` are never disturbed.

```bash
docker compose -f docker-compose.local.yml up -d
./apps/api/.venv/Scripts/python.exe scripts/dev/bootstrap_local_db.py
```

Running `bootstrap_local_db.py` applies all ordered migrations (`supabase/migrations/20261123000001*.sql` through `20261127000004*.sql`) and loads idempotent seed opportunities and skills (`supabase/seed/seed.sql`).

## 2. Starting Local Services for Development

1. **FastAPI Backend (`apps/api`):**
   ```bash
   cd apps/api
   uv run --no-sync uvicorn app.main:app --reload --port 8000
   ```
2. **ARQ Background Worker (`apps/api/app/tasks/worker.py`):**
   ```bash
   cd apps/api
   uv run --no-sync python -m app.tasks.worker
   ```
3. **Next.js Frontend (`apps/web`):**
   ```bash
   pnpm --filter @opportunity-os/web dev
   ```

## 3. Production Deployment Topology

| Tier | Platform | Manifest / Config | Notes |
|---|---|---|---|
| **Database / Auth / Storage** | Hosted Supabase | `supabase/migrations/*.sql` | Apply ordered migrations using Supabase CLI `supabase db push` or reviewed SQL migrations; verify private `resumes` bucket RLS. |
| **Frontend Web App** | Vercel | `apps/web/vercel.json` | Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_BASE_URL` pointing to Cloud Run API URL. |
| **Backend API** | Google Cloud Run | `infra/cloudrun/api-service.yaml` & `infra/docker/Dockerfile.api` | Uses non-root user, frozen `uv.lock`, WebSocket sticky sessions (`--timeout 300`), healthchecks at `/api/v1/health`. |
| **Background Worker & Playwright** | Cloud Run Worker / Compute | `infra/cloudrun/worker-job.yaml` & `infra/docker/Dockerfile.worker` | Runs ARQ cron jobs (`backfill_missing_embeddings`, `check_opportunity_deadlines`, `aggregate_analytics_metrics`) and Chromium automation. |
| **Container Stack** | Docker Compose Prod | `docker-compose.prod.yml` | Full multi-container production template requiring explicit secrets in environment. |

## 4. Production Safety & Security Gates

- `ENVIRONMENT=production` fails closed unless `DEBUG=false`, `REDIS_URL`, and `SUPABASE_URL` / `SUPABASE_JWT_ISSUER` are set.
- Private files upload exclusively via `POST /api/v1/resumes/upload` to private Supabase Storage with per-user `auth.uid()` RLS policies and signed URLs (`GET /api/v1/resumes/{id}/download-url`).
- Sentry error tracking and PostHog analytics activate cleanly when `SENTRY_DSN` and `POSTHOG_API_KEY` are supplied, scrubbing default PII.
- Automated application submission via Playwright unconditionally halts prior to clicking Submit and creates an `approval_requests` gate (`status='pending'`), and unconditionally halts on CAPTCHA/MFA (`requires_manual_completion`).
