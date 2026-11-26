-- =============================================================================
-- NexteRaS Proposed Migration (ml branch ONLY — NOT APPLIED TO PRODUCTION)
-- Version: 20261125000001
-- Purpose: Backward-compatible support for 384-dim all-MiniLM-L6-v2 / multilingual-MiniLM
--          embeddings alongside existing Gemini text-embedding-004 vector(768).
-- Safety: Forward-only additive columns + partial HNSW index. Zero data loss.
-- Rollback:
--   DROP INDEX IF EXISTS public.idx_embeddings_minilm_384_hnsw;
--   ALTER TABLE public.opportunity_embeddings
--     DROP COLUMN IF EXISTS embedding_minilm_384,
--     DROP COLUMN IF EXISTS embedding_model_id,
--     DROP COLUMN IF EXISTS embedding_model_version;
-- =============================================================================

ALTER TABLE public.opportunity_embeddings
    ADD COLUMN IF NOT EXISTS embedding_minilm_384 vector(384),
    ADD COLUMN IF NOT EXISTS embedding_model_id TEXT DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    ADD COLUMN IF NOT EXISTS embedding_model_version TEXT;

-- Partial HNSW index avoids indexing null 384-dim vectors and lets vector(768) remain untouched.
CREATE INDEX IF NOT EXISTS idx_embeddings_minilm_384_hnsw
    ON public.opportunity_embeddings
    USING hnsw (embedding_minilm_384 vector_cosine_ops)
    WHERE embedding_minilm_384 IS NOT NULL;
