# Opportunity OS — Machine Learning Subsystem (`ml/`)

This directory houses all Machine Learning model research, dataset processing, feature extraction, fine-tuning scripts, and benchmark evaluations for **Opportunity OS**.

## 1. Ownership & Governance
- **Sole Lead:** Sanju (Frontend & ML Lead).
- **Backend Serving Partner:** Ramaraju (Backend & Infrastructure Lead).
- **Advisory:** Antigravity (Architecture QA).

## 2. Directory Structure

```
ml/
├── README.md                          # Subsystem guide & quickstart
├── .gitignore                         # Excludes raw datasets, binaries, and checkpoints
├── pyproject.toml                     # Python dependencies & build config
├── model_configs/                     # Experiment configurations (YAML)
│   └── baseline_matching.yaml         # Default hyperparameters for embedding model
├── datasets/                          # Datasets directory (DVC tracked)
│   └── README.md                      # Dataset acquisition & licensing guidelines
├── notebooks/                         # Exploratory data analysis & model probing
├── experiments/                       # Experiment run logs & metric records
│   └── README.md
├── evaluation/                        # Benchmarks & evaluation test harnesses
│   └── benchmarks.json                # Canonical benchmark metrics record
├── scripts/                           # Reproducible CLI automation scripts
│   ├── train.py                       # Bi-encoder & ranker training script
│   └── evaluate.py                    # Evaluation test runner
└── src/                               # Reusable Python ML package
    ├── __init__.py
    ├── data/                          # Data loading & PII scrubbing
    ├── features/                      # Tokenization & ESCO taxonomy matching
    ├── models/                        # Bi-encoder, cross-encoder, & rankers
    └── evaluation/                    # Metrics (NDCG@10, MRR, Precision)
```

## 3. Quickstart: Setting up the ML Environment on Spare Laptop

```bash
cd ml

# 1. Create a virtual environment using Python 3.11+
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies with UV or Pip
pip install -e .

# 3. Run baseline evaluation
python scripts/evaluate.py --config model_configs/baseline_matching.yaml
```

## 4. Large Dataset & Artifact Policy
- **Never commit `.csv`, `.parquet`, `.pt`, `.bin`, `.safetensors`, or `.onnx` files into Git.**
- Use DVC or Hugging Face Hub (`huggingface.co/sanjuskb/...`) for artifact versioning.
