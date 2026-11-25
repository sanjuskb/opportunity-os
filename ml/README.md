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
| `ml/src/infrastructure/` | Model registry (`ml_registry.yaml`), single-model thread-safe eviction cache (`execute_with_model`), PII redaction (`redact_pii`) & upload safety checks | [ML_DEPLOYMENT_GUIDE.md](../docs/ml/ML_DEPLOYMENT_GUIDE.md) |
| `ml/src/extraction/` | Hybrid resume profile & skill extraction (`.txt`, `.md`, `.json`, `.pdf` via PyMuPDF, canonical taxonomy, LLM JSON recovery) | [NEXTERAS_ML_ARCHITECTURE_INVENTORY.md](../docs/ml/NEXTERAS_ML_ARCHITECTURE_INVENTORY.md) |
| `ml/src/eligibility/` | Unstructured JD prerequisite parser & strict deterministic evaluator (degree equivalence, branch, batch, academic year, CGPA/%, backlogs, experience, location/remote, deadline, citizenship & missing-info tracking) | [NEXTERAS_ML_ARCHITECTURE_INVENTORY.md](../docs/ml/NEXTERAS_ML_ARCHITECTURE_INVENTORY.md) |
| `ml/src/ranking/` | Deduplication, expiry filtering, eligibility separation & weighted baseline ranker + supervised GBDT feature pipeline (`pending_user_interaction_data`) | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/multilingual/` | Non-destructive Unicode NFC script preprocessing (`en, hi, te, ta, kn, ml, bn, hinglish`) + `paraphrase-multilingual-MiniLM-L12-v2` + exception-safe translation fallback | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/verification/` | Auxiliary evidence consistency service (`cross-encoder/nli-deberta-v3-small` + timeout/error lexical fallback; `is_advisory_only=True`) | [ML_EVALUATION_REPORT.md](../docs/ml/ML_EVALUATION_REPORT.md) |
| `ml/src/matching/` | `SemanticMatcher` resolving fine-tuned `ml/artifacts/minilm-nexteras-v1` checkpoint or automatic pretrained `all-MiniLM-L6-v2` fallback | [MINILM_CHECKPOINT_REPRODUCTION.md](model_configs/MINILM_CHECKPOINT_REPRODUCTION.md) |
| `ml/src/integration/` | Unified dependency-injectable `NexteRaSMLService`, real executable `build_nexteras_career_workflow()` LangGraph `StateGraph` (M11 halt/resume), & optional Gemini credential-checked backends | [BACKEND_INTEGRATION_HANDOFF.md](../docs/ml/BACKEND_INTEGRATION_HANDOFF.md) |

---

## 3. Running Tests, Evaluations & Fine-Tuning

### Activate Environment (PowerShell)
```powershell
cd "d:\ai career intelligence autonomous system"
.\ml\.venv\Scripts\Activate.ps1
```

### Run Automated Tests (Separated Modes)
```powershell
# Fast unit, API integration, and LangGraph E2E tests
.\ml\.venv\Scripts\python.exe -m pytest ml\tests -m "not slow" -v

# Real Hugging Face & fine-tuned PyTorch CPU model inference tests
.\ml\.venv\Scripts\python.exe -m pytest ml\tests -m "slow" -v
```

### Run Offline & Pretrained Model Benchmarks
```powershell
python ml\scripts\run_full_ml_evaluation.py --components extraction eligibility ranking semantic_baseline multilingual nli_fallback nli
```

---

## 4. Fine-Tuned `all-MiniLM-L6-v2` Checkpoint (`ml/artifacts/minilm-nexteras-v1`)

1. **Reproduce Fine-Tuning on CPU (`matching_curriculum_v2.json`):**
   ```powershell
   python ml\scripts\generate_curriculum_v2.py
   python ml\scripts\prepare_minilm_data.py --config ml\model_configs\minilm_cpu_finetune.yaml
   python ml\scripts\train_minilm.py --config ml\model_configs\minilm_cpu_finetune.yaml
   ```
   Saves the validation-selected checkpoint to **`ml/artifacts/minilm-nexteras-v1`** (gitignored; weights are never committed to Git).
2. **Automatic Activation & Pretrained Fallback:**
   `ModelRegistry` (`ml/model_configs/ml_registry.yaml`) points `semantic_matcher.local_path` to `ml/artifacts/minilm-nexteras-v1`. When present, `SemanticMatcher` and `NexteRaSMLService` load it automatically (`using_finetuned_checkpoint == True`); when absent (e.g., fresh clone), they fall back cleanly to pretrained `sentence-transformers/all-MiniLM-L6-v2`.
3. **Compare Baseline vs Fine-Tuned:**
   ```powershell
   python ml\scripts\evaluate_minilm.py --config ml\model_configs\minilm_cpu_finetune.yaml
   ```
4. **Vector Dimension Contract (`vector(384)` vs `vector(768)`):**
   Before persisting 384-dim MiniLM vectors into Supabase `pgvector`, review [VECTOR_DIMENSION_COMPATIBILITY.md](../docs/ml/VECTOR_DIMENSION_COMPATIBILITY.md) and coordinate applying [20261125000001_add_minilm_384_embeddings.sql](../supabase/migrations/20261125000001_add_minilm_384_embeddings.sql).
