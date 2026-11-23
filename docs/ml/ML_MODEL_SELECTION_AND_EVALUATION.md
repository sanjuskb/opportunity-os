# Opportunity OS — Machine Learning Model Selection & Evaluation Blueprint

**Document Version:** 1.0.0  
**Phase:** Homingo Phase 5 — Engineering Blueprint  
**Subsystem:** Machine Learning Architecture & Evaluation  
**Owner & Lead:** Sanju (Frontend & ML Lead)  
**Backend Serving Partner:** Ramaraju (Backend & Infrastructure Lead)  
**Facilitator:** Antigravity (Architecture QA)  

---

## 1. Governance & Non-Negotiable Ownership Policy

> [!IMPORTANT]
> **ALL ML MODEL SELECTION, DATASET RESEARCH, TRAINING, FINE-TUNING, EXPERIMENTATION AND EVALUATION ARE OWNED EXCLUSIVELY BY SANJU.**  
> Ramaraju owns backend integration, FastAPI endpoints, model-serving containers, and hardware provisioning. Antigravity acts solely as an architecture QA advisor and will never independently train, select, or swap ML models without Sanju's explicit written approval.

---

## 2. Core Philosophy: Pragmatic, Grounded & Production-Minded

For Opportunity OS to succeed in the Homingo Hackathon and deliver genuine utility to Indian college students, the ML strategy adheres to three core tenets:

1. **Do Not Over-Engineer:** Not every AI capability requires an expensive custom-trained transformer. Standard deterministic algorithms, lightweight pre-trained encoders, and targeted few-shot LLM inferences are preferred where they yield superior latency, cost, and explainability.
2. **Explainability Over Black-Box Scores:** When a student is marked ineligible or ranked for an opportunity, the model must output human-interpretable reasoning (e.g. *"Missing Python / Docker prerequisite"*) rather than an opaque float score.
3. **Low-Latency & Cost Efficiency:** All candidate inference pipelines must operate within sub-200ms latency budgets on standard cloud CPU/T4 GPU instances without requiring enterprise multi-GPU clusters.

---

## 3. Detailed ML Feature Specifications

Below is the exhaustive architectural specification for all six ML features in Opportunity OS.

---

### Feature 1: Resume Parsing & Structured Information Extraction

#### 1.1 Problem Definition
Indian college students author resumes in wildly varying formats (single-column academic CVs, two-column Canva templates, tables, text without headings). The system must extract candidate contact info, college, degree, graduation year, CGPA, technical skills, projects, and work experience into a validated, grounded JSON schema matching `@opportunity-os/shared-types`.

#### 1.2 Architectural Approach: Two-Stage Hybrid Pipeline
- **Stage 1 (Deterministic Layout & Text Extraction):** `pdfplumber` / PyMuPDF extracts raw text blocks, reading order, and bounding boxes. Scanned PDFs are routed to Tesseract OCR with image deskewing.
- **Stage 2 (Structured Entity Extraction):** Lightweight, schema-guided LLM extraction (Gemini 1.5 Flash with Pydantic JSON schema) or Zero-Shot Named Entity Recognition (GLiNER).
  - *Recommendation for Sanju:* Gemini 1.5 Flash for the hackathon MVP due to 100% schema compliance and multi-column document comprehension; evaluate GLiNER (`urchade/gliner_base-v2.1`) for offline/on-premise zero-cost token extraction.

#### 1.3 Candidate Models
1. **Gemini 1.5 Flash:** Cloud API, native JSON mode, $1\text{M}$ context window.
2. **GLiNER Base (`urchade/gliner_base-v2.1`):** 160M parameter bidirectional encoder; zero-shot entity extraction on CPU in $< 350\text{ms}$.
3. **SpaCy `en_core_web_trf`:** Traditional RoBERTa-based NER baseline.

#### 1.4 Datasets & Licensing
- **Resume Entities for NER (Kaggle):** 2,000+ annotated student/professional resumes (Apache 2.0).
- **Synthetic Indian Collegiate Resume Benchmark:** 200 synthetic student resumes generated across 7 engineering branches and 20 Indian universities with edge cases (CGPA out of 10 vs percentage out of 100).

#### 1.5 Baseline & Evaluation Metrics
- **Baseline:** Regex + heuristic keyword matching.
- **Evaluation Metrics:**
  - Strict Token F1-score for entities (Education, Projects, Skills): **Target $\text{F1} \ge 0.92$**.
  - Critical Field Extraction Accuracy (CGPA, Degree, Batch Year): **Target $\ge 98.0\%$** (zero room for student disqualification due to parser error).
- **Inference Budget:** $< 1.2\text{s}$ per resume.

---

### Feature 2: Resume-Job Semantic Matching (Bi-Encoder + Cross-Encoder)

#### 2.1 Problem Definition
Determine semantic relevance between a student's verified profile/resume and an unstructured job/internship description. Keyword matching fails when a student lists *"FastAPI"* and the job lists *"Python backend frameworks"*.

#### 2.2 Architectural Approach: Two-Stage Dense Retrieval & Reranking
- **Stage 1 (Bi-Encoder Dense Vector Search):** Generates independent 768-dim embeddings for opportunity descriptions and student Career Passports. Pre-computed and indexed in PostgreSQL via `pgvector` with HNSW cosine indexing.
- **Stage 2 (Cross-Encoder Deep Relevance Scoring):** Takes top-20 retrieved opportunities and passes the concatenated pair `(student_profile, job_description)` through a cross-attention transformer to compute fine-grained relevance score $S \in [0, 100]$.

#### 2.3 Candidate Models
- **Bi-Encoder Candidates:**
  1. `BAAI/bge-large-en-v1.5` (Top performer on MTEB retrieval benchmark; 1024-dim).
  2. `sentence-transformers/all-MiniLM-L6-v2` (Ultra-fast 384-dim; runs in $15\text{ms}$ on CPU).
  3. `text-embedding-004` (Google Vertex/Gemini embedding API; 768-dim).
- **Cross-Encoder Candidates:**
  1. `cross-encoder/ms-marco-MiniLM-L-6-v2` (Fast, 6-layer BERT reranker).
  2. `BAAI/bge-reranker-large` (State-of-the-art multilingual reranker).

#### 2.4 Baseline & Evaluation Metrics
- **Baseline:** BM25 keyword search (PostgreSQL `tsvector`).
- **Evaluation Metrics:**
  - $\text{NDCG@10}$: Normalized Discounted Cumulative Gain at rank 10: **Target $\ge 0.85$**.
  - $\text{MRR@10}$: Mean Reciprocal Rank: **Target $\ge 0.80$**.
  - $\text{Precision@5}$: **Target $\ge 0.88$**.
- **Inference Budget:** Bi-encoder $< 30\text{ms}$; Cross-encoder top-20 rerank $< 120\text{ms}$.

---

### Feature 3: Candidate Ranking & Opportunity Recommendation

#### 3.1 Problem Definition
Produce an individualized feed of opportunities for each student that balances deterministic eligibility (hard gate), semantic relevance, skill overlap, and deadline urgency.

#### 3.2 Architectural Approach: Constrained Multi-Factor Scoring
The ranking engine enforces a hard constraint before scoring:

$$S_{\text{final}} = M_{\text{eligibility}} \times \left( w_1 S_{\text{semantic}} + w_2 S_{\text{skills}} + w_3 S_{\text{urgency}} + w_4 S_{\text{location\_pref}} \right)$$

Where:
- $M_{\text{eligibility}} \in \{0, 1\}$ (Computed deterministically: Batch match $\times$ Degree match $\times$ CGPA match).
- $S_{\text{semantic}} \in [0, 1]$ (Normalized cross-encoder score).
- $S_{\text{skills}} = \frac{|\text{StudentSkills} \cap \text{JobSkills}|}{|\text{JobSkills}|}$.
- $S_{\text{urgency}} = \exp\left(-\frac{\text{days\_until\_deadline}}{14}\right)$.
- Default weights: $w_1 = 0.45, w_2 = 0.35, w_3 = 0.10, w_4 = 0.10$.

#### 3.3 Candidate Models
- Baseline: Multi-factor weighted heuristic formula.
- Advanced Experiment: **LambdaMART / LightGBM Ranker** trained on student bookmark, application click, and acceptance events.

---

### Feature 4: Skill Extraction & Taxonomy Classification (ESCO Normalization)

#### 4.1 Problem Definition
Free-form job descriptions and student profiles describe identical skills with varied vocabulary: *"React.js"*, *"ReactJS"*, *"React 19"*, *"React Native"*. The model must extract skill mentions and normalize them into a canonical ontology (e.g. `skill:react` vs `skill:react_native`).

#### 4.2 Architectural Approach: Token Classifier + Vector KNN Linker
- **Extractor:** Token classification transformer identifies span boundaries.
- **Linker:** Cosine similarity lookup against an embedded dictionary of 13,800 canonical skills from the **ESCO (European Skills, Competences and Occupations)** open taxonomy.

#### 4.3 Candidate Models
- `SkillNER` (SpaCy-based skill matcher).
- `sentence-transformers/all-MiniLM-L6-v2` over ESCO embeddings.

#### 4.4 Accuracy Targets
- Exact Skill Span F1: **$\ge 0.90$**.
- Taxonomy Linkage Accuracy: **$\ge 95.0\%$**.

---

### Feature 5: Multilingual Voice Emotion & Cadence Adaptation

#### 5.1 Problem Definition
Indian students speaking in regional languages (Hindi, Telugu, Tamil, etc.) often exhibit vocal hesitation, pauses, or nervousness when describing their projects. The voice agent must detect conversational cadence and adjust response empathy and pacing accordingly.

#### 5.2 Approach & Boundary
- Managed via Gemini Live multi-modal streaming API audio features and system prompting.
- Sanju evaluates system prompt variations to ensure supportive, collegiate tone in each Indic language without condescension.

---

### Feature 6: ATS Groundedness & Hallucination Verification Classifier

#### 6.1 Problem Definition
In the Resume Studio, when an LLM synthesizes tailored resume bullet points for a job description, there is a dangerous risk that the LLM fabricates false projects, exaggerated metrics, or unverified achievements.

#### 6.2 Architectural Approach: Natural Language Inference (NLI) Verification Gate
Every bullet point in the generated resume must pass through an NLI entailment classifier:
- **Premise:** Verified items from the student's Career Passport.
- **Hypothesis:** Synthesized resume bullet point.
- **Classifier:** `cross-encoder/nli-deberta-v3-small`.
- **Decision Rule:**
  - If $\text{P}(\text{Entailment}) \ge 0.85$ and $\text{P}(\text{Contradiction}) \le 0.05 \implies$ **APPROVED**.
  - Else $\implies$ **FLAGGED AS UNGROUNDED / REJECTED**.

#### 6.3 Evaluation Target
- Hallucination false negative rate (allowing a fake claim through): **$< 0.5\%$**.

---

## 4. Summary Table of Selected ML Candidate Models

| Feature | Primary Model Candidate | Backup / Lightweight Model | Baseline | Primary Evaluation Metric | Target Threshold |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Resume Parser** | Gemini 1.5 Flash (JSON Mode) | GLiNER Base (`urchade/gliner_base-v2.1`) | Regex / Heuristic | Field Extraction Accuracy | $\ge 98.0\%$ |
| **2. Semantic Matching** | `BAAI/bge-large-en-v1.5` + Cross-Encoder | `sentence-transformers/all-MiniLM-L6-v2` | BM25 Keyword Search | NDCG@10 | $\ge 0.85$ |
| **3. Ranking Engine** | Calibrated Multi-Factor Weighted Ranker | LightGBM LambdaMART | Raw Cosine Similarity | MAP@10 / NDCG@5 | $\ge 0.88$ |
| **4. Skill Normalization** | MiniLM Vector KNN Linker | SkillNER Dictionary Matcher | Substring Match | Taxonomy Link Accuracy | $\ge 95.0\%$ |
| **5. Hallucination Gate** | `cross-encoder/nli-deberta-v3-small` | Gemini Grounding Judge | Exact Substring Match | Hallucination Detection Rate | $\ge 99.0\%$ |
