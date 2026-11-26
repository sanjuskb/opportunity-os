# NexteRaS — ML Architecture Inventory & Final Status Matrix

**Branch:** `ml`  
**Audit Date:** 2026-11-25  
**Status Legend (Strictly Applied):**
- `IMPLEMENTED`: Production/modular code exists on `ml`.
- `TESTED`: Automated `pytest` suite passes for the component.
- `EVALUATED`: Measured on a documented local CPU benchmark dataset.
- `INTEGRATED`: Compatibility adapter built and test-verified against `apps/api` & LangGraph shapes (awaiting live Postgres/Gemini credentials).
- `DEPLOYED`: Actually deployed to live Cloud Run / Vercel / Supabase (none yet).
- `PENDING`: Intentionally awaiting personal execution or external data/integration.

---

## 1. Reconciliation Inventory Table (Part 4 Requirement)

| Capability | Existing Implementation (Start of `ml`) | Remaining Work Completed on `ml` | Chosen Approach | Current Status |
| :--- | :--- | :--- | :--- | :--- |
| **A. Resume Skill & Profile Extraction** | Blueprint only in `ML_MODEL_SELECTION_AND_EVALUATION.md` | Implemented Pydantic schemas, canonical CS/ECE skill/degree/branch taxonomy, word-boundary evidence extraction, malformed LLM JSON recovery & hallucination guard (`ml/src/extraction/`) | Deterministic rule parser + pluggable `StructuredLLMBackend` (no key hardcoding) | **IMPLEMENTED, TESTED, EVALUATED** (`1.0` Skill F1 / `0` hallucinated on synthetic benchmark; real PDF LLM eval `PENDING` API key) |
| **B. Multilingual Text Understanding** | Only UI locale enum `IndianLanguage` (`en, hi, te, ta, kn, ml, bn`) | Implemented non-destructive NFC script preprocessor (`ml/src/multilingual/preprocessing.py`), lazy `paraphrase-multilingual-MiniLM-L12-v2` service + confidence/locale fallback routing, and 8-locale audit | Pretrained `paraphrase-multilingual-MiniLM-L12-v2` + explicit `EMPIRICALLY_WEAK_DIRECT_LOCALES` fallback to translation/LLM | **IMPLEMENTED, TESTED, EVALUATED** (Strong `en`/`hinglish` 1.0 R@1; `hi` 0.67; `ta`/`bn`/`kn`/`te`/`ml` routed to translation fallback) |
| **C. Opportunity Ranking Engine** | Mathematical weights drafted in blueprint only | Implemented deduplication, expiry filtering, eligibility separation (`ranked` vs `excluded`), explainable score contributions, & supervised GBDT feature/readiness pipeline (`ml/src/ranking/`) | Rule-gated linear baseline; LightGBM/XGBoost deferred until `>= 500` real user interaction sessions exist | **IMPLEMENTED, TESTED, EVALUATED** (`1.0` P@1 / nDCG@3 on synthetic benchmark; supervised GBDT `PENDING` real telemetry) |
| **D. Deterministic Eligibility Engine** | Client-side mock helper in `apps/web/src/lib/mock-data/` | Implemented JD requirement parser (`parser.py`) + strict deterministic evaluator covering degree equivalence, branch, batch, academic year, CGPA/%, backlogs, deadline, citizenship & missing-info tracking (`ml/src/eligibility/`) | Pure deterministic logic returning `eligible \| ineligible \| needs_more_info \| unable_to_verify` with audit spans | **IMPLEMENTED, TESTED, EVALUATED** (`1.0` exact accuracy, `0.0` false eligible rate on 8 edge cases) |
| **E. Evidence Verification (NLI)** | Modeled visually as `M09` node in Agent Control Center | Implemented replaceable `EvidenceVerificationService` supporting lazy `cross-encoder/nli-deberta-v3-small` + lightweight lexical fallback, strict thresholds, and advisory invariants (`ml/src/verification/`) | Auxiliary pretrained NLI cross-encoder (`is_advisory_only=True`, never auto-approves external actions) | **IMPLEMENTED, TESTED, EVALUATED** (`0.8889` accuracy, `0.0` false-supported rate with DeBERTa-v3-small; async worker binding `PENDING`) |
| **F. Semantic Matching & Personal Lab** | `personal_minilm_cpu.yaml`, `train_minilm.py`, starter splits | Preserved Sanju's training kit untouched; upgraded `SemanticMatcher` with lazy loading, registry checkpoint resolution & automatic pretrained fallback (`ml/src/matching/`) | `sentence-transformers/all-MiniLM-L6-v2` (`384`-dim CPU) + placeholder `ml/artifacts/minilm-nexteras-v1` | **PRETRAINED BASELINE EVALUATED & INTEGRATED** (`1.0` synthetic R@1; personal fine-tuning **PENDING Sanju**) |
| **G. Inference Service, Registry & DB Compat** | Empty `apps/api/app/ml/` stub; `pgvector(768)` schema conflict | Built `ModelRegistry`, `ResourceManagedModelCache(max_loaded_models=1)`, `redact_pii`, `NexteRaSMLService`, `NexteRaSLangGraphAdapter`, `apps/api/app/ml/adapter.py`, `Dockerfile.ml`, & proposed additive `vector(384)` SQL migration | Modular clean boundaries decoupled from FastAPI routes; forward-only `20261125000001_add_minilm_384_embeddings.sql` | **IMPLEMENTED, TESTED, INTEGRATION-READY** (`DEPLOYED: PENDING` PR review & staging DB/Cloud Run deploy) |
