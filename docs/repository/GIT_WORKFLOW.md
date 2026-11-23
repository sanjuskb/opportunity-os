# Opportunity OS — Standard Git Workflow & Branch Governance

**Document Version:** 1.0.0  
**Phase:** Repository Consolidation & Development Environment Standardization  
**Prepared By:** Antigravity (Senior Repository Administrator & DevOps Engineer)  
**Governance Standard:** Four Permanent Remote Branches (`main`, `develop`, `sanju`, `ramaraju`)  
**Target Repository:** `https://github.com/sanjuskb/opportunity-os`  

---

## 1. Permanent Branch Topology & Ownership

Opportunity OS enforces a strict four-branch topology across the repository:

```
  +-------------------------------------------------------------+
  |                           main                              |
  | (Stable, audited, production-ready hackathon release code)  |
  +-------------------------------------------------------------+
                                 ^
                                 | Protected Release PR
                                 |
  +-------------------------------------------------------------+
  |                          develop                            |
  | (Shared integration branch: validated frontend + backend)   |
  +-------------------------------------------------------------+
               ^                                   ^
               | Contributor PR                    | Contributor PR
               |                                   |
  +-------------------------+         +-------------------------+
  |          sanju          |         |        ramaraju         |
  | (Frontend, UI, Voice,   |         | (Backend FastAPI, DB,   |
  |  Spline, and ALL ML)    |         |  LangGraph, Integrations|
  +-------------------------+         +-------------------------+
```

### 1.1 Branch Roles & Boundaries
- **`main`**: Production release only. Never commit or push directly to `main`. Merges into `main` occur only via approved PR from `develop`.
- **`develop`**: Shared integration branch. Houses cross-team API contracts, shared TypeScript packages, and unified staging deployments.
- **`sanju`**: Dedicated contributor branch for **Sanju**. Houses the complete Next.js frontend, UI/UX, Voice Orb client, and **ALL Machine Learning (ML)** models, datasets, configs, and pipelines.
- **`ramaraju`**: Dedicated contributor branch for **Ramaraju**. Houses the FastAPI backend, Supabase PostgreSQL migrations, LangGraph agents, and external ingestion pipelines.

---

## 2. Daily Development Workflow for Sanju (Frontend & ML)

### 2.1 Working on the Primary Laptop (Frontend UI Development)
1. **Pull Latest Changes from `develop`:**
   ```bash
   git checkout sanju
   git pull origin sanju
   git merge origin/develop
   ```
2. **Implement Frontend Features:**
   ```bash
   # Make changes in apps/web/ or packages/
   pnpm --filter @opportunity-os/web test
   pnpm --filter @opportunity-os/web build
   ```
3. **Commit & Push to `sanju`:**
   ```bash
   git add apps/web/ packages/
   git commit -m "feat(web): implement opportunity card infinite scroll"
   git push origin sanju
   ```

### 2.2 Working on the Spare Laptop (Machine Learning Development)
Sanju performs ML experiments on the spare machine using Sanju's own GitHub credentials (SSH key authentication).

1. **Clone or Update the Repository:**
   ```bash
   git checkout sanju
   git pull origin sanju
   ```
2. **Execute Experiments in `ml/`:**
   ```bash
   cd ml
   source .venv/bin/activate
   python scripts/train.py --config model_configs/baseline_matching.yaml
   python scripts/evaluate.py
   ```
3. **Commit ML Code (Zero Large Datasets or Weights in Git):**
   ```bash
   # Verify no raw .csv, .parquet, or .pt files are staged
   git status
   git add ml/src/ ml/model_configs/ ml/scripts/ docs/ml/
   git commit -m "feat(ml): evaluate bi-encoder semantic matching benchmark"
   git push origin sanju
   ```
4. **Synchronize Back to Primary Laptop:**
   On the primary laptop: `git pull origin sanju` immediately syncs all ML code without merge conflicts.

---

## 3. Daily Development Workflow for Ramaraju (Backend & DB)

1. **Pull Latest Changes from `develop`:**
   ```bash
   git checkout ramaraju
   git pull origin ramaraju
   git merge origin/develop
   ```
2. **Implement Backend Services:**
   ```bash
   # Make changes in apps/api/ or supabase/migrations/
   uv run --directory apps/api pytest
   ```
3. **Commit & Push to `ramaraju`:**
   ```bash
   git add apps/api/ supabase/
   git commit -m "feat(api): implement ephemeral voice ticket handshake endpoint"
   git push origin ramaraju
   ```

---

## 4. Integration Workflow into `develop`

When a major milestone or sprint feature set is ready for cross-team integration:

1. **Open a Pull Request:**
   - Sanju opens PR: `sanju` $\rightarrow$ `develop`.
   - Ramaraju opens PR: `ramaraju` $\rightarrow$ `develop`.
2. **Automated CI Validation:**
   - GitHub Actions executes `Backend Checks`, `Frontend Checks`, `Security Checks`, and `CI Pipeline`.
   - All tests, type-checks, and builds must pass (100% Green).
3. **Peer Review & Approval:**
   - Contributor reviews and approves the PR.
4. **Merge & Update Contributor Branches:**
   - Once merged, both contributors pull `origin/develop` into their local branches to maintain synchronization.

---

## 5. Security & Repository Hygiene Commandments

1. **Zero Direct Pushes to `main` or `develop`:** All merges into `develop` and `main` must pass through reviewed Pull Requests.
2. **Zero Force-Pushing (`git push --force`):** Never force-push to `main`, `develop`, `sanju`, or `ramaraju`.
3. **Zero Secrets in Git:** API keys (Gemini, Supabase, Olostep, Crustdata) and private student data must never be committed. All secrets reside in local `.env` files protected by `.gitignore`.
4. **Zero Model Weights or Datasets in Git:** All datasets and binary model weights (`.pt`, `.bin`, `.safetensors`, `.onnx`) are governed via DVC or Hugging Face Model Hub.
5. **No Long-Lived Feature Branches:** Temporary feature branches (e.g. `feature/ml-pipeline`) must be short-lived, merged into `sanju` or `ramaraju`, and deleted promptly upon completion.
