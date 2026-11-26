# Opportunity OS — Database Schema & Entity Relationships

## 1. Overview & Extensions

The database is built on **PostgreSQL 16** via **Supabase**, with the following extensions enabled:
- `uuid-ossp`: High-entropy UUID primary keys.
- `vector`: `pgvector` extension supporting dual vector similarity searches:
  - `embedding vector(768)` (Gemini `text-embedding-004`, IVFFlat cosine index `idx_embeddings_vector`).
  - `embedding_minilm_384 vector(384)` (`sentence-transformers/all-MiniLM-L6-v2`, partial HNSW cosine index `idx_embeddings_minilm_384_hnsw`).

---

## 2. Migrations & Local Development Architecture

### 2.1 Migration Sequence (`supabase/migrations/`)
1. `20261123000001_initial_schema.sql` — Creates all 25 tables, `uuid-ossp`/`vector` extensions, and initial indexes.
2. `20261126000001_harden_rls_and_auth_trigger.sql` — Enables RLS on all 25 tables, defines least-privilege RLS policies, and creates the `SECURITY DEFINER` `public.handle_new_user()` trigger on `auth.users`.
3. `20261126000002_constraints_and_vector_alignment.sql` — Safely enforces `UNIQUE (user_id, opportunity_id)` on `applications` and `UNIQUE (opportunity_id)` on `opportunity_eligibility` (failing loudly if duplicates exist), adds `updated_at` triggers (`profiles`, `student_profiles`), and adds `embedding_minilm_384 vector(384)` + metadata + partial HNSW index (`IF NOT EXISTS`, compatible with `origin/ml`'s `20261125000001_add_minilm_384_embeddings.sql`).
4. `20261126000003_security_audit_remediation.sql` — Hardens `handle_new_user()` (`SET search_path = public, pg_temp`, `OWNER TO postgres`, deterministic `<id>@no-email.local` fallback for `NULL`/empty emails), revokes direct `authenticated` `UPDATE` on `applications`, restricts `authenticated` `INSERT`/`DELETE` on `applications` to `'drafting'`/`'saved'`, restricts `authenticated` `UPDATE` on `notifications` to `(is_read)`, and restricts `authenticated` `UPDATE` on `profiles` to `(full_name, avatar_url, preferred_language)`.

### 2.2 Local Supabase Startup Workflow
Local database, Auth (`auth.users`, GoTrue), and Storage **must** run via **Supabase CLI** as the single source of truth. `docker-compose.yml` does not run a competing PostgreSQL container; its `api` service connects to Supabase on `host.docker.internal:54322` using `postgresql+asyncpg://postgres:postgres@host.docker.internal:54322/postgres`.

```powershell
# Prerequisites: Docker Desktop + Supabase CLI
supabase start          # Starts Postgres 16 (port 54322), API (54321), Studio, and Auth
supabase db reset       # Applies all supabase/migrations/*.sql and supabase/seed/seed.sql
docker compose up -d    # Starts Redis, FastAPI (connecting to host.docker.internal:54322), and Web
```

---

## 3. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    PROFILES ||--o| STUDENT_PROFILES : has
    PROFILES ||--o| USER_PREFERENCES : configures
    PROFILES ||--o{ APPLICATIONS : submits
    PROFILES ||--o{ RESUMES : owns
    PROFILES ||--o{ AGENT_SESSIONS : runs
    PROFILES ||--o{ APPROVAL_REQUESTS : reviews
    PROFILES ||--o{ CONVERSATIONS : conducts
    PROFILES ||--o{ NOTIFICATIONS : receives

    STUDENT_PROFILES ||--o{ EDUCATION : records
    STUDENT_PROFILES ||--o| CAREER_PASSPORTS : verifies

    OPPORTUNITIES ||--o| OPPORTUNITY_ELIGIBILITY : defines
    OPPORTUNITIES ||--o| OPPORTUNITY_EMBEDDINGS : embeds
    OPPORTUNITIES ||--o{ APPLICATIONS : receives
    OPPORTUNITIES ||--o{ SAVED_OPPORTUNITIES : bookmarked
    OPPORTUNITIES ||--o{ APPROVAL_REQUESTS : targets

    RESUMES ||--o{ RESUME_VERSIONS : tracks
    RESUMES ||--o{ RESUME_CUSTOMIZATIONS : customizes
    OPPORTUNITIES ||--o{ RESUME_CUSTOMIZATIONS : tailored_for

    AGENT_SESSIONS ||--o{ AGENT_EVENTS : emits
    AGENT_SESSIONS ||--o{ APPROVAL_REQUESTS : initiates
    APPROVAL_REQUESTS ||--o{ BROWSER_EXECUTION_LOGS : audits

    CONVERSATIONS ||--o{ CONVERSATION_MESSAGES : contains
```

---

## 4. Detailed Table Specifications, Constraints & Triggers

### 4.1 Profiles & Identity
- **`public.profiles`**: Extends `auth.users` (`id` PK/FK `ON DELETE CASCADE`) with email, full name, avatar, and preferred regional language (`en`, `hi`, `te`, `ta`, `kn`, `ml`, `bn`). Auto-provisioned on signup via `on_auth_user_created` (`public.handle_new_user()`); `updated_at` maintained by `trg_profiles_updated_at`.
- **`public.student_profiles`**: College name, degree, branch, graduation year, CGPA, state, and bio (`user_id` FK `profiles(id)`). `updated_at` maintained by `trg_student_profiles_updated_at`.
- **`public.education`**: Granular academic records (`student_id` FK `student_profiles(id)`).
- **`public.skills`**: Master taxonomy of technical, soft, and domain skills.
- **`public.user_preferences`**: Role filters, preferred locations, remote-only preference, minimum stipend, and notification frequency (`user_id` UNIQUE FK `profiles(id)`).

### 4.2 Career Passport & Grounded Resumes
- **`public.career_passports`**: Verified single-source-of-truth document (`student_id` UNIQUE FK `student_profiles(id)`).
- **`public.resumes`**: Master resume blueprints (`user_id` FK `profiles(id)`).
- **`public.resume_versions`**: Immutable revision snapshots (`resume_id` FK `resumes(id)`).
- **`public.resume_customizations`**: Job-specific tailored resumes (`resume_id` FK `resumes(id)`, `opportunity_id` FK `opportunities(id)`).

### 4.3 Opportunity Intelligence
- **`public.opportunities`**: Ingested internships, scholarships, and jobs with source provenance.
- **`public.opportunity_sources`**: Ingestion source health, scraping frequencies, and provider metadata (backend-only).
- **`public.opportunity_eligibility`**: Deterministic rule sets (`opportunity_id` UNIQUE FK `opportunities(id)` via `uq_opportunity_eligibility_opportunity_id`).
- **`public.opportunity_embeddings`**: Dual-model vector store (`opportunity_id` UNIQUE FK `opportunities(id)`):
  - `embedding vector(768)` — Gemini `text-embedding-004` (`idx_embeddings_vector`, IVFFlat).
  - `embedding_minilm_384 vector(384)` + `embedding_model_id` + `embedding_model_version` — MiniLM (`idx_embeddings_minilm_384_hnsw`, partial HNSW).
- **`public.saved_opportunities`**: Student bookmarks (`UNIQUE (user_id, opportunity_id)`).

### 4.4 Applications, Agents & Human Approval Gate
- **`public.applications`**: Application lifecycle tracking (`UNIQUE (user_id, opportunity_id)` via `uq_applications_user_opportunity`). Authenticated clients may create/delete `'drafting'`/`'saved'` drafts and read their own records; all status transitions (`evaluating` $\rightarrow$ `ready_for_review` $\rightarrow$ `approved` $\rightarrow$ `submitted`), `applied_at`, and `submission_method` updates are executed strictly by FastAPI (`service_role`).
- **`public.agent_sessions`**: LangGraph state machine executions (`user_id` FK `profiles(id)`).
- **`public.agent_events`**: Append-only LangGraph node events (`session_id` FK `agent_sessions(id)`).
- **`public.approval_requests`**: **Human-in-the-Loop Gate**. Client users may `SELECT` their own requests; decisions and status transitions are executed strictly by the backend API (`service_role`) so clients cannot self-approve or alter `payload_summary`.
- **`public.browser_execution_logs`**: Append-only Playwright execution audit trail (`session_id` FK `agent_sessions(id)`).

### 4.5 Multilingual Conversations, Voice & Monitoring
- **`public.conversations` & `public.conversation_messages`**: Chat history (`user_id` FK `profiles(id)`, `conversation_id` FK `conversations(id)`).
- **`public.voice_sessions`**: Voice telemetry and transcripts (`user_id` FK `profiles(id)`).
- **`public.notifications`**: User alerts (`user_id` FK `profiles(id)`).
- **`public.opportunity_monitors`**: Scheduled portal monitors (`user_id` FK `profiles(id)`).
- **`public.analytics_events`**: Funnel telemetry (`user_id` nullable FK `profiles(id)`).

---

## 5. Security & Row Level Security (RLS) Matrix

All 25 `public.*` tables have `ENABLE ROW LEVEL SECURITY`. `service_role` bypasses RLS for backend orchestration, ML indexing, and audit logging.

---

## 6. Backend Async SQLAlchemy & Repository Contracts (`apps/api`)

- **Session Management (`app/db/session.py`):** `DatabaseManager` creates a pooled `AsyncEngine` (`postgresql+asyncpg://`, `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=1800`) initialized in FastAPI `lifespan` and disposed gracefully on shutdown.
- **ORM Models (`app/models/entities.py`):** Maps core tables (`Profile`, `StudentProfile`, `Education`, `CareerPassport`, `Opportunity`, `OpportunityEligibility`, `OpportunityEmbedding`, `Application`, `ApprovalRequest`, `Notification`, `Resume`) with `passive_deletes=True` so PostgreSQL owns cascading deletes and schema DDL remains exclusively in `supabase/migrations/`.
- **Ownership Enforcement (`app/repositories/`):** Because FastAPI's privileged DB role can bypass RLS, every repository method on user-owned tables (`ProfileRepository`, `StudentProfileRepository`, `CareerPassportRepository`, `ApplicationRepository`, `ApprovalRepository`, `NotificationRepository`, `ResumeRepository`) **must** enforce `user_id == current_user.user_id` predicates on all reads, updates, and deletes.
- **Pagination & Vector Search (`OpportunityRepository`):** Uses `(created_at, id)` Base64 keyset cursor pagination and `pgvector` cosine distance (`<=>`) on `embedding_minilm_384` (384-dim) or `embedding` (768-dim).

| Table | `anon` Access | `authenticated` Access | Ownership / Isolation Rule |
| :--- | :--- | :--- | :--- |
| `opportunities`, `opportunity_eligibility`, `skills` | `SELECT` | `SELECT` | Publicly readable catalogs; writes `service_role` only |
| `opportunity_sources`, `opportunity_embeddings` | None | None | Restricted strictly to `service_role` |
| `profiles` | None | `SELECT`, `INSERT`, `UPDATE (full_name, avatar_url, preferred_language)` | `auth.uid() = id` (`email` synced from `auth.users` / `service_role` only) |
| `student_profiles`, `user_preferences`, `saved_opportunities`, `resumes`, `conversations`, `opportunity_monitors` | None | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | `auth.uid() = user_id` |
| `applications` | None | `SELECT`, `INSERT` (draft/saved), `DELETE` (draft/saved) | `auth.uid() = user_id` (`UPDATE` & status transitions `service_role` only) |
| `education`, `career_passports` | None | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | `EXISTS` on `student_profiles.user_id = auth.uid()` |
| `resume_versions`, `resume_customizations` | None | `SELECT`, `INSERT` | `EXISTS` on `resumes.user_id = auth.uid()` |
| `conversation_messages` | None | `SELECT`, `INSERT` | `EXISTS` on `conversations.user_id = auth.uid()` |
| `voice_sessions` | None | `SELECT`, `INSERT` | `auth.uid() = user_id` |
| `notifications` | None | `SELECT`, `UPDATE (is_read)` | `auth.uid() = user_id` (`service_role` inserts) |
| `agent_sessions`, `approval_requests` | None | `SELECT` | `auth.uid() = user_id` (mutations `service_role` only) |
| `agent_events`, `browser_execution_logs` | None | `SELECT` | `EXISTS` on `agent_sessions.user_id = auth.uid()` (append-only `service_role`) |
| `analytics_events` | None | `INSERT` | `WITH CHECK (auth.uid() = user_id)`; reads `service_role` only |
