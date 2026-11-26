-- =============================================================================
-- Opportunity OS - Canonical 384-dim Embedding Pipeline Metadata & Constraints
-- Version: 20261126000004
-- Description:
--   1. Adds operational pipeline metadata columns to public.opportunity_embeddings
--      for the canonical 384-dim sentence-transformers/all-MiniLM-L6-v2 pipeline:
--      content_hash, embedding_status, error_message, retry_count, updated_at.
--   2. Preserves both existing vector columns (legacy embedding vector(768) and
--      canonical embedding_minilm_384 vector(384)), existing indexes, FKs, and
--      service_role-only RLS.
--   3. Backfills existing non-null 384-dim rows to embedding_status = 'ready'.
--   4. Enforces valid status values, non-negative retry_count, and the invariant
--      that 'ready' rows always have a non-null embedding_minilm_384 vector.
-- =============================================================================

ALTER TABLE public.opportunity_embeddings
    ADD COLUMN IF NOT EXISTS content_hash TEXT,
    ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS retry_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Backfill existing rows that already store a canonical 384-dim MiniLM vector
UPDATE public.opportunity_embeddings
SET embedding_status = 'ready',
    updated_at = COALESCE(updated_at, NOW())
WHERE embedding_minilm_384 IS NOT NULL
  AND embedding_model_id = 'sentence-transformers/all-MiniLM-L6-v2'
  AND embedding_status = 'pending';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_opportunity_embeddings_status'
          AND conrelid = 'public.opportunity_embeddings'::regclass
    ) THEN
        ALTER TABLE public.opportunity_embeddings
            ADD CONSTRAINT chk_opportunity_embeddings_status
            CHECK (embedding_status IN ('pending', 'ready', 'failed'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_opportunity_embeddings_retry_count_non_negative'
          AND conrelid = 'public.opportunity_embeddings'::regclass
    ) THEN
        ALTER TABLE public.opportunity_embeddings
            ADD CONSTRAINT chk_opportunity_embeddings_retry_count_non_negative
            CHECK (retry_count >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_opportunity_embeddings_ready_requires_vector'
          AND conrelid = 'public.opportunity_embeddings'::regclass
    ) THEN
        ALTER TABLE public.opportunity_embeddings
            ADD CONSTRAINT chk_opportunity_embeddings_ready_requires_vector
            CHECK (embedding_status <> 'ready' OR embedding_minilm_384 IS NOT NULL);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_opportunity_embeddings_status
    ON public.opportunity_embeddings (embedding_status);

DROP TRIGGER IF EXISTS trg_opportunity_embeddings_updated_at ON public.opportunity_embeddings;
CREATE TRIGGER trg_opportunity_embeddings_updated_at
    BEFORE UPDATE ON public.opportunity_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
