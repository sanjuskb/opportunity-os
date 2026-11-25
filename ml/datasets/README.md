# ML Datasets Guide, Schema & Split Provenance

All datasets used in **NexteRaS** follow strict provenance labeling, schema validation, PII stripping, and leakage-free splitting.

---

## 1. Starter Dataset: `synthetic/matching_seed_examples.json`

- **Flag:** `"is_synthetic": true` (validated in Pydantic by `MatchingPairRecord`).
- **Purpose:** Safe, readable synthetic Indian collegiate employability pairs for Sanju's hands-on CPU fine-tuning session on `sentence-transformers/all-MiniLM-L6-v2`.
- **Important Caution:** Because these pairs are curated synthetic starter examples (`34` labeled scenarios across `20` train pairs, `6` val pairs, and `8` unseen test queries against a `12`-doc test corpus with `4` hard distractors), retrieval gains on this starter benchmark validate pipeline mechanics and domain phrasing adaptation — **not** production accuracy across live portals.

### Pydantic Schema (`ml/src/data/matching_dataset.py`)
Every record includes:
- `pair_id`, `split` (`train` | `val` | `test`), `relevance_label` (`1` | `0`), `is_synthetic` (`true`)
- `student`: `student_id`, `education_year`, `branch`, `skills`, `career_interest`, `profile_summary`, `preferred_languages`
- `opportunity`: `opportunity_id`, `title`, `organization`, `domain_family`, `description`, `required_skills`, `eligible_years`
- Optional `hard_negative_opportunity`: realistic distractor sharing surface keywords (e.g., `"Python"`, `"3rd Year B.Tech"`) but belonging to an unrelated engineering domain.

---

## 2. Preventing Data Leakage

`ml/src/data/matching_dataset.py` enforces **entity- and opportunity-disjoint splitting** in `validate_no_split_leakage()`:
1. **Zero Student Overlap:** No `student_id` in `train` may appear in `val` or `test`.
2. **Zero Positive Opportunity Overlap:** No positive `opportunity_id` in `train` may appear in `val` or `test`.
3. **Processed Output (`datasets/processed/`, gitignored):** Generated deterministically by `ml/scripts/prepare_minilm_data.py` into `train_pairs.jsonl`, `val_pairs.jsonl`, `test_queries.jsonl`, and `test_corpus.jsonl`.

---

## 3. Approved External Datasets (Overnight / Production Phase)
1. **ESCO Taxonomy (European Skills, Competences and Occupations):** CC0 / Public Domain equivalent (~13,800 canonical skills).
2. **Resume Entities for NER (Kaggle):** Apache 2.0 / CC BY 4.0 (token entity boundaries).
3. **Licensed Multilingual Corpora (e.g., AI4Bharat IndicCorp / Flores-200 eval prompts):** For benchmarking 7-language understanding (`en, hi, te, ta, kn, ml, bn`).

## 4. PII Scrubbing Policy
Personal emails, phone numbers, Aadhaar references, and real student roll numbers must be stripped before writing any dataset to `datasets/raw/` or `datasets/processed/`.
