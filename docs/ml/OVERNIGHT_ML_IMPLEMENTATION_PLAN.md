# NexteRaS — Overnight 12-Hour ML Implementation Plan (`ml` Branch)

**Owner for Execution After Personal 3-Hr Training Session:** Antigravity (on `ml` branch only)  
**Target Hardware Constraints:** Windows CPU-only (`i5-1334U`, `Intel Iris Xe`, `15.64 GB` RAM) — keep models compact (`<= 180M` params on CPU) or API-backed where justified, with strict schema validation and pytest coverage.

---

## Implementation Queue (Sections 6.A – 6.G)

### Task A — Resume Skill & Profile Extraction (`ml/src/extraction/`)
- **Goal:** Parse raw text/PDF resumes cleanly into validated Pydantic schemas (`ExtractedResume`: `skills`, `education`, `projects`, `experience`, `certifications`, `technologies`).
- **Approach (No Unnecessary From-Scratch Training):**
  - Stage 1: Clean text + section normalization (`re` / deterministic section headers, PyMuPDF if local PDF support added).
  - Stage 2: Structured extraction interface supporting **Gemini JSON Mode** (cloud API when `GEMINI_API_KEY` set) AND a local CPU-compatible **offline baseline (`skill dictionary + regex + optional GLiNER`)** with strict fallback error handling and malformed-JSON recovery.
- **Tests:** Malformed text, Indian CGPA (`8.82/10`) vs percentage (`84%`) normalization, empty sections.

### Task B — Multilingual Text Understanding Audit (`ml/src/multilingual/`)
- **Goal:** Evaluate coverage across all **7 claimed NexteRaS locales**: `en` (English), `hi` (Hindi), `te` (Telugu), `ta` (Tamil), `kn` (Kannada), `ml` (Malayalam), `bn` (Bengali) — plus Hinglish code-switching.
- **Approach:**
  - Compare `all-MiniLM-L6-v2` (English-trained; expected weak on Indic scripts) against pretrained **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** (~`118M` params, runs on CPU!).
  - Author clean per-language test fixtures (`ml/datasets/synthetic/multilingual_eval_prompts.json`) covering **all 7 scripts + transliterated Hinglish**.
  - **Strict Honesty Rule:** Output exact per-language Recall/Cosine scores (`en, hi, te, ta, kn, ml, bn`). Flag any language scoring below threshold honestly instead of claiming blanket 7-language parity.

### Task C — Opportunity Ranking (`ml/src/ranking/`)
- **Goal:** Transparent multi-factor ranking strictly gated by deterministic eligibility (`M_elig` = 0 discards disqualified roles unless user opts into "show near-miss gaps").
- **Data Audit Decision:** Since **no large logged student click/application interaction dataset exists yet**, do **not** train an overfit synthetic LightGBM/XGBoost ranker.
  - Implement a **clean, inspectable deterministic-gated linear ranker** (`Semantic * 0.45 + SkillOverlap * 0.35 + DeadlineUrgency * 0.10 + LocationMatch * 0.10`) with weight explanations per item.
  - Add a documented GBDT/LambdaMART training interface + exact telemetry logging schema required before XGBoost/LightGBM becomes justified (`>= 1,000` labeled student-opportunity impression/click/apply sessions).

### Task D — Deterministic Eligibility Engine (`ml/src/eligibility/`)
- **Goal:** Zero-hallucination hard rule verification traceable back to exact opportunity requirements.
- **Checks:**
  - `graduation_year` membership (`student.graduation_year in opp.eligible_batches`)
  - `degree` canonical normalization (`B.Tech` ↔ `B.E.`, `Dual Degree`, `M.Tech`, `MCA`)
  - `min_cgpa` numeric check (supporting 10-point CGPA vs normalized %)
  - `branch` normalization & skill gap intersection (`matched_skills`, `missing_skills`)
  - Traceable audit payload quoting exact violated rule threshold.

### Task E — Resume Analysis & Hallucination NLI Gate (`ml/src/verification/`)
- **Goal:** Verify whether synthesized resume bullet points are factually entailed by verified Career Passport records (`M09` Hallucination NLI Gate).
- **Approach (Zero Custom Training Needed):** Reuse pretrained **`cross-encoder/nli-deberta-v3-small`** (or lightweight heuristic + NLI wrapper) with clear threshold audit, returning `entailment_score`, `contradiction_score`, and `flagged_unsupported_claims`.

### Task F — Decoupled Matching & Inference Service Layer (`ml/src/matching/`)
- **Goal:** Unified `SemanticMatcher` + `NexteRaSMatchPipeline` allowing A/B toggle between `sentence-transformers/all-MiniLM-L6-v2` (base) and `ml/artifacts/minilm-nexteras-v1` (fine-tuned), strictly isolated from FastAPI HTTP handlers (see `ML_INTEGRATION_CONTRACT.md`).

### Task G — Standardized Evaluation Harness & Reports (`ml/scripts/`, `ml/tests/`, `ml/experiments/`)
- Unify dataset schema docs, train/val/test leakage checks, Precision/Recall/MRR@10/nDCG@10/latency reporting across all components, automated `pytest` verification (`ml/tests/`), and honest Markdown/JSON evaluation summaries with documented limitations.

---

## Overnight Acceptance Criteria
1. Every module has deterministic unit tests runnable completely offline on CPU (`pytest ml/tests`).
2. Model-heavy evaluation scripts support `--limit` / CPU timing instrumentation and never alter frontend (`apps/web`), `sanju`, `develop`, `main`, or `ramaraju`.
3. `ml/evaluation/benchmarks.json` updated cleanly with real measured baseline/post metrics **only** for components genuinely executed on verified splits (leaving unrun external benchmarks explicitly marked `"pending_dataset"`).
