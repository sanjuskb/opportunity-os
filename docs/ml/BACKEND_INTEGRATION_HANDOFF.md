# NexteRaS Backend Integration Handoff (`ml` -> `ramaraju` / `develop`)

**Source Branch:** `ml` (HEAD will be recorded in final commit)  
**Target Coordinator:** Ramaraju (Backend, Supabase & Infrastructure Lead)  
**Rule Followed:** Neither `ramaraju`, `develop`, `sanju`, nor `main` was modified. All FastAPI integration adapters on `ml` degrade cleanly when `ml.src` is absent in slim API-only builds.

---

## 1. Files Modified / Added in `apps/api/` & `supabase/` on Branch `ml`

| File Path | Change Summary | Impact on Slim API CI (`uv sync --extra dev`) |
| :--- | :--- | :--- |
| `apps/api/app/api/v1/ml.py` | **NEW** — Adds `/api/v1/ml/health`, `/extract-resume`, `/multilingual/understand`, `/semantic-match`, `/rank-opportunities`, `/verify-evidence`, `/recommend-pipeline` + `/api/v1/eligibility/evaluate` | Safe (`is_ml_subsystem_available()` returns `False` -> RFC 7807 `503` JSON; passes `ruff`, `mypy --strict`, `pytest`) |
| `apps/api/app/schemas/ml.py` | **NEW** — Typed Pydantic v2 request/response DTOs matching TypeScript `@opportunity-os/shared-types` & `CROSS_TEAM_CONTRACT_REGISTER.md` | Pure Pydantic — zero heavy imports |
| `apps/api/app/api/v1/router.py` | Mounts `ml_router` (`/ml`) and `eligibility_router` (`/eligibility`) under `/api/v1` while leaving `/health` & `/opportunities` intact | Verified passing |
| `apps/api/app/ml/adapter.py` | Calls `NexteRaSMLService.from_env()` cleanly when `ml.src` is present, raising `MLSubsystemUnavailableError` when absent | Safe lazy import inside function |
| `apps/api/app/core/config.py` | Adds optional ML runtime env vars (`ML_MATCHING_MODEL_PATH`, `ML_MAX_LOADED_MODELS`, `TORCH_NUM_THREADS`, `ENABLE_PRETRAINED_NLI`) with safe defaults | Backward-compatible with existing `.env` |
| `apps/api/tests/integration/test_ml_routes.py` | **NEW** — Verifies slim-API `503` fallback, stubbed ML routing, and live ML route calls when `ml.src` is mounted | Passes under both `apps/api/.venv` and `ml/.venv` |
| `supabase/migrations/20261125000001_add_minilm_384_embeddings.sql` | Additive forward-only columns (`embedding_minilm_384 vector(384)`, `embedding_model_id`, `embedding_model_version`) + partial HNSW index | **NOT applied remotely**; preserves `initial_schema.sql` `vector(768)` untouched |

---

## 2. Exact Steps Required From Backend Teammate (`ramaraju`)

1. **Container / Packaging Decision (Choose Monorepo vs Sidecar):**
   - **Option 1 (Unified CPU Worker Image):** Copy `ml/` alongside `apps/api/` (see `infra/docker/Dockerfile.ml`) and install CPU PyTorch + `ml/requirements.txt` so `/api/v1/ml/*` and `/api/v1/eligibility/evaluate` run in-process for hackathon MVP.
   - **Option 2 (Microservice Split):** Run `ml/` as a dedicated internal Cloud Run service (e.g., `ml-worker:8001` with 2–4 GiB RAM) and have `apps/api` proxy heavy inference (`/recommend-pipeline`, `/verify-evidence`) via `httpx`.
2. **Database Vector Search Alignment (`pgvector`):**
   - Review and approve [20261125000001_add_minilm_384_embeddings.sql](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261125000001_add_minilm_384_embeddings.sql) before running `supabase db push` in staging.
   - When querying `public.opportunity_embeddings`:
     - Filter by `WHERE embedding_minilm_384 IS NOT NULL AND embedding_model_id = $1` when scoring with `minilm-nexteras-v1` / `all-MiniLM-L6-v2` (384-dim).
     - NEVER compare `embedding` (`vector(768)`) against `embedding_minilm_384` (`vector(384)`).
3. **Async Queue Offloading (`Redis + ARQ`):**
   - Keep **`ENABLE_PRETRAINED_NLI=false`** on synchronous HTTP web pods (uses lightweight lexical verifier `~2 ms`, preventing `~1.05 GB` RSS + multi-second CPU blocks on user requests).
   - Run **`ENABLE_PRETRAINED_NLI=true`** only inside background ARQ workers (`max_concurrency=1`) when verifying tailored resumes prior to surfacing the `M11` approval modal (`public.approval_requests`).
4. **LangGraph & Human Approval Gate Wiring:**
   - Wire your Supabase-backed LangGraph checkpointer (`AsyncPostgresSaver`) into `ml.src.integration.langgraph_adapter.build_nexteras_career_workflow(ml_service, checkpointer=..., use_interrupt=True)` or invoke individual node adapters (`eligibility_hard_rule_node`, `opportunity_ranking_node`, `resume_evidence_guardrail_node`).
   - Preserve the `M11` invariant: never dispatch Playwright submission or outreach unless `human_approval_decision == "approved"` is verified from `public.approval_requests`.
5. **External Credentials to Inject in Deployment Secrets (Never Git):**
   - `GEMINI_API_KEY`: Enables `GeminiStructuredLLMBackend` & `GeminiTranslationFallbackBackend` automatically via `NexteRaSMLService.from_env()`.
   - `OLOSTEP_API_KEY`, `CRUSTDATA_API_KEY`: Needed when replacing mocked listings with live web discovery.
   - `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`: Required for live Postgres + RLS + ARQ integration.
