# NexteRaS (Opportunity OS) — Safe Environment Configuration Guide

> **Security Policy:** Never commit real credentials, passwords, JWT secrets, or API tokens into Git, Dockerfiles, or markdown documents. All local secrets belong strictly in gitignored `.env` and `apps/web/.env.local` (or Cloud Run / Vercel secret managers in production).

---

## 1. Selected Development Database Strategy

NexteRaS intentionally separates **local development & destructive integration testing** from **hosted Supabase**:

1. **Hosted Supabase Project (Staging / Remote Auth & Storage):**
   - Used for Supabase GoTrue Auth (Google OAuth PKCE + 6-digit Email OTP), JWKS token verification (`SUPABASE_JWKS_URL`), and private Storage (`resumes` bucket) once migrations are explicitly reviewed and approved.
   - **Never** run destructive local test suites against the hosted database (`TEST_DATABASE_URL` must point strictly to `127.0.0.1` / `localhost`).

2. **Local Non-Conflicting PostgreSQL 17 + pgvector & Redis Stack (`docker-compose.local.yml`):**
   - Host port `54322` is preserved cleanly if running `supabase start` or an unrelated local database on the developer workstation.
   - `docker-compose.local.yml` boots `pgvector/pgvector:pg17` on **`127.0.0.1:54332`** (`opportunity-os-postgres`) and `redis:7-alpine` on **`127.0.0.1:6379`** (`opportunity-os-redis`).
   - `scripts/dev/bootstrap_local_db.py` initializes `extensions` (`uuid-ossp`, `pgcrypto`, `vector`), `auth` (`auth.users`, `auth.uid()`, `auth.role()`), `storage` (`storage.buckets`, `storage.objects`), and Supabase roles (`anon`, `authenticated`, `service_role`) cleanly, then applies all ordered `supabase/migrations/*.sql` files + `supabase/seed/seed.sql`.

> **Rule:** Never run local Supabase CLI and hosted remote migrations simultaneously against the same `DATABASE_URL`. Keep `.env` explicitly scoped per environment.

---

## 2. Variable Inventory

| Variable | Scope | Purpose | Source / Safe Placeholder |
|---|---|---|---|
| `ENVIRONMENT` | API / Worker | `development`, `staging`, or `production` (`production` enforces fail-closed checks & `DEBUG=false`) | `development` |
| `DATABASE_URL` | API / Worker | Asyncpg SQLAlchemy DSN (`postgresql+asyncpg://...`) | `postgresql+asyncpg://postgres:postgres@127.0.0.1:54332/postgres` |
| `TEST_DATABASE_URL` | Pytest Live | Local-only DB DSN for `tests/integration/*_live.py` | `postgresql+asyncpg://postgres:postgres@127.0.0.1:54332/postgres` |
| `REDIS_URL` | API / Worker | Redis connection URL for ARQ queues, voice tickets, and rate limits | `redis://127.0.0.1:6379/0` |
| `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL` | API / Web | Supabase project URL (`https://<ref>.supabase.co`) | `https://your-project-ref.supabase.co` |
| `SUPABASE_ANON_KEY` / `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | API / Web | Client-safe publishable/anon key | `placeholder-supabase-publishable-key` |
| `SUPABASE_SERVICE_ROLE_KEY` | API / Worker | Server-only elevated Supabase key (`SECRET` / `service_role`) | `placeholder-supabase-secret-key` |
| `SUPABASE_JWKS_URL` | API | Asymmetric ES256/RS256 JWKS verification URL | `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_SECRET` / `JWT_SECRET` | API | Symmetric HS256 fallback secret (≥ 32 chars) | `placeholder-jwt-secret-at-least-32-chars` |
| `SUPABASE_STORAGE_BUCKET` | API | Private bucket storing uploaded PDF/DOCX resumes | `resumes` |
| `GEMINI_API_KEY` | API / ML | Google Gemini REST & Live API key | `placeholder-gemini-api-key` |
| `GEMINI_MODEL` / `GEMINI_LIVE_MODEL` | API | Default Gemini REST and Live models | `gemini-2.5-flash` |
| `OLOSTEP_API_KEY` | API / Worker | Olostep search/scrape/crawl/monitors key | `placeholder-olostep-api-key` |
| `CRUSTDATA_API_KEY` | API / Worker | Crustdata company & job intelligence key | `placeholder-crustdata-api-key` |
| `ML_MATCHING_MODEL_PATH` | API / ML | Local MiniLM fine-tuned checkpoint path | `ml/artifacts/minilm-nexteras-v1` |
| `ML_MAX_LOADED_MODELS` / `TORCH_NUM_THREADS` | API / Worker | CPU RAM/thread bounds for single-node inference | `1` / `4` |
| `ENABLE_PRETRAINED_NLI` | API / ML | Enables cross-encoder NLI model when memory allows (`false` uses fast lexical NLI fallback) | `false` |
| `PLAYWRIGHT_HEADLESS` / `PLAYWRIGHT_TIMEOUT_MS` | Worker | Sandbox browser execution settings | `true` / `30000` |
| `SENTRY_DSN` / `POSTHOG_API_KEY` | API / Web | Optional error monitoring & product analytics keys | empty / `placeholder-*` |
| `NEXT_PUBLIC_API_BASE_URL` | Web | Public FastAPI v1 base URL | `http://localhost:8000/api/v1` |

---

## 3. Verification Checklist (No Secret Output)

Run verification safely via presence checks rather than printing raw values:
- Confirm `.env` and `apps/web/.env.local` exist locally and `git status -sb` never shows them tracked.
- Run `python scripts/dev/bootstrap_local_db.py` to initialize local Postgres 17 + pgvector and apply all migrations cleanly.
- Run `cd apps/api && uv run pytest -v` and confirm `/api/v1/health/ready` reports `database: "healthy"` and `redis: "healthy"`.
