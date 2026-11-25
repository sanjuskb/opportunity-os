# NexteRaS — ML Production Deployment & Resource Preparation Guide

**Scope:** Cloud Run / isolated FastAPI worker integration for NexteRaS ML services (CPU-only execution; no production secrets modified or deployed here).

---

## 1. Infrastructure Alignment
Matches `docker-compose.yml` & `docs/deployment/deployment-plan.md`:
- **Web App (`Vercel`):** Next.js 15 frontend — unaffected.
- **Core Backend (`FastAPI` on `Cloud Run / Container`):** Calls ML via clean adapter [apps/api/app/ml/adapter.py](file:///d:/ai%20career%20intelligence%20autonomous%20system/apps/api/app/ml/adapter.py) + [fastapi_adapter.py](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/src/integration/fastapi_adapter.py).
- **Database (`Supabase PostgreSQL + pgvector`):** Existing `vector(768)` untouched; proposed additive `vector(384)` migration prepared in [20261125000001_add_minilm_384_embeddings.sql](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261125000001_add_minilm_384_embeddings.sql).
- **Background Queue (`Redis 7 + ARQ`):** Runs batch embedding, ingestion & NLI verification asynchronously off the hot HTTP request path.
- **Artifact Storage:** Model checkpoints (`ml/artifacts/minilm-nexteras-v1`) live outside Git (private Hugging Face Hub repo or mounted GCS/Supabase volume downloaded once on container startup / Cloud Run volume mount).

---

## 2. Container & Memory Sizing Rules
See [infra/docker/Dockerfile.ml](file:///d:/ai%20career%20intelligence%20autonomous%20system/infra/docker/Dockerfile.ml):
- **CPU PyTorch Only:** Uses `--index-url https://download.pytorch.org/whl/cpu` (avoids ~2.5 GB CUDA wheel bloat).
- **Memory Budget (Google Cloud Run):**
  - **Minimum:** `2 vCPU / 2 GiB RAM` when running **1 resident transformer** (`max_loaded_models=1`, `all-MiniLM-L6-v2` ~320 MB RSS or `paraphrase-multilingual-MiniLM-L12-v2` ~750 MB RSS).
  - **Recommended Production Worker:** `4 vCPU / 4 GiB RAM` when serving both multilingual retrieval and auxiliary NLI verification in worker queues.
- **No Per-Request Model Downloads:** Set `HF_HOME=/var/cache/huggingface` pointing to a warmed image layer or persistent volume, plus `HF_HUB_OFFLINE=1` in locked production once warmed.

---

## 3. Startup, Health, Readiness & Fallback Behavior
- **Liveness Check (`health_and_readiness().status`):** Verifies Python CPU runtime (`cuda_available == False`), config YAML & ModelRegistry validity in `< 10 ms` **without** blocking on Hugging Face downloads (`readiness = "ready_lazy"`).
- **Warmup Option:** Background ARQ workers pre-warm `SemanticMatcher` at startup (`svc.semantic_matcher.encode(["warmup"])`) so first user search does not absorb cold load latency.
- **Unavailable Model Fallback:**
  - If Sanju's custom `ml/artifacts/minilm-nexteras-v1` checkpoint is absent, `ModelRegistry` automatically resolves `sentence-transformers/all-MiniLM-L6-v2` (`using_finetuned_checkpoint: false`).
  - If external model weights cannot download/load (`MLInferenceError`), `match_semantic()` returns `([], "fallback_unavailable")`, allowing deterministic eligibility (`M06`) + keyword/SQL ranker to keep functioning seamlessly.
  - **Human Approval Invariant (`M11`):** Neither semantic scores nor NLI verdicts can dispatch applications autonomously (`requires_human_approval == True`).
