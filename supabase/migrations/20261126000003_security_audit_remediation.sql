-- =============================================================================
-- Opportunity OS - Security Audit Remediation
-- Version: 20261126000003
-- Description:
--   1. Hardens public.handle_new_user() with SET search_path = public, pg_temp,
--      explicit OWNER TO postgres, and deterministic unique placeholder email
--      when auth.users.email is NULL or empty.
--   2. Removes direct authenticated UPDATE on public.applications and restricts
--      authenticated INSERT/DELETE to draft/saved states; all status transitions
--      and submission metadata are controlled by FastAPI (service_role).
--   3. Restricts authenticated UPDATE on public.notifications to (is_read).
--   4. Restricts authenticated UPDATE on public.profiles to
--      (full_name, avatar_url, preferred_language), preventing email tampering.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Harden Auth Signup Trigger (public.handle_new_user)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    safe_email TEXT;
BEGIN
    safe_email := COALESCE(
        NULLIF(BTRIM(NEW.email), ''),
        NEW.id::text || '@no-email.local'
    );

    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        safe_email,
        NULLIF(NEW.raw_user_meta_data ->> 'full_name', ''),
        NULLIF(NEW.raw_user_meta_data ->> 'avatar_url', '')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

ALTER FUNCTION public.handle_new_user() OWNER TO postgres;
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;

-- -----------------------------------------------------------------------------
-- 2. Restrict public.applications Client Mutations (Backend-Controlled Status)
-- -----------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can update own applications" ON public.applications;
REVOKE UPDATE ON public.applications FROM authenticated;

DROP POLICY IF EXISTS "Users can insert own applications" ON public.applications;
CREATE POLICY "Users can insert own draft applications"
    ON public.applications
    FOR INSERT
    TO authenticated
    WITH CHECK (
        auth.uid() = user_id
        AND COALESCE(status, 'drafting') IN ('drafting', 'saved')
        AND COALESCE(submission_method, 'manual') = 'manual'
        AND applied_at IS NULL
    );

DROP POLICY IF EXISTS "Users can delete own applications" ON public.applications;
CREATE POLICY "Users can delete own draft applications"
    ON public.applications
    FOR DELETE
    TO authenticated
    USING (
        auth.uid() = user_id
        AND status IN ('drafting', 'saved')
    );

-- -----------------------------------------------------------------------------
-- 3. Restrict public.notifications UPDATE to is_read Only
-- -----------------------------------------------------------------------------
REVOKE UPDATE ON public.notifications FROM authenticated;
GRANT UPDATE (is_read) ON public.notifications TO authenticated;

-- -----------------------------------------------------------------------------
-- 4. Restrict public.profiles UPDATE to User-Editable Fields (Protect email)
-- -----------------------------------------------------------------------------
REVOKE UPDATE ON public.profiles FROM authenticated;
GRANT UPDATE (full_name, avatar_url, preferred_language) ON public.profiles TO authenticated;
