-- =============================================================================
-- Opportunity OS - Extended Eligibility Rules & Student Vector Embeddings
-- Version: 20261127000002
-- Description:
--   1. Adds full deterministic ML eligibility columns to public.opportunity_eligibility
--      (academic years, backlogs, experience, locations, remote, citizenship, preferred skills).
--   2. Adds student academic & matching preference fields to public.student_profiles.
--   3. Provisions public.student_embeddings (384-dim MiniLM + HNSW index + RLS).
-- =============================================================================

SET LOCAL search_path = public, extensions;

ALTER TABLE public.opportunity_eligibility
    ADD COLUMN IF NOT EXISTS eligible_academic_years INT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS max_active_backlogs INT,
    ADD COLUMN IF NOT EXISTS min_experience_months INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS allowed_locations TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS remote_allowed BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS required_citizenship TEXT,
    ADD COLUMN IF NOT EXISTS preferred_skills TEXT[] DEFAULT '{}';

ALTER TABLE public.student_profiles
    ADD COLUMN IF NOT EXISTS current_academic_year INT,
    ADD COLUMN IF NOT EXISTS active_backlogs INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS experience_months INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS citizenship TEXT,
    ADD COLUMN IF NOT EXISTS skills TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS preferred_locations TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS open_to_relocate BOOLEAN DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS public.student_embeddings (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    embedding_minilm_384 vector(384),
    content_hash TEXT,
    embedding_model_id TEXT DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_embeddings_minilm_384_hnsw
    ON public.student_embeddings
    USING hnsw (embedding_minilm_384 vector_cosine_ops)
    WHERE embedding_minilm_384 IS NOT NULL;

DROP TRIGGER IF EXISTS trg_student_embeddings_updated_at ON public.student_embeddings;
CREATE TRIGGER trg_student_embeddings_updated_at
    BEFORE UPDATE ON public.student_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.student_embeddings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own student embeddings" ON public.student_embeddings;
CREATE POLICY "Users can view own student embeddings"
    ON public.student_embeddings
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

