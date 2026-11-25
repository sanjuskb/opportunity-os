# NexteRaS — Machine Learning Subsystem (`ml/`)

Machine Learning models, deterministic eligibility/ranking engines, reproducible benchmarks, and integration adapters for **NexteRaS — The Upcoming Era.**

---

## 1. Laptop Hardware & Python Environment Summary

- **Machine:** ASUSTeK Vivobook X1504VA (`15.64 GiB` / `16.79 GB` RAM, `79.38 GB` free on `D:`)
- **Processor:** 13th Gen Intel Core i5-1334U (`10` Cores / `12` Logical Processors)
- **GPU / Compute Mode:** Intel Iris Xe Graphics (integrated graphics — **CPU-only PyTorch execution**; no NVIDIA GPU / no CUDA Toolkit)
- **Python Environment:** `ml/.venv` (`Python 3.11.16` managed via `uv`, registered Jupyter kernel `nexteras-ml`)
- **Core Runtime Verified:** `torch==2.15.0+cpu` (`torch.cuda.is_available() == False`)

> [!IMPORTANT]
> **Laptop Memory Protection:** Because OS + IDE/browser consume substantial RAM on a 16 GB laptop, `ml/src/infrastructure/runtime.py` enforces **`ResourceManagedModelCache(max_loaded_models=1, cpu_threads=6)`** so heavy transformer models never stack in RAM simultaneously.

---

## 2. Implemented Subsystem Capabilities (`ml/src/`)

| Package | Role | Key Docs |
| :--- | :--- | :--- |
| `ml/src/infrastructure/` | Model registry (`ml_registry.yaml`), single-model lazy eviction cache, PII redaction (`redact_pii`) & upload safety checks | [ML_DEPLOYMENT_GUIDE.md](../docs/ml/ML_DEPLOYMENT_GUIDE.md) |
| `ml/src/extraction/` | Hybrid resume profile & skill extraction (canonical CS/ECE aliases, evidence spans, broken LLM JSON recovery) | [NEXTERAS_ML_ARCHITECTURE_INVENTORY.md](../docs/ml/NEXTERAS_ML_ARCHITECTURE_INVENTORY.md) |
| `ml/src/eligibility/` | Unstructured JD prerequisite parser & strict deterministic eligibility evaluator (`eligible \| ineligible \| needs_more_info \| unable_to_verify`) | [NEXTERAS_ML_ARCHITECTURE_INVENTORY.md](../docs/ml/NEXTERAS_ML_ARCHITECTURE_INVENTORY.md) |
| `ml/src/ranking/` | Deduplication, expiry filtering, eligibility separation & weighted baseline ranker + supervised GBDT feature pipeline (`pending_user_interaction_data`) | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/multilingual/` | Non-destructive Unicode NFC script preprocessing (`en, hi, te, ta, kn, ml, bn, hinglish`) + `paraphrase-multilingual-MiniLM-L12-v2` + fallback hooks | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/verification/` | Auxiliary evidence consistency service (`cross-encoder/nli-deberta-v3-small` + lightweight lexical fallback; `is_advisory_only=True`) | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/matching/` | `SemanticMatcher` resolving Sanju's personal fine-tuned checkpoint or automatic pretrained `all-MiniLM-L6-v2` baseline | [ML_PERSONAL_TRAINING_GUIDE.md](../docs/ml/ML_PERSONAL_TRAINING_GUIDE.md) |
| `ml/src/integration/` | Unified dependency-injectable `NexteRaSMLService` & `NexteRaSLangGraphAdapter` aligned with `apps/api/app/ml/adapter.py` | [ML_INTEGRATION_CONTRACT.md](../docs/ml/ML_INTEGRATION_CONTRACT.md) |

---

## 3. Running Tests, Evaluations & Services

### Activate Environment (PowerShell)
```powershell
cd "d:\ai career intelligence autonomous system"
.\ml\.venv\Scripts\Activate.ps1
```

### Run Full Automated Test Suite (`pytest` across all 8 test modules)
```powershell
.\ml\.venv\Scripts\python.exe -m pytest ml\tests -v
```

### Run Offline & Pretrained Model Benchmarks (One Heavy Model Per Process)
```powershell
# Fast offline checks (< 1s)
python ml\scripts\run_full_ml_evaluation.py --components extraction eligibility ranking nli_fallback

# Optional sequential Hugging Face CPU evaluations (isolates memory cleanly per process):
python ml\scripts\run_full_ml_evaluation.py --components semantic_baseline
python ml\scripts\run_full_ml_evaluation.py --components multilingual
python ml\scripts\run_full_ml_evaluation.py --components nli
```

---

## 4. Integrating Sanju's Personally Fine-Tuned `all-MiniLM-L6-v2` Model

Your personal training kit (`ml/scripts/train_minilm.py`, `ml/notebooks/01_minilm_personal_training.ipynb`, `ml/model_configs/personal_minilm_cpu.yaml`) was preserved completely untouched:

1. **Train personally during your 3-hour session:**
   ```powershell
   python ml\scripts\prepare_minilm_data.py
   python ml\scripts\train_minilm.py
   ```
   This saves your fine-tuned checkpoint cleanly to **`ml/artifacts/minilm-nexteras-v1`** (gitignored).
2. **Automatic Activation (Zero Code Changes Needed):**
   `ModelRegistry` (`ml/model_configs/ml_registry.yaml`) points `semantic_matcher.local_path` to `ml/artifacts/minilm-nexteras-v1`. As soon as that directory contains your saved model files, `SemanticMatcher` and `NexteRaSMLService` automatically switch from pretrained baseline to your fine-tuned checkpoint (`using_finetuned_checkpoint == True`), while continuing to fall back safely when absent!
3. **Compare Before vs After:**
   ```powershell
   python ml\scripts\evaluate_minilm.py
   ```
4. **Vector Dimension Contract (`vector(384)` vs `vector(768)`):**
   Before persisting 384-dim MiniLM vectors into Supabase `pgvector`, review [VECTOR_DIMENSION_COMPATIBILITY.md](../docs/ml/VECTOR_DIMENSION_COMPATIBILITY.md) and coordinate applying [20261125000001_add_minilm_384_embeddings.sql](../supabase/migrations/20261125000001_add_minilm_384_embeddings.sql).
