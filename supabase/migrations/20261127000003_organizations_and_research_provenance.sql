-- =============================================================================
-- Opportunity OS - Organizations (Firmographics) & Research Provenance
-- Version: 20261127000003
-- Description:
--   1. Creates public.organizations table for Crustdata company intelligence & verification.
--   2. Enables RLS with public SELECT and service_role-managed enrichment writes.
--   3. Extends public.opportunities and public.opportunity_sources with provenance metadata.
-- =============================================================================

SET LOCAL search_path = public, extensions;

CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name TEXT NOT NULL,
    domain TEXT UNIQUE,
    industry TEXT,
    headcount_range TEXT,
    funding_stage TEXT,
    description TEXT,
    hiring_velocity_score NUMERIC(5,2),
    is_verified BOOLEAN DEFAULT FALSE,
    crustdata_payload JSONB DEFAULT '{}',
    last_enriched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organizations_name_lower
    ON public.organizations (lower(name));

DROP TRIGGER IF EXISTS trg_organizations_updated_at ON public.organizations;
CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON public.organizations
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organizations catalog is publicly readable" ON public.organizations;
CREATE POLICY "Organizations catalog is publicly readable"
    ON public.organizations
    FOR SELECT
    TO anon, authenticated
    USING (true);

ALTER TABLE public.opportunities
    ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS content_hash TEXT,
    ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(4,3) DEFAULT 0.800,
    ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_opportunities_source_url
    ON public.opportunities (source_url);

ALTER TABLE public.opportunity_sources
    ADD COLUMN IF NOT EXISTS last_response_code INT,
    ADD COLUMN IF NOT EXISTS requests_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DROP TRIGGER IF EXISTS trg_opportunity_sources_updated_at ON public.opportunity_sources;
CREATE TRIGGER trg_opportunity_sources_updated_at
    BEFORE UPDATE ON public.opportunity_sources
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
