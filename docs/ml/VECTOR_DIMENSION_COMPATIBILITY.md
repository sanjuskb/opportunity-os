# NexteRaS — Vector Dimension Compatibility Analysis (`pgvector(768)` vs `384`)

## 1. Confirmed Schema Finding
In [supabase/migrations/20261123000001_initial_schema.sql](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261123000001_initial_schema.sql) (line 124), `public.opportunity_embeddings` defines:
```sql
embedding vector(768)
```
with an `ivfflat (embedding vector_cosine_ops)` index (line 289) sized for Google Gemini `text-embedding-004` (`768` dimensions).

Meanwhile, both CPU-friendly Sentence Transformers selected in NexteRaS ML emit **`384` dimensions**:
- `sentence-transformers/all-MiniLM-L6-v2` (Sanju's personal fine-tuning model): **`384`-dim**
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`: **`384`-dim**

Inserting a `384`-dimensional numpy vector into `vector(768)` raises a PostgreSQL `DataError` (`expected 768 dimensions, not 384`). Zero-padding `384 -> 768` alters vector norms unless kept strict, is fragile, and mixes incompatible embedding spaces inside one IVFFlat index.

---

## 2. Trade-Off Comparison Across Options

| Option | Quality & Accuracy | Storage & RAM | Indexing & Query Safety | Migration & Existing Data Safety | Integration Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Keep single `vector(768)` column (Gemini only)** | High for English & cloud search | Baseline (`3 KB` / row) | Single IVFFlat index | Safe, zero migration | Blocks storing Sanju's fine-tuned `all-MiniLM-L6-v2` (`384`-dim) in Postgres |
| **2. Additive `embedding_minilm_384 vector(384)` column (RECOMMENDED)** | Supports BOTH Gemini cloud `768` AND offline/fine-tuned MiniLM `384` cleanly | `~1.5 KB` extra per row + small partial HNSW index | Dedicated partial `HNSW (vector_cosine_ops)` per embedding space — zero space mixing | 100% backward-compatible additive column; `initial_schema.sql` untouched | FastAPI service selects column matching active `model_version` |
| **3. Replace MiniLM with `768`-dim local model (`BAAI/bge-base-en-v1.5`)** | Slightly stronger raw English MTEB, `~440 MB` disk vs `90 MB` | High CPU RAM (`~1.2 GB` vs `~320 MB`), `~3x` slower CPU training | Reuses `vector(768)` if Gemini rows absent (still incompatible if Gemini + BGE mixed!) | Risky mixing two 768 spaces in one column | Breaks Sanju's agreed personal training focus on `all-MiniLM-L6-v2` |
| **4. External local NumPy/FAISS vector store** | Equal to Option 2 | Separate RAM/disk cache | Fast in-memory scan for `< 50k` rows | Zero DB migration needed now | Harder horizontal scaling on multi-replica Cloud Run without shared volume |

---

## 3. Recommended Decision & Safe Deployment Sequence

**Recommendation:** Adopt **Option 2** (additive forward-only migration [20261125000001_add_minilm_384_embeddings.sql](file:///d:/ai%20career%20intelligence%20autonomous%20system/supabase/migrations/20261125000001_add_minilm_384_embeddings.sql)) paired with **in-memory `SemanticMatcher` reranking (Option 4 fallback)** on small top-50 candidate subsets when `pgvector` isn't active locally.

### Exact Coordination & Deployment Sequence (Pending Backend Sign-Off)
1. **Never edit `20261123000001_initial_schema.sql`** — preserve applied schema history verbatim.
2. **Coordinate PR Review with Ramaraju (`develop`):** Review `20261125000001_add_minilm_384_embeddings.sql` before applying `supabase db push` in staging.
3. **Apply Additive Migration:** Zero downtime (`ADD COLUMN IF NOT EXISTS` on nullable columns + partial HNSW `WHERE embedding_minilm_384 IS NOT NULL`).
4. **Dual-Write / Re-index Workers:** ARQ ingestion workers populate `embedding_minilm_384` alongside `embedding_model_version` (`all-MiniLM-L6-v2` or `minilm-nexteras-v1`).
5. **Rollback:** Single `DROP INDEX` + `ALTER TABLE ... DROP COLUMN IF EXISTS` completely reverses the change without touching `embedding vector(768)`.
