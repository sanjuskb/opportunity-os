# NexteRaS Fine-Tuned MiniLM Checkpoint Reproduction & Storage Guide

**Active Local Checkpoint Path:** `ml/artifacts/minilm-nexteras-v1` *(excluded from Git via `.gitignore` line 88 and `ml/.gitignore` line 41 — binary `.safetensors` weights are never committed to version control)*  
**Base Pretrained Fallback:** `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0, `384`-dim)

---

## 1. Reproducing `ml/artifacts/minilm-nexteras-v1` From Scratch

Ensure you are on the `ml` branch with the CPU Python 3.11 environment activated:

```powershell
# 1. Regenerate & verify zero-leakage splits for curriculum v2
ml\.venv\Scripts\python.exe ml\scripts\generate_curriculum_v2.py
ml\.venv\Scripts\python.exe ml\scripts\prepare_minilm_data.py --config ml\model_configs\minilm_cpu_finetune.yaml

# 2. Run CPU contrastive triplet fine-tuning (~13 min on Intel Core i5-1334U, 16 GB RAM)
ml\.venv\Scripts\python.exe ml\scripts\train_minilm.py --config ml\model_configs\minilm_cpu_finetune.yaml

# 3. Verify side-by-side baseline vs fine-tuned checkpoint metrics
ml\.venv\Scripts\python.exe ml\scripts\evaluate_minilm.py --config ml\model_configs\minilm_cpu_finetune.yaml
```

## 2. Deployment & Artifact Hosting Strategy

Because GitHub repositories should never bloat with binary model weights:
- **Runtime Safety Fallback:** `ModelRegistry` (`ml/model_configs/ml_registry.yaml`) resolves `ml/artifacts/minilm-nexteras-v1` automatically when populated, and falls back seamlessly to downloading/loading pretrained `sentence-transformers/all-MiniLM-L6-v2` when absent (zero crashes in slim containers).
- **Cloud Run / Production Packaging:** Upload `ml/artifacts/minilm-nexteras-v1` to either:
  1. A private Hugging Face Hub repository (`hf download <org>/nexteras-minilm-v1 --local-dir /app/ml/artifacts/minilm-nexteras-v1`), **or**
  2. A Google Cloud Storage bucket synced during Cloud Run container startup / volume mount (`ML_MATCHING_MODEL_PATH=/models/minilm-nexteras-v1`).
