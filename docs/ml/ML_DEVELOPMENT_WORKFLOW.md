# Opportunity OS — Two-Laptop ML & Frontend Collaboration Workflow

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Developer Tooling, Dual-Laptop Git Operations & ML Artifact Governance  
**Owner & Lead:** Sanju (Frontend & ML Lead)  
**Repository:** `https://github.com/sanjuskb/opportunity-os`  

---

## 1. Operating Model Overview

To balance intense frontend UI engineering with GPU-heavy machine learning experimentation without overburdening a single machine, Sanju operates across two physical machines:

1. **Laptop A (Primary Machine — Windows):**
   - **Primary Focus:** Next.js 15 frontend architecture, Tailwind styling, UI/UX components, Web Audio API, Voice Orb integration, client testing, and PR reviews.
2. **Laptop B (Spare Machine — Linux / Windows with Dedicated GPU):**
   - **Primary Focus:** Python ML experimentation, dataset ingestion, sentence-transformer fine-tuning, benchmark evaluation, and ONNX model quantization.

---

## 2. Identity, Authentication & Security Governance

> [!IMPORTANT]
> Both laptops access the **same unified GitHub repository** (`sanjuskb/opportunity-os`). There is **zero duplicate repository creation**.

### 2.1 SSH Key Protocol (No Shared Passwords or PATs)
- **Rule 1:** Sanju generates a dedicated SSH key pair on Laptop B (`ssh-keygen -t ed25519 -C "sanju-laptop-b"`).
- **Rule 2:** The public key (`id_ed25519.pub`) is added to Sanju's personal GitHub account under **Settings $\rightarrow$ SSH and GPG Keys**.
- **Rule 3:** Personal Access Tokens (PATs) and GitHub passwords are **never stored in plaintext** or shared across machines.
- **Rule 4:** Git config on both machines uses identical committer credentials:
  ```bash
  git config user.name "sanjuskb"
  git config user.email "sanju.skb.191144@gmail.com"
  ```

---

## 3. Branching & Git Feature Workflow

All development is isolated using short-lived feature branches that merge into `develop` via standard Pull Requests.

```
develop -------------------------------------------------------------* (Merge PR)
   \                                                                 /
    \--- feature/frontend-dashboard (Laptop A) ---------------------/
     \
      \-- feature/ml-biencoder-matching (Laptop B) ----------------* (Merge PR)
```

### 3.1 Standard Feature Branch Naming
- Frontend Work (Laptop A):
  - `feature/frontend-shell-and-tokens`
  - `feature/voice-orb-audio-worklet`
  - `feature/opportunities-infinite-feed`
- Machine Learning Work (Laptop B):
  - `feature/ml-pipeline-scaffold`
  - `feature/ml-biencoder-matching`
  - `feature/ml-skill-extraction`
  - `feature/ml-evaluation-benchmarks`

### 3.2 Dual-Laptop Synchronization Protocol
When transitioning between machines:
1. **On Laptop B before leaving:**
   ```bash
   git status
   git add ml/src/ ml/model_configs/ ml/scripts/
   git commit -m "feat(ml): implement bi-encoder fine-tuning script"
   git push origin feature/ml-biencoder-matching
   ```
2. **On Laptop A to inspect ML work:**
   ```bash
   git fetch origin
   git checkout feature/ml-biencoder-matching
   ```

---

## 4. Large Dataset & Model Artifact Governance (Zero Large Binaries in Git)

> [!CAUTION]
> Git is designed for text source code, not multi-gigabyte binary files. Committing `.parquet`, `.csv`, `.bin`, `.pt`, or `.onnx` files into Git permanently inflates repository size and causes merge conflicts.

### 4.1 Strict `.gitignore` Enforcement
The root `.gitignore` and `ml/.gitignore` strictly block:
- `ml/datasets/raw/*`
- `ml/datasets/processed/*`
- `*.pt`, `*.bin`, `*.safetensors`, `*.onnx`
- `mlruns/` (MLflow tracking database)
- `.venv/`, `__pycache__/`

### 4.2 Artifact Storage Options for Models & Datasets
For sharing datasets and trained model weights between Laptop B and Ramaraju's backend serving layer, Sanju uses:
1. **Option A (Recommended — Hugging Face Model Hub):**
   - Store model weights in a private Hugging Face model repository: `huggingface.co/sanjuskb/opportunity-os-matching-v1`.
   - Downloaded during backend deployment via `transformers` / `onnxruntime` with an environment token.
2. **Option B (DVC + Supabase Storage / S3):**
   - Use Data Version Control (`dvc`):
     ```bash
     dvc init
     dvc remote add -d storage s3://opportunity-os-ml-bucket/
     dvc add ml/datasets/processed/benchmark_pairs.parquet
     git add benchmark_pairs.parquet.dvc .gitignore
     git commit -m "chore(ml): track processed dataset with DVC"
     dvc push
     ```

---

## 5. Security & Secret Isolation Rules

1. **Zero Secrets in Repositories:** Never commit `.env` files or API credentials.
2. **Environment Variable Parity:**
   - On Laptop B, copy `.env.example` to `.env` and populate local ML configuration:
     ```env
     GEMINI_API_KEY=your_key_here
     HF_TOKEN=your_huggingface_token
     ML_LOG_LEVEL=INFO
     ```
3. **Student Privacy Protection:** All test datasets must be fully anonymized. Never process or store unredacted student phone numbers, email addresses, or university IDs.
