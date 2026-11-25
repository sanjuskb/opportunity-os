# NexteRaS — Machine Learning Subsystem (`ml/`)

Machine Learning research, dataset preparation, fine-tuning, and retrieval evaluation for **NexteRaS — The Upcoming Era.**

---

## 1. Laptop Hardware & Python Environment Summary

- **Machine:** ASUSTeK Vivobook X1504VA (`15.64 GB` RAM)
- **Processor:** 13th Gen Intel Core i5-1334U (`10` Cores / `12` Logical Processors)
- **GPU / Compute Mode:** Intel Iris Xe Graphics (integrated graphics — **CPU-only PyTorch execution**; no NVIDIA GPU / no CUDA Toolkit)
- **Python Environment:** `ml/.venv` (`Python 3.11.16` managed via `uv`, isolated from global Windows Python `3.13.6`)
- **Core Runtime Verified:** `torch 2.15.0+cpu` (`torch.cuda.is_available() == False`)

> [!NOTE]
> Intel Iris Xe does not support NVIDIA CUDA. All experiments in `ml/` are sized cleanly for **CPU execution** (`batch_size <= 8`, `all-MiniLM-L6-v2` `22M` parameters, `max_sequence_length: 256`). Optional Intel OpenVINO/ONNX CPU export is documented separately without adding experimental dependencies.

---

## 2. Environment Activation & Verification

### PowerShell (Windows)
```powershell
cd "d:\ai career intelligence autonomous system"
.\ml\.venv\Scripts\Activate.ps1
python -c "import torch, sentence_transformers; print(torch.__version__, 'CUDA:', torch.cuda.is_available())"
```

### CMD (Windows)
```cmd
cd /d "d:\ai career intelligence autonomous system"
ml\.venv\Scripts\activate.bat
```

### Reproducible Installation on Another CPU Machine
```powershell
uv venv ml\.venv --python 3.11 --seed
.\ml\.venv\Scripts\python.exe -m pip install --upgrade pip
.\ml\.venv\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0+cpu
.\ml\.venv\Scripts\python.exe -m pip install -r ml\requirements.txt
```

---

## 3. Directory Structure

```text
ml/
├── README.md                                  # Setup, quickstart & hardware guide
├── requirements.txt                           # Reproducible CPU dependency lock
├── pyproject.toml                             # Package config (NexteRaS ML)
├── .gitignore                                 # Excludes .venv, HF caches, weights, raw/processed data, logs
├── model_configs/
│   ├── baseline_matching.yaml                 # Baseline bi-encoder config
│   └── personal_minilm_cpu.yaml               # Sanju's 3-hour CPU fine-tuning config
├── datasets/
│   ├── README.md                              # Schema, provenance & split isolation rules
│   └── synthetic/
│       └── matching_seed_examples.json        # Clearly tagged synthetic starter pairs & test distractors
├── notebooks/
│   └── 01_minilm_personal_training.ipynb      # Step-by-step guided CPU fine-tuning lab
├── scripts/
│   ├── prepare_minilm_data.py                 # Generates leakage-free train/val/test JSONLs
│   ├── train_minilm.py                        # Baseline eval + CPU fine-tuning + post-eval
│   ├── evaluate_minilm.py                     # Side-by-side base vs tuned evaluation script
│   ├── train.py                               # Original baseline scaffold (preserved)
│   └── evaluate.py                            # Benchmark loader (preserved)
├── src/
│   ├── common/config.py                       # YAML loading, CPU threads & seeding
│   ├── data/matching_dataset.py               # Pydantic schemas & split leakage validator
│   ├── evaluation/retrieval_metrics.py        # Recall@K, MRR@10, nDCG@10 & margin scorer
│   └── matching/semantic_matcher.py           # Clean inference wrapper decoupled from FastAPI
├── experiments/
│   ├── README.md                              # Evaluation protocol & local run log format
│   └── runs/                                  # Local JSON comparison reports (gitignored)
├── evaluation/
│   └── benchmarks.json                        # Canonical target metric register
└── tests/
    └── test_dataset_and_metrics.py            # Automated split leakage & metric tests
```

---

## 4. Quickstart — Personal 3-Hour Learning Session (`all-MiniLM-L6-v2`)

1. **Run unit tests (verifies zero split leakage and exact IR metrics):**
   ```powershell
   .\ml\.venv\Scripts\python.exe -m pytest ml\tests -q
   ```
2. **Prepare leakage-free processed JSONL splits (`< 1 second`, offline):**
   ```powershell
   .\ml\.venv\Scripts\python.exe ml\scripts\prepare_minilm_data.py
   ```
3. **Inspect training setup with dry run (`0 model downloads`, validates config & splits):**
   ```powershell
   .\ml\.venv\Scripts\python.exe ml\scripts\train_minilm.py --dry-run
   ```
4. **Execute interactive Jupyter notebook OR full CLI training (~1.5–4 min CPU after ~90 MB HF download):**
   ```powershell
   .\ml\.venv\Scripts\python.exe -m jupyter lab ml\notebooks\01_minilm_personal_training.ipynb
   # OR CLI:
   .\ml\.venv\Scripts\python.exe ml\scripts\train_minilm.py
   ```

See [ML_PERSONAL_TRAINING_GUIDE.md](../docs/ml/ML_PERSONAL_TRAINING_GUIDE.md) and [OVERNIGHT_ML_IMPLEMENTATION_PLAN.md](../docs/ml/OVERNIGHT_ML_IMPLEMENTATION_PLAN.md) for deeper guidance.

---

## 5. Git Artifact Policy
- **Never commit** `ml/.venv/`, Hugging Face model caches, `.pt`/`.bin`/`.safetensors`/`.onnx` model weights, `ml/datasets/raw/*`, `ml/datasets/processed/*`, or local run logs.
- All new ML experiments must stay on branch `ml` until ready for PR review into `develop`.
