# Opportunity OS — ML Experimentation Framework & Training Pipeline

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** ML Pipelines, Reproducibility & Model Artifact Management  
**Owner & Lead:** Sanju (Frontend & ML Lead)  
**Backend Serving Partner:** Ramaraju (Backend & Infrastructure Lead)  
**Facilitator:** Antigravity (Architecture QA)  

---

## 1. Principles of Reproducible Experimentation

To ensure that ML experiments conducted on Sanju's spare laptop can be effortlessly validated, reproduced, and deployed to Ramaraju's backend serving layer, the ML pipeline adheres to strict reproducibility standards:

1. **Deterministic Random Seeds:** All training and evaluation scripts explicitly fix seeds across all libraries (`torch.manual_seed(42)`, `np.random.seed(42)`, `random.seed(42)`, `torch.cuda.manual_seed_all(42)`).
2. **Configuration as Code (YAML):** Model hyperparameters, embedding dimensions, loss functions, learning rates, and dataset paths are decoupled from code and defined in `ml/model_configs/*.yaml`.
3. **Leakage-Free Validation Splitting:** Opportunity and resume datasets are partitioned using **Scaffold / Domain Splits** (splitting by academic institution or career domain) rather than random splits to ensure the models generalize across unseen colleges.
4. **Local Experiment Tracking:** Lightweight experiment logging using MLflow or local SQLite/JSON logs in `ml/experiments/` without external cloud SaaS dependencies.

---

## 2. Directory Layout of the `ml/` Monorepo Subsystem

```
ml/
├── README.md                          # Quickstart instructions for running ML experiments
├── .gitignore                         # Excludes raw datasets, binaries, checkpoints, cache
├── pyproject.toml                     # Python dependencies (PyTorch, transformers, sentence-transformers)
├── requirements.txt                   # Locked pip requirements for fast spare laptop setup
├── model_configs/                     # Experiment configurations (YAML)
│   ├── baseline_matching.yaml
│   ├── bge_finetuning.yaml
│   └── ranker_config.yaml
├── datasets/                          # Local dataset cache (DVC tracked)
│   ├── README.md                      # Dataset acquisition & licensing guidelines
│   ├── raw/                           # Raw inputs (ignored in Git)
│   └── processed/                     # Preprocessed tokenized inputs (ignored in Git)
├── notebooks/                         # Exploratory data analysis & model probing
│   └── 01_exploratory_matching.ipynb
├── experiments/                       # Experiment run logs & metric summaries
│   ├── README.md
│   └── runs/                          # JSON metric records per run
├── evaluation/                        # Benchmarks & evaluation test harnesses
│   ├── benchmarks.json
│   └── test_suite.py
├── scripts/                           # Reproducible CLI automation scripts
│   ├── prepare_data.py
│   ├── train_biencoder.py
│   ├── evaluate_matching.py
│   └── export_onnx.py
└── src/                               # Reusable Python ML package
    ├── __init__.py
    ├── data/
    │   ├── __init__.py
    │   ├── loaders.py
    │   └── preprocessors.py
    ├── features/
    │   ├── __init__.py
    │   ├── embeddings.py
    │   └── taxonomy_matcher.py
    ├── models/
    │   ├── __init__.py
    │   ├── biencoder.py
    │   ├── crossencoder.py
    │   └── ranker.py
    └── evaluation/
        ├── __init__.py
        └── metrics.py
```

---

## 3. End-to-End Training & Evaluation Pipeline

The standard ML workflow executes in five automated stages:

```
+-------------------------------------------------------------------------+
| STAGE 1: DATA INGESTION & ANONYMIZATION (scripts/prepare_data.py)       |
| Ingests raw job descriptions and resumes; strips PII (names, phones,    |
| emails); normalizes unicode and Indic text; splits into 70/15/15 folds. |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| STAGE 2: FEATURE ENCODING & TOKENIZATION (src/features/)                |
| Tokenizes skill terms against ESCO taxonomy; generates candidate dense   |
| embeddings using MiniLM/BGE; saves tokenized cache to ml/datasets/.      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| STAGE 3: FINE-TUNING & METRIC OPTIMIZATION (scripts/train_biencoder.py) |
| Fine-tunes sentence-transformer with MultipleNegativesRankingLoss       |
| on positive (student_profile, job_match) pairs with in-batch negatives.  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| STAGE 4: BENCHMARK EVALUATION (scripts/evaluate_matching.py)            |
| Computes NDCG@10, MRR@10, and field accuracy against test dataset.      |
| Writes performance results to ml/evaluation/benchmarks.json.            |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| STAGE 5: ARTIFACT EXPORT & ONNX QUANTIZATION (scripts/export_onnx.py)   |
| Quantizes PyTorch model to INT8 ONNX graph for ultra-fast, zero-GPU CPU |
| serving in Ramaraju's FastAPI backend container.                        |
+-------------------------------------------------------------------------+
```

---

## 4. Hardware Optimization & ONNX Runtime Serving

To ensure that Ramaraju's backend can run inference with minimal cloud resource costs:

1. **PyTorch to ONNX Export:**
   ```python
   # scripts/export_onnx.py
   import torch
   from transformers import AutoModel, AutoTokenizer

   def export_to_onnx(model_name: str, output_path: str):
       model = AutoModel.from_pretrained(model_name)
       tokenizer = AutoTokenizer.from_pretrained(model_name)
       dummy_input = tokenizer("Software Engineer Internship", return_tensors="pt")
       
       torch.onnx.export(
           model,
           (dummy_input['input_ids'], dummy_input['attention_mask']),
           output_path,
           input_names=['input_ids', 'attention_mask'],
           output_names=['embeddings'],
           dynamic_axes={'input_ids': {0: 'batch', 1: 'sequence'}, 'embeddings': {0: 'batch'}},
           opset_version=14
       )
   ```
2. **8-bit Dynamic Quantization:** Reduces model weight footprint from $420\text{ MB}$ to $\sim 110\text{ MB}$ and accelerates CPU inference latency by $2.8\times$ with $< 0.5\%$ loss in NDCG@10.
3. **Serving Hand-off:** The exported `.onnx` model and tokenizer configuration are placed in external artifact storage (Hugging Face Model Hub / Supabase Storage) and loaded directly by FastAPI in `apps/api/app/services/ml/` using `onnxruntime`.
