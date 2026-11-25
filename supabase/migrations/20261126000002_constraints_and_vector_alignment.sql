-- =============================================================================
-- Opportunity OS - Constraints, Updated-At Triggers & Vector Alignment
-- Version: 20261126000002
-- Description:
--   1. Safely enforces UNIQUE(user_id, opportunity_id) on public.applications
--      (fails loudly if duplicates exist rather than silently deleting data).
--   2. Safely enforces UNIQUE(opportunity_id) on public.opportunity_eligibility.
--   3. Adds updated_at auto-update triggers on profiles and student_profiles.
--   4. Adds 384-dim MiniLM embedding column + metadata + partial HNSW index
--      alongside existing 768-dim Gemini embeddings, remaining 100% compatible
--      with origin/ml's additive migration (20261125000001_add_minilm_384_embeddings.sql).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Safe Uniqueness Constraint on public.applications (Duplicate Guard)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    dup_count INT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_applications_user_opportunity'
          AND conrelid = 'public.applications'::regclass
    ) THEN
        SELECT COUNT(*) INTO dup_count
        FROM (
            SELECT user_id, opportunity_id
            FROM public.applications
            GROUP BY user_id, opportunity_id
            HAVING COUNT(*) > 1
        ) AS duplicates;

        IF dup_count > 0 THEN
            RAISE EXCEPTION
                'Cannot add uq_applications_user_opportunity: % duplicate (user_id, opportunity_id) pair(s) found in public.applications. Audit and resolve duplicates before applying this migration.',
                dup_count;
        END IF;

        ALTER TABLE public.applications
            ADD CONSTRAINT uq_applications_user_opportunity UNIQUE (user_id, opportunity_id);
    END IF;
END;
$$;

-- -----------------------------------------------------------------------------
-- 2. Safe Uniqueness Constraint on public.opportunity_eligibility (1:1 with opportunities)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    dup_count INT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_opportunity_eligibility_opportunity_id'
          AND conrelid = 'public.opportunity_eligibility'::regclass
    ) THEN
        SELECT COUNT(*) INTO dup_count
        FROM (
            SELECT opportunity_id
            FROM public.opportunity_eligibility
            GROUP BY opportunity_id
            HAVING COUNT(*) > 1
        ) AS duplicates;

        IF dup_count > 0 THEN
            RAISE EXCEPTION
                'Cannot add uq_opportunity_eligibility_opportunity_id: % duplicate opportunity_id(s) found in public.opportunity_eligibility. Audit and resolve duplicates before applying this migration.',
                dup_count;
        END IF;

        ALTER TABLE public.opportunity_eligibility
            ADD CONSTRAINT uq_opportunity_eligibility_opportunity_id UNIQUE (opportunity_id);
    END IF;
END;
$$;

-- -----------------------------------------------------------------------------
-- 3. Automatic updated_at Triggers
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_student_profiles_updated_at ON public.student_profiles;
CREATE TRIGGER trg_student_profiles_updated_at
    BEFORE UPDATE ON public.student_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 4. Dual-Vector Support (Preserve 768-dim Gemini + Add 384-dim MiniLM)
--    Idempotent with origin/ml's 20261125000001_add_minilm_384_embeddings.sql
-- -----------------------------------------------------------------------------
ALTER TABLE public.opportunity_embeddings
    ADD COLUMN IF NOT EXISTS embedding_minilm_384 vector(384),
    ADD COLUMN IF NOT EXISTS embedding_model_id TEXT DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    ADD COLUMN IF NOT EXISTS embedding_model_version TEXT;

CREATE INDEX IF NOT EXISTS idx_embeddings_minilm_384_hnsw
    ON public.opportunity_embeddings
    USING hnsw (embedding_minilm_384 vector_cosine_ops)
    WHERE embedding_minilm_384 IS NOT NULL;
