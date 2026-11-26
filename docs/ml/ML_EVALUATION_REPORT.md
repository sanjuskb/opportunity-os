# NexteRaS — Reproducible CPU ML Evaluation Report

**Executed on:** Windows 11 · ASUSTeK Vivobook X1504VA (`13th Gen Intel Core i5-1334U`, `Intel Iris Xe` CPU-only, `16.79 GB` decimal / `15.64 GiB` RAM)  
**Environment:** `ml/.venv` · Python `3.11.16` · `torch==2.15.0+cpu` (`CUDA_AVAILABLE: False`) · `sentence-transformers==6.3.0` · `transformers==5.24.1`  
**Machine-Readable Output:** [latest_evaluation_report.json](file:///d:/ai%20career%20intelligence%20autonomous%20system/ml/evaluation/latest_evaluation_report.json)  
**Benchmark Caveat:** All local measurements below run on explicitly labeled **synthetic benchmarks** (`is_synthetic: true`). They verify pipeline behavior, safety guardrails, and comparative CPU model characteristics—not production accuracy across live portals. Personal fine-tuning of `all-MiniLM-L6-v2` remains `PENDING_USER_EXECUTION` under Sanju's ownership.

---

## 1. Resume Extraction (`Workstream A`)
- **Active Engine Evaluated:** `deterministic-rule-parser-v1` (zero neural weight download, `< 35 ms` CPU total)
- **Dataset:** `nexteras_resume_extraction_benchmark` (`4` anonymized synthetic engineering resumes)
- **Measured Results:**
  - `schema_validity_rate`: **`1.0000`** (`4/4`)
  - `scalar_exact_match_accuracy`: **`1.0000`** (`degree`, `branch`, `graduation_year`, `cgpa`/`percentage`, `full_name` including missing-name negative control)
  - `skill_precision`: **`1.0000`**, `skill_recall`: **`1.0000`**, `skill_f1`: **`1.0000`**
  - `unsupported_extraction_count`: **`0`** (zero forbidden skills hallucinated)
  - `total_latency_ms`: **`33.8 ms`** (`Process RSS: 205.6 MB`)
- **Known Limitations:** Handles structured section headers cleanly; multi-column PDF typography or uncatalogued niche tools require pluggable `StructuredLLMBackend` (Gemini JSON mode) refinement.

---

## 2. Deterministic Eligibility Engine (`Workstream D`)
- **Active Engine Evaluated:** `deterministic-rule-engine-v1`
- **Dataset:** `nexteras_eligibility_edge_cases` (`8` edge cases: B.E./B.Tech equivalence, CGPA cutoff, missing CGPA, active backlogs, expired deadline, percentage normalization, ambiguous clearance clause, explicit citizenship rule)
- **Measured Results:**
  - `exact_outcome_accuracy`: **`1.0000`** (`8/8`)
  - `false_eligible_rate`: **`0.0000`** (`0`)
  - `false_ineligible_rate`: **`0.0000`** (`0`)
  - `unknown_and_unverified_handling_rate`: **`1.0000`** (`needs_more_info` & `unable_to_verify` never marked eligible)
  - `explanation_traceability_rate`: **`1.0000`** (every decision rule carries `evidence_source` and `reason`)
  - `total_latency_ms`: **`0.75 ms`**

---

## 3. Constrained Opportunity Ranking Baseline (`Workstream C`)
- **Active Engine Evaluated:** `deterministic-weighted-ranker-v1`
- **Dataset:** `ranking_benchmark.json` (`6` candidate entries: `3` distinct eligible + `1` duplicate + `1` expired + `1` high-similarity ineligible)
- **Measured Results:**
  - `precision_at_1`: **`1.0000`** (`rk-top-01` scored `92.36`, `rk-mid-02` `63.38`, `rk-low-03` `25.53`)
  - `ndcg_at_3`: **`1.0000`**
  - `eligibility_violations_in_ranked`: **`0`** (high-similarity `0.97` ineligible & `0.95` expired candidates cleanly segregated into `.excluded`)
  - `duplicates_removed`: **`1`**, `expired_removed`: **`1`**
  - `deterministic_repeat_consistency`: **`true`** (`0.31 ms` CPU latency)
- **Supervised ML Readiness:** `supervised_training_status = pending_user_interaction_data` (requires `>= 500` real interaction sessions; zero click data fabricated).

---

## 4. Semantic Matching Pretrained Baseline (`Workstream F` — Personal Training Preserved)
- **Model Evaluated:** `sentence-transformers/all-MiniLM-L6-v2` (pretrained only; **NOT fine-tuned here**)
- **Dataset:** Held-out synthetic split (`8` unseen queries vs `12` unseen opportunities including `4` keyword-sharing hard distractors)
- **Measured Results:**
  - `recall_at_1`: **`1.0000`**, `mrr_at_10`: **`1.0000`**, `ndcg_at_10`: **`1.0000`**
  - `mean_pos_neg_margin`: **`+0.2009`**
  - `encode_latency_per_query_ms`: **`58.36 ms`** (`model_load_ms: 23.7s` cold load w/ HF check; `peak_rss_mb: 615.3 MB`, `+163.2 MB` delta)
- **Why Personal Training Remains Meaningful:** While off-the-shelf MiniLM already separates curated domain pairs at top-1, `+0.2009` cosine margin leaves room to sharpen Indian engineering phrasing & subtle domain distinctions during Sanju's 3-hour fine-tuning lab (`ml/scripts/train_minilm.py`).

---

## 5. Multilingual Cross-Lingual Retrieval Audit (`Workstream B`)
- **Model Evaluated:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dim, Apache-2.0)
- **Dataset:** `nexteras_multilingual_7_languages_eval` (`24` queries: `3` per language across `en, hi, te, ta, kn, ml, bn, hinglish` against `6` English NexteRaS opportunities)
- **Resource Cost:** Cold load `63.8s`, inference `646.9 ms` (`24` queries + `6` docs), **`peak_rss_mb: 1215.6 MB`** (`+1010.5 MB` RSS).

| Language Variant | Recall@1 | Recall@3 | MRR@10 | nDCG@10 | Pos-Neg Cosine Margin | Direct Retrieval Adequacy |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`en` (English)** | `1.0000` | `1.0000` | `1.0000` | `1.0000` | `+0.2063` | Adequate directly |
| **`hinglish` (Romanized Mix)** | `1.0000` | `1.0000` | `1.0000` | `1.0000` | `+0.2051` | Adequate when tech keywords present (still supports fallback) |
| **`hi` (Hindi)** | `0.6667` | `0.6667` | `0.7500` | `0.8102` | `+0.1037` | Moderate (`2/3` top-1) |
| **`ta` (Tamil)** | `0.6667` | `0.6667` | `0.7500` | `0.8102` | `-0.0326` | **Weak margin — Fallback recommended** |
| **`bn` (Bengali)** | `0.3333` | `0.6667` | `0.5667` | `0.6726` | `-0.0582` | **Weak — Fallback required** |
| **`kn` (Kannada)** | `0.3333` | `0.6667` | `0.5667` | `0.6726` | `-0.0368` | **Weak — Fallback required** |
| **`te` (Telugu)** | `0.0000` | `0.6667` | `0.4167` | `0.5642` | `-0.0644` | **Weak — Fallback required** |
| **`ml` (Malayalam)** | `0.0000` | `0.3333` | `0.2778` | `0.4538` | `-0.0961` | **Unsupported directly — Fallback required** |
| **Overall (`24` queries)** | `0.5000` | `0.7083` | `0.6660` | `0.7480` | `+0.0284` | — |

**Engineering Decision:** Empirical measurement proves `paraphrase-multilingual-MiniLM-L12-v2` **cannot** claim reliable zero-shot Dravidian/Bengali cross-lingual retrieval to English postings on its own (`bn`, `kn`, `ml`, `ta`, `te` show negative mean top-1 cosine margins). Therefore `MultilingualUnderstandingService` explicitly encodes `EMPIRICALLY_WEAK_DIRECT_LOCALES = {"bn", "kn", "ml", "ta", "te"}` and routes those + Hinglish queries through the pluggable Gemini / translation fallback (`TranslationFallbackBackend`) while keeping `original_text` preserved verbatim!

---

## 6. Auxiliary Evidence & Claim Verification (`Workstream E`)
- **Dataset:** `nexteras_verification_claims_benchmark` (`9` pairs: `3` supported, `3` contradicted, `3` insufficient_evidence)

| Verification Backend | Overall Acc. | False Supported Rate | Supported Acc. | Contradicted Acc. | Insufficient Acc. | Latency (Total) | Peak RSS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `lexical-number-and-overlap-fallback-v1` | `0.7778` | **`0.0000`** | `0.3333` | `1.0000` | `1.0000` | `2.02 ms` | `205.7 MB` |
| `cross-encoder/nli-deberta-v3-small` | **`0.8889`** (`8/9`) | **`0.0000`** | **`1.0000`** | **`1.0000`** | `0.6667` | `67.42 s` (w/ load) | `1054.6 MB` |

**Engineering Decision:** Pretrained `cross-encoder/nli-deberta-v3-small` accurately distinguished paraphrased support (`0.994–0.998`) and contradictions (`0.980–0.999`) with **`0%` false-supported errors**, while flagging `ver-amb-03` (`"requires Python"` vs `"requires 5 years Go"`) as contradicted (`0.9939`) rather than neutral. Its ~`1.05 GB` peak RSS and multi-second CPU runtime confirm it must run asynchronously inside ARQ worker tasks / single-resident lazy cache (`is_advisory_only=True`, never sole authority for `M11` human approval).
