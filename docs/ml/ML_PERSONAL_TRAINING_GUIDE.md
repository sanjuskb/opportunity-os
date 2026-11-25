# Sanju's Personal 3-Hour CPU Fine-Tuning Guide (`all-MiniLM-L6-v2`)

**Model:** `sentence-transformers/all-MiniLM-L6-v2` (22.7M params, 384-dim embeddings, pretrained weights)  
**Objective:** Learn end-to-end bi-encoder domain adaptation using `MultipleNegativesRankingLoss` on **CPU-only Windows (`13th Gen Intel Core i5-1334U`, `Intel Iris Xe`, `15.64 GB` RAM)** — never training a transformer from scratch.

---

## 1. Hardware Reality & Expected Resource Footprint

- **Why Pretrained Weights Instead of From Scratch:** Pretraining a language encoder requires billions of tokens and GPU clusters. Fine-tuning `all-MiniLM-L6-v2` adapts existing semantic representations to Indian collegiate roles (`CGPA`, `B.Tech`, `Indic NLP`, `RTOS`, `FastAPI`, etc.) in minutes on CPU.
- **CPU Budget (`personal_minilm_cpu.yaml`):**
  - `device: cpu` (`torch.cuda.is_available() == False` expected on Intel Iris Xe)
  - `cpu_threads: 6` (safe for 10C / 12T laptop without thermal throttling or freezing VS Code)
  - `batch_size: 8`, `epochs: 3`, `max_sequence_length: 256`, `use_fp16: false`
- **Expected Download & Runtime:**
  - **First run download:** ~`90 MB` from Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`)
  - **Peak RAM during training:** ~`1.2–1.8 GB` RSS (comfortably within `15.64 GB` total RAM)
  - **Wall-clock time (~20 train pairs, 3 epochs):** ~`1.5 to 4 minutes` total on i5-1334U CPU (leave laptop plugged in for full 3-hour study/experimentation headroom).
- **Intel Iris Xe Notes:** Integrated Intel Iris Xe has no CUDA runtime. Optional future acceleration via `optimum-intel` / OpenVINO or ONNX Runtime INT8 quantization is **not** needed for this learning exercise and must remain separate from PyTorch training.

---

## 2. How `MultipleNegativesRankingLoss` Works

Given a batch of $B = 8$ matched pairs $\{(a_i, p_i)\}_{i=1}^8$ (`anchor` = student profile, `positive` = target internship):
- Every in-batch opportunity $p_j$ ($j \ne i$) automatically acts as an implicit negative for student $a_i$.
- Cross-entropy pushes cosine similarity $\cos(a_i, p_i)$ upward and $\cos(a_i, p_j)$ downward simultaneously — ideal for ranking without needing massive manual negative labels.

---

## 3. Data Leakage Rules Built Into This Exercise

1. All starter data in `ml/datasets/synthetic/matching_seed_examples.json` is explicitly flagged `"is_synthetic": true`.
2. `prepare_minilm_data.py` partitions into **disjoint student IDs and disjoint opportunity IDs** across `train` (`20`), `val` (`6`), and `test` (`8` queries against `12` docs including `4` hard keyword-sharing distractors).
3. `evaluate_minilm.py` runs **strictly on held-out unseen `test` entities** before and after training.

---

## 4. Exact Execution Sequence (3-Hour Session)

```powershell
# 1. Activate environment
cd "d:\ai career intelligence autonomous system"
.\ml\.venv\Scripts\Activate.ps1

# 2. Verify tests & zero leakage
pytest ml\tests -q

# 3. Prepare train / val / test JSONLs (offline, <1s)
python ml\scripts\prepare_minilm_data.py

# 4. Dry run (inspects dataset & trainer settings without downloading weights)
python ml\scripts\train_minilm.py --dry-run

# 5. Open Jupyter Lab OR run CLI training + side-by-side comparison
jupyter lab ml\notebooks\01_minilm_personal_training.ipynb
# OR CLI:
python ml\scripts\train_minilm.py
```

---

## 5. Known Limitations to Understand Before Drawing Conclusions
- A 20-pair synthetic starter set is intentionally small so you can iterate in 3 hours and observe training dynamics on CPU; real generalization requires 500–5,000+ scrubbed real/licensed job-resume pairs and real student feedback.
- Fine-tuning improves domain phrasing alignment **only if** held-out `nDCG@10` / `Recall@K` / `mean_pos_neg_margin` increases relative to baseline without overfitting validation loss. Never report gains unless your actual JSON comparison report in `ml/experiments/runs/` shows them.
