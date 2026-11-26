-- =============================================================================
-- Opportunity OS - Private Resumes Storage Bucket, Owner RLS & Upload Metadata
-- Version: 20261127000001
-- Description:
--   1. Provisions private `resumes` bucket in storage.buckets (5 MB cap, PDF/DOCX/TXT/MD/JSON).
--   2. Enables strict owner-only storage.objects RLS scoped to auth.uid() folder prefix.
--   3. Extends public.resumes with file storage, SHA-256, MIME type, and extraction metadata.
-- =============================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'resumes',
    'resumes',
    FALSE,
    5242880,
    ARRAY[
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown',
        'application/json'
    ]
)
ON CONFLICT (id) DO UPDATE
SET public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own resume objects" ON storage.objects;
CREATE POLICY "Users can view own resume objects"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'resumes'
        AND split_part(name, '/', 1) = auth.uid()::text
    );

DROP POLICY IF EXISTS "Users can upload own resume objects" ON storage.objects;
CREATE POLICY "Users can upload own resume objects"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'resumes'
        AND split_part(name, '/', 1) = auth.uid()::text
    );

DROP POLICY IF EXISTS "Users can update own resume objects" ON storage.objects;
CREATE POLICY "Users can update own resume objects"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'resumes'
        AND split_part(name, '/', 1) = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'resumes'
        AND split_part(name, '/', 1) = auth.uid()::text
    );

DROP POLICY IF EXISTS "Users can delete own resume objects" ON storage.objects;
CREATE POLICY "Users can delete own resume objects"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'resumes'
        AND split_part(name, '/', 1) = auth.uid()::text
    );

ALTER TABLE public.resumes
    ADD COLUMN IF NOT EXISTS storage_bucket TEXT,
    ADD COLUMN IF NOT EXISTS storage_path TEXT,
    ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
    ADD COLUMN IF NOT EXISTS mime_type VARCHAR(150),
    ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
    ADD COLUMN IF NOT EXISTS file_sha256 VARCHAR(64),
    ADD COLUMN IF NOT EXISTS raw_text TEXT,
    ADD COLUMN IF NOT EXISTS extraction_status VARCHAR(30) DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS extraction_confidence NUMERIC(4,3),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DROP TRIGGER IF EXISTS trg_resumes_updated_at ON public.resumes;
CREATE TRIGGER trg_resumes_updated_at
    BEFORE UPDATE ON public.resumes
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.resume_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_customizations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own resume versions" ON public.resume_versions;
CREATE POLICY "Users can view own resume versions"
    ON public.resume_versions
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_versions.resume_id AND r.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can view own resume customizations" ON public.resume_customizations;
CREATE POLICY "Users can view own resume customizations"
    ON public.resume_customizations
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_customizations.resume_id AND r.user_id = auth.uid()
        )
    );
