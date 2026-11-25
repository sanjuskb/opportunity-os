# NexteRaS — ML Architecture Inventory & Readiness Audit

**Branch:** `ml` (branched cleanly from `origin/sanju` at `a8022a3`)  
**Scope:** Strictly grounded audit of designed vs. implemented NexteRaS ML capabilities and architectural boundaries.

---

## 1. Intelligence Layer Boundaries (Non-Negotiable Separation)

| Intelligence Tier | Owns | Must Never Do |
| :--- | :--- | :--- |
| **Deterministic Python Logic** | CGPA inequality, graduation year/batch check, degree/branch exact & synonym mapping, schema validation, hard eligibility gating | Use probabilistic thresholding to guess or override hard prerequisites |
| **Specialized Local ML (`ml/`)** | Dense semantic embeddings (`all-MiniLM-L6-v2` 384-dim), ESCO skill linking, NLI bullet grounding, calibrated multi-factor / gradient-boosted ranking (once labeled click data exists) | Fabricate factual credentials or replace deterministic rules |
| **Gemini / Frontier LLM** | Conversational reasoning, structured JD/resume JSON extraction, plain-language match explanations, multilingual coaching, LangGraph tool selection | Bypass eligibility gates or hallucinate unverified projects |

---

## 2. Six Intended ML Capabilities — Current Audit Status

| # | Capability | Candidate Approach / Model | Inputs | Outputs | Status on `ml` Branch Start (`a8022a3`) | Planned Implementation Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Semantic Opportunity Matching** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim CPU baseline) + fine-tuned bi-encoder (`MultipleNegativesRankingLoss`) | Normalized Student Profile text & Opportunity Passage text | 384-dim unit vectors, cosine scores, top-K matches | Config & scaffold (`ml/model_configs/baseline_matching.yaml`), `pgvector` schema uses `vector(768)`; **starter CPU training & eval code now prepared** | Personal 3-hr CPU fine-tuning (`minilm-nexteras-v1`), then decoupled inference adapter |
| **2** | **Resume Skill Extraction** | PyMuPDF deterministic text read + Pydantic schema-enforced structured extraction (Gemini Flash JSON mode API or local GLiNER `urchade/gliner_base-v2.1` + rule normalizer) | Raw resume text / PDF blocks | Validated `ExtractedResume` JSON (`skills`, `education`, `projects`, `experience`, `certifications`) | Designed in `docs/ml/ML_MODEL_SELECTION_AND_EVALUATION.md`; **not yet coded** | Overnight Task A (`ml/src/extraction/`) |
| **3** | **Opportunity Ranking** | Hard deterministic gate $M_{\text{elig}} \times (w_1 S_{\text{sem}} + w_2 S_{\text{skills}} + w_3 S_{\text{urgency}} + w_4 S_{\text{loc}})$; upgrade to LightGBM/XGBoost **only once interaction labels exist** | Eligible candidate-opportunity pairs + semantic scores + deadline | Ordered opportunity feed + score breakdown | Formula designed in `ML_MODEL_SELECTION_AND_EVALUATION.md`; `best_achieved: null` | Overnight Task C: transparent deterministic-gated heuristic baseline first; document labeling needs for GBDT |
| **4** | **Eligibility Assessment** | Deterministic Python rule evaluator (`batch`, `degree`, `CGPA`, `branch`, normalized skill match) + structured prerequisite extractor | Student Career Passport + extracted JD prerequisites | `EligibilityResult` (`is_eligible`, boolean flags, traceable reason strings) | Frontend TypeScript explainer exists in `mockStore.ts`; Python engine **not yet implemented** | Overnight Task D (`ml/src/eligibility/`) returning traceable reasons |
| **5** | **Multilingual Text Understanding** | Pretrained multilingual encoder / normalization test suite (`paraphrase-multilingual-MiniLM-L12-v2` or Indic-capable encoder) + Gemini translation/voice | Text / mixed Hinglish / regional queries across `en, hi, te, ta, kn, ml, bn` | Multilingual query embeddings, language validation report | **Not tested** on Python ML side; frontend locale list supports 7 codes | Overnight Task B: audit all 7 locales individually without unverified support claims |
| **6** | **Resume Analysis & Hallucination Gate** | Reused pretrained NLI cross-encoder (`cross-encoder/nli-deberta-v3-small`) checking Career Passport premise vs tailored resume bullet hypothesis | Verified Career Passport items + tailored resume bullets | Entailment score, `is_grounded` flag, unsupported-claim warning | Modeled as `M09` in frontend Agent Control Center; **no Python inference module yet** | Overnight Task E (`ml/src/extraction/nli_gate.py`) reusing pretrained NLI without unnecessary custom training |

---

## 3. Existing Codebase Surfaces Inspected
- **Frontend (`sanju`, untouched):** 29 Next.js App Router pages, `Agent Control Center` (`M01`–`M14`), `packages/shared-types/src/index.ts` (`StudentProfile`, `Opportunity`, `EligibilityResult`, `IndianLanguage`).
- **Backend (`apps/api`, untouched):** FastAPI `app/main.py` with `/api/v1/health` and empty `/api/v1/opportunities` stub (`router.py`), Pydantic schemas (`app/schemas/common.py`: `OpportunityResponse`, `EligibilityCheckRequest`, `EligibilityCheckResponse`), empty placeholder directory `apps/api/app/ml/__init__.py`.
- **Database (`supabase/migrations/20261123000001_initial_schema.sql`, untouched):** 25 PostgreSQL tables including `opportunity_embeddings (embedding vector(768))` indexed with `ivfflat (vector_cosine_ops)`.
- **LangGraph Workflows (`docs/agents/langgraph-workflows.md`):** Planned workflow graphs (`DiscoveryWorkflow`, `EligibilityWorkflow`, `ResumeWorkflow`, `ApplicationWorkflow`) and Pydantic tool schemas.
