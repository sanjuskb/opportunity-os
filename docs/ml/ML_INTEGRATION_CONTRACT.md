# NexteRaS — ML Integration Contract (FastAPI, LangGraph & pgvector)

**Status:** Proposed Integration Specification (Do not modify `apps/api/`, `supabase/migrations/`, `sanju`, `develop`, `main`, or `ramaraju` without team sign-off).

---

## 1. Decoupling Principle

All ML model loading, tokenization, embedding generation, and deterministic eligibility evaluation must reside inside `ml/src/` (exposed through clean Python service classes such as `ml.src.matching.SemanticMatcher`), **never** embedded inline inside FastAPI route handlers (`apps/api/app/api/v1/`).

```text
FastAPI Route (/api/v1/eligibility/evaluate)
   └──► apps/api/app/services/ml/ (thin dependency-injected adapter)
           ├──► DeterministicEligibilityEngine  (batch, CGPA, degree -> bool + reasons)
           └──► SemanticMatcher (all-MiniLM-L6-v2 base vs fine-tuned checkpoint)
```

---

## 2. CRITICAL Schema Alignment Notice (`pgvector`: `vector(768)` vs `384`)

During the audit of [supabase/migrations/20261123000001_initial_schema.sql](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261123000001_initial_schema.sql) (line 124):
- Existing table `public.opportunity_embeddings` defines:
  ```sql
  embedding vector(768)
  ```
  designed for Google Gemini `text-embedding-004` (`768` dimensions).
- Meanwhile, `sentence-transformers/all-MiniLM-L6-v2` outputs **`384`-dimensional vectors**.

### Required Team Decision Before Connecting DB Vector Search
We must **NOT** silently alter `initial_schema.sql`. Choose one clean option with Ramaraju before integration:
- **Option A (Dual Vector Column / Separate Local Index):** Add a lightweight nullable migration later (`ALTER TABLE public.opportunity_embeddings ADD COLUMN embedding_minilm vector(384);`) so cloud Gemini `vector(768)` and offline CPU `vector(384)` coexist cleanly with separate IVFFlat/HNSW indexes.
- **Option B (Two-Stage Architecture):** Use PostgreSQL `pgvector(768)` (or deterministic filters + `BAAI/bge-base-en-v1.5` 768-dim offline) for candidate retrieval, and use fine-tuned `all-MiniLM-L6-v2` (384-dim) in FastAPI in-memory / local NumPy candidate scoring during top-50 re-scoring.

---

## 3. Proposed Python Interfaces for Backend Consumption

### A. Deterministic + Semantic Match Output (Aligns with `apps/api/app/schemas/common.py` `EligibilityCheckResponse`)
```python
class MatchComparisonResult(BaseModel):
    opportunity_id: str
    is_eligible: bool                     # Strictly deterministic rule output (0 ML override)
    deterministic_checks: dict[str, bool] # batch_matched, degree_matched, cgpa_matched
    semantic_score: float                 # Cosine similarity [0.0, 1.0] from SemanticMatcher
    overall_match_score: float            # 0.0 to 100.0 (forced 0 if is_eligible is False)
    matched_skills: list[str]
    missing_skills: list[str]
    model_version: str                    # e.g. "all-MiniLM-L6-v2" or "minilm-nexteras-v1"
```

### B. A/B Base vs Fine-Tuned Model Switch
- Controlled via backend environment config (`ML_MATCHING_MODEL_PATH`), defaulting safely to pretrained `sentence-transformers/all-MiniLM-L6-v2` when `ml/artifacts/minilm-nexteras-v1` is absent in deployment containers.

### C. LangGraph Node Mapping (`docs/agents/langgraph-workflows.md`)
- `EligibilityWorkflow.HardRuleCheckNode` -> deterministic Python rules only.
- `EligibilityWorkflow.SkillGapScorerNode` -> `SemanticMatcher` + ESCO skill normalizer.
- `ResumeWorkflow.HumanReviewNode` -> `NLIHallucinationGate` (`cross-encoder/nli-deberta-v3-small`) checks tailored resume bullets strictly against verified Career Passport facts before surfacing approval card (`M11`).
