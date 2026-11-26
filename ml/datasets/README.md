# ML Datasets Guide, Provenance, Schema & Leakage Governance

Every dataset inside **NexteRaS `ml/datasets/`** enforces strict provenance tagging, PII exclusion, schema validation, and leakage prevention. **Zero real student PII and zero fabricated real-world opportunity logs are permitted.**

---

## 1. Local Synthetic Benchmark & Starter Datasets (`ml/datasets/synthetic/`)

| Dataset File | Task | Examples | Languages | Labels | Splits | Known Bias / Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `matching_curriculum_v2.json` | Contrastive Semantic Matching (`minilm-nexteras-v1`) | `88` labeled hard-negative triplets (`48` train, `16` val -> `32` docs, `24` test -> `48` docs) across `8` NexteRaS career domains | English campus bios & formal JDs | `relevance_label` (`1`), hard-negative domain distractors | Disjoint `train` / `val` / `test` (zero ID, title, or summary overlap) | Explicitly synthetic; hard negatives are domain_family-disjoint keyword traps to prevent false negatives |
| `matching_seed_examples.json` | Semantic Matching (`Starter reference set`) | `34` labeled scenarios (`20` train, `6` val, `8` test queries vs `12` corpus docs w/ `4` hard distractors) | English text + Indian locale tags | `relevance_label` (`1`), domain family | Disjoint `train` / `val` / `test` verified by `validate_no_split_leakage()` | Small starter baseline (`1.0` pretrained R@1 ceiling); retained as regression suite |
| `resume_extraction_benchmark.json` | Resume Extraction (`Workstream A`) | `4` synthetic undergraduate resumes (with missing fields & negative controls) | English | Expected scalars, `required_skills`, `forbidden_skills` | Evaluation holdout | Reflects Indian engineering B.Tech / B.E. / MCA layouts; misses multi-column scanned OCR PDFs |
| `eligibility_edge_cases.json` | Deterministic Eligibility (`Workstream D`) | `8` rule boundary scenarios | English | `eligible`, `ineligible`, `needs_more_info`, `unable_to_verify` | Evaluation holdout | Tests B.E./B.Tech equiv, CGPA, %, backlogs, deadlines, citizenship, ambiguous clauses |
| `ranking_benchmark.json` | Opportunity Ranking (`Workstream C`) | `6` candidates (`3` eligible, `1` dup, `1` expired, `1` ineligible) | English | `ideal_grade` (0–3), `expected_excluded` | Evaluation holdout | Tests separation discipline, not statistical click calibration (click logs pending collection) |
| `multilingual_eval_corpus.json` | Multilingual Retrieval (`Workstream B`) | `24` queries across `8` language variants vs `6` English target docs | `en, hi, te, ta, kn, ml, bn` + `hinglish` (`3` queries each) | `target_doc_id` | Cross-lingual eval corpus | Native queries authored cleanly cleanly without noisy slang typos; `3` queries per language gives directional triage only |
| `verification_claims_benchmark.json` | NLI Evidence Consistency (`Workstream E`) | `9` claim-premise pairs (`3` supported, `3` contradicted, `3` insufficient_evidence) | English | `expected_verdict` | Evaluation holdout | Small balanced trio test; real paraphrased resumes have finer metric subtlety |

**Common Safeguards Across All Local Fixtures:**
- **`is_synthetic: true`** present on every top-level JSON file.
- **Zero PII:** Synthetic student names (`Ananya Iyer`, `Rohan Deshmukh`, `Meera Nair`) carry zero real emails, phone numbers, Aadhaar IDs, or student registration numbers; runtime logs automatically apply `redact_pii()`.
- **Leakage Control:** Processed splits (`ml/datasets/processed/`, gitignored) are generated reproducibly via `ml/scripts/prepare_minilm_data.py` with automated `student_id` & `opportunity_id` zero-overlap assertions.

---

## 2. Approved External Datasets (For Post-MVP / Real Training Scaling)
1. **ESCO Taxonomy (European Skills, Competences and Occupations):** CC0 / Public Domain equivalent (~13,800 canonical skills).
2. **Resume Entities for NER (Kaggle):** Apache 2.0 / CC BY 4.0 (token entity boundaries).
3. **AI4Bharat / FLORES-200 Indic Benchmarks:** CC BY / Open research licenses for expanded 7-language retrieval testing before claiming parity.

## 3. Interaction Data Required Before Supervised Ranking (`Workstream C`)
Supervised LightGBM / XGBoost ranking remains explicitly `pending_user_interaction_data`. Before training any ranker:
- Collect at least **`500` anonymized student-opportunity ranking sessions** recording real `clicked`, `saved`, `applied`, or `dismissed` labels (`InteractionTrainingRecord` schema in `ml/src/ranking/supervised_pipeline.py`) partitioned chronologically/by user to avoid leakage.
