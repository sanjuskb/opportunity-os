# ML Evaluation & Experimentation Guide

Defines the evaluation protocol, IR metrics, comparison rules, and local logging format for **NexteRaS** CPU experiments.

---

## 1. Mandatory Before-and-After Evaluation Protocol

Never claim a fine-tuned model improved performance unless a controlled side-by-side comparison on **held-out unseen examples** proves it:

1. **Step 1 — Prepare Clean Splits:** Run `ml/scripts/prepare_minilm_data.py` and verify zero `student_id` / `opportunity_id` overlap.
2. **Step 2 — Baseline Measurement BEFORE Fine-Tuning:** Evaluate off-the-shelf `sentence-transformers/all-MiniLM-L6-v2` on `test_queries.jsonl` vs `test_corpus.jsonl`.
3. **Step 3 — CPU Fine-Tuning:** Train strictly on `train_pairs.jsonl` using `MultipleNegativesRankingLoss` with fixed RNG seeds (`seed: 42`).
4. **Step 4 — Held-Out Evaluation AFTER Fine-Tuning:** Re-run identical `evaluate_sentence_transformer()` on `test_queries.jsonl` vs `test_corpus.jsonl`.
5. **Step 5 — Delta Reporting:** Compare `Recall@1`, `Recall@3`, `Recall@5`, `MRR@10`, `nDCG@10`, `mean_pos_neg_margin`, and CPU query encoding latency side-by-side.

---

## 2. Metrics Implemented (`ml/src/evaluation/retrieval_metrics.py`)

| Metric | Meaning in NexteRaS |
| :--- | :--- |
| **Recall@1 / @3 / @5** | Fraction of unseen students whose true target internship appears in the top `K` cosine matches |
| **MRR@10** | Mean Reciprocal Rank `1 / rank` across top 10 ranked internships |
| **nDCG@10** | Rank-discounted retrieval gain (higher weight when true match ranks #1 vs #4) |
| **mean_pos_neg_margin** | Average cosine gap `cos(q, pos) - max(cos(q, neg))` showing separation vs hard distractors |
| **encode_latency_per_query_ms** | Real CPU wall-clock encoding latency per query on Intel Core i5-1334U |

---

## 3. Experiment Run Log Schema (`ml/experiments/runs/<timestamp>_minilm.json`)

Each run writes a local gitignored JSON report containing:
- `timestamp_utc`, `git_commit`, `hardware` (`cpu_threads`, `torch_version`, `cuda_available: false`)
- `config`: exact YAML training settings
- `split_counts`: `train_pairs`, `val_pairs`, `test_queries`, `test_corpus_docs`
- `baseline_metrics` vs `finetuned_metrics` and `delta_metrics` (`finetuned - baseline`)
- `known_limitations`: explicit caveats on sample size and synthetic phrasing distribution
