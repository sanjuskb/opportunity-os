# Opportunity OS — Machine Learning & Model Strategy

## 1. System Segmentation: Deterministic Rules vs. Probabilistic ML

Opportunity OS enforces a strict architectural boundary between **hard eligibility** and **soft recommendations**:

| Task | Category | Implementation Method | Justification |
| :--- | :--- | :--- | :--- |
| **Graduation Year / Batch** | Deterministic | SQL / Python Set Comparison | A 2026 job requirement must strictly reject 2024 graduates; zero room for probability |
| **Degree & Branch Filtering** | Deterministic | Exact & Synonymous Match (e.g. B.Tech == B.E.) | Hard prerequisites dictated by employers |
| **Minimum CGPA** | Deterministic | Numeric Inequality | Pure arithmetic verification |
| **Skill Match & Semantic Relevance** | Probabilistic | Dense Vector Similarity (pgvector) | Nuanced evaluation of cross-domain skills |
| **Resume-to-JD Alignment** | Probabilistic | Cosine Distance + LLM Semantic Scoring | Evaluating experiential relevance |
| **Interview Answer Evaluation** | Probabilistic | Speech/Text LLM Rubric Scoring | Subjective communication & technical depth |

---

## 2. Model Selection & Embeddings Matrix

### 2.1 Embedding Models (Production Inference)
- **Primary:** `text-embedding-004` (Google Gemini) — 768 dimensions.
- **Fallback / Local Offline:** `BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2` (384 dims).
- **Distance Metric:** Cosine similarity via pgvector IVFFlat index.

### 2.2 Semantic Reranker & Match Scorer
- **Candidate Models:** `cross-encoder/ms-marco-MiniLM-L-6-v2` or `BBA-Reranker`.
- **Purpose:** Two-stage retrieval: pgvector retrieves top 50 candidates $\rightarrow$ cross-encoder reranks top 10 for display to student.

### 2.3 Educational LoRA Experimentation (Non-Production Prototype)
- **Objective:** Fine-tune a lightweight model (`meta-llama/Llama-3.2-3B-Instruct` or `Qwen2.5-3B`) using PEFT/LoRA specifically for Indian college curriculum mapping (translating Indian university syllabus descriptions into standard job skill taxonomies).
- **Dataset:** Curated Indian AICTE university syllabi mapped to standard ESCO / O*NET skill taxonomy.
- **Location:** Managed under `experiments/model-training/`. Kept strictly separated from production inference.

---

## 3. Evaluation Metrics & Experiment Tracking

1. **Retrieval Precision & Recall:**
   - Recall@20: Target $> 88\%$ on ground-truth matched internships.
   - Mean Reciprocal Rank (MRR): Target $> 0.75$.
2. **Deterministic Integrity:**
   - 100% precision on hard disqualifiers (e.g., student never recommended a job for which their CGPA or batch is invalid).
3. **Tracking Tool:** MLflow / Weights & Biases telemetry recorded during offline evaluation runs.
