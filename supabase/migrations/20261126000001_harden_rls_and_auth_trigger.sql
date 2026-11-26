-- =============================================================================
-- Opportunity OS - RLS Hardening & Secure Auth Profile Trigger
-- Version: 20261126000001
-- Description:
--   1. Enables Row Level Security (RLS) on all 25 public tables.
--   2. Replaces incomplete/missing policies with least-privilege ownership,
--      public read, and append-only audit policies.
--   3. Adds a SECURITY DEFINER auth.users signup trigger with restricted
--      search_path to safely provision public.profiles.
--   4. Keeps opportunity_embeddings, opportunity_sources, and analytics reads
--      inaccessible to ordinary client roles (service_role / backend only).
--   5. Prevents direct client mutation of approval_requests, agent_events,
--      and browser_execution_logs.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Enable Row Level Security on all 25 public tables
-- -----------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.education ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.career_passports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunity_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunity_eligibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunity_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_customizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.browser_execution_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opportunity_monitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 2. Public Read-Only Catalogs (anon + authenticated SELECT, service_role writes)
-- -----------------------------------------------------------------------------

-- 2a. opportunities (replace initial authenticated-only policy with anon + authenticated)
DROP POLICY IF EXISTS "Public opportunities are viewable by all authenticated users" ON public.opportunities;
DROP POLICY IF EXISTS "Opportunities are publicly readable" ON public.opportunities;
CREATE POLICY "Opportunities are publicly readable"
    ON public.opportunities
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- 2b. opportunity_eligibility
DROP POLICY IF EXISTS "Opportunity eligibility is publicly readable" ON public.opportunity_eligibility;
CREATE POLICY "Opportunity eligibility is publicly readable"
    ON public.opportunity_eligibility
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- 2c. skills
DROP POLICY IF EXISTS "Skills taxonomy is publicly readable" ON public.skills;
CREATE POLICY "Skills taxonomy is publicly readable"
    ON public.skills
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- Note: opportunity_sources and opportunity_embeddings have RLS enabled with NO
-- anon/authenticated policies, restricting them strictly to service_role.

-- -----------------------------------------------------------------------------
-- 3. User Identity & Profile Provisioning (auth.users -> public.profiles)
-- -----------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Secure signup trigger: always binds profile.id = NEW.id from auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(NEW.email, ''),
        NULLIF(NEW.raw_user_meta_data ->> 'full_name', ''),
        NULLIF(NEW.raw_user_meta_data ->> 'avatar_url', '')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- -----------------------------------------------------------------------------
-- 4. Student Academic & Preference Tables (Direct user_id or student_id ownership)
-- -----------------------------------------------------------------------------

-- 4a. student_profiles
DROP POLICY IF EXISTS "Users can view own student profile" ON public.student_profiles;
CREATE POLICY "Users can view own student profile"
    ON public.student_profiles FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own student profile" ON public.student_profiles;
CREATE POLICY "Users can insert own student profile"
    ON public.student_profiles FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own student profile" ON public.student_profiles;
CREATE POLICY "Users can update own student profile"
    ON public.student_profiles FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own student profile" ON public.student_profiles;
CREATE POLICY "Users can delete own student profile"
    ON public.student_profiles FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 4b. education (owned via student_profiles.user_id)
DROP POLICY IF EXISTS "Users can view own education" ON public.education;
CREATE POLICY "Users can view own education"
    ON public.education FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = education.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own education" ON public.education;
CREATE POLICY "Users can insert own education"
    ON public.education FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = education.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update own education" ON public.education;
CREATE POLICY "Users can update own education"
    ON public.education FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = education.student_id AND sp.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = education.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own education" ON public.education;
CREATE POLICY "Users can delete own education"
    ON public.education FOR DELETE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = education.student_id AND sp.user_id = auth.uid()
        )
    );

-- 4c. user_preferences
DROP POLICY IF EXISTS "Users can view own preferences" ON public.user_preferences;
CREATE POLICY "Users can view own preferences"
    ON public.user_preferences FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own preferences" ON public.user_preferences;
CREATE POLICY "Users can insert own preferences"
    ON public.user_preferences FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own preferences" ON public.user_preferences;
CREATE POLICY "Users can update own preferences"
    ON public.user_preferences FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own preferences" ON public.user_preferences;
CREATE POLICY "Users can delete own preferences"
    ON public.user_preferences FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 4d. career_passports (owned via student_profiles.user_id)
DROP POLICY IF EXISTS "Users can view own career passport" ON public.career_passports;
CREATE POLICY "Users can view own career passport"
    ON public.career_passports FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = career_passports.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own career passport" ON public.career_passports;
CREATE POLICY "Users can insert own career passport"
    ON public.career_passports FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = career_passports.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update own career passport" ON public.career_passports;
CREATE POLICY "Users can update own career passport"
    ON public.career_passports FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = career_passports.student_id AND sp.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = career_passports.student_id AND sp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own career passport" ON public.career_passports;
CREATE POLICY "Users can delete own career passport"
    ON public.career_passports FOR DELETE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.student_profiles sp
            WHERE sp.id = career_passports.student_id AND sp.user_id = auth.uid()
        )
    );

-- -----------------------------------------------------------------------------
-- 5. Saved Opportunities, Applications & Resumes
-- -----------------------------------------------------------------------------

-- 5a. saved_opportunities
DROP POLICY IF EXISTS "Users can view own saved opportunities" ON public.saved_opportunities;
CREATE POLICY "Users can view own saved opportunities"
    ON public.saved_opportunities FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own saved opportunities" ON public.saved_opportunities;
CREATE POLICY "Users can insert own saved opportunities"
    ON public.saved_opportunities FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own saved opportunities" ON public.saved_opportunities;
CREATE POLICY "Users can update own saved opportunities"
    ON public.saved_opportunities FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own saved opportunities" ON public.saved_opportunities;
CREATE POLICY "Users can delete own saved opportunities"
    ON public.saved_opportunities FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 5b. applications
DROP POLICY IF EXISTS "Users can view own applications" ON public.applications;
CREATE POLICY "Users can view own applications"
    ON public.applications FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own applications" ON public.applications;
CREATE POLICY "Users can insert own applications"
    ON public.applications FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own applications" ON public.applications;
CREATE POLICY "Users can update own applications"
    ON public.applications FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own applications" ON public.applications;
CREATE POLICY "Users can delete own applications"
    ON public.applications FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 5c. resumes
DROP POLICY IF EXISTS "Users can view own resumes" ON public.resumes;
CREATE POLICY "Users can view own resumes"
    ON public.resumes FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own resumes" ON public.resumes;
CREATE POLICY "Users can insert own resumes"
    ON public.resumes FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own resumes" ON public.resumes;
CREATE POLICY "Users can update own resumes"
    ON public.resumes FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own resumes" ON public.resumes;
CREATE POLICY "Users can delete own resumes"
    ON public.resumes FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 5d. resume_versions (owned via resumes.user_id)
DROP POLICY IF EXISTS "Users can view own resume versions" ON public.resume_versions;
CREATE POLICY "Users can view own resume versions"
    ON public.resume_versions FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_versions.resume_id AND r.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own resume versions" ON public.resume_versions;
CREATE POLICY "Users can insert own resume versions"
    ON public.resume_versions FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_versions.resume_id AND r.user_id = auth.uid()
        )
    );

-- 5e. resume_customizations (owned via resumes.user_id)
DROP POLICY IF EXISTS "Users can view own resume customizations" ON public.resume_customizations;
CREATE POLICY "Users can view own resume customizations"
    ON public.resume_customizations FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_customizations.resume_id AND r.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own resume customizations" ON public.resume_customizations;
CREATE POLICY "Users can insert own resume customizations"
    ON public.resume_customizations FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.resumes r
            WHERE r.id = resume_customizations.resume_id AND r.user_id = auth.uid()
        )
    );

-- -----------------------------------------------------------------------------
-- 6. Agents, Approvals & Append-Only Audit Logs
-- -----------------------------------------------------------------------------

-- 6a. agent_sessions (client read-only; backend service_role manages lifecycle)
DROP POLICY IF EXISTS "Users can view own agent sessions" ON public.agent_sessions;
CREATE POLICY "Users can view own agent sessions"
    ON public.agent_sessions FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

-- 6b. agent_events (append-only: client SELECT only via session ownership; service_role writes)
DROP POLICY IF EXISTS "Users can view own agent events" ON public.agent_events;
CREATE POLICY "Users can view own agent events"
    ON public.agent_events FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.agent_sessions s
            WHERE s.id = agent_events.session_id AND s.user_id = auth.uid()
        )
    );

-- 6c. approval_requests (client SELECT only; decisions & state transitions via backend API / service_role)
-- Prevents direct client self-approval or tampering with payload_summary/action_type.
DROP POLICY IF EXISTS "Users can view own approval requests" ON public.approval_requests;
CREATE POLICY "Users can view own approval requests"
    ON public.approval_requests FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

-- 6d. browser_execution_logs (append-only: client SELECT only via session ownership; service_role writes)
DROP POLICY IF EXISTS "Users can view own browser execution logs" ON public.browser_execution_logs;
CREATE POLICY "Users can view own browser execution logs"
    ON public.browser_execution_logs FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.agent_sessions s
            WHERE s.id = browser_execution_logs.session_id AND s.user_id = auth.uid()
        )
    );

-- -----------------------------------------------------------------------------
-- 7. Conversations, Voice, Notifications, Monitors & Analytics
-- -----------------------------------------------------------------------------

-- 7a. conversations
DROP POLICY IF EXISTS "Users can view own conversations" ON public.conversations;
CREATE POLICY "Users can view own conversations"
    ON public.conversations FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own conversations" ON public.conversations;
CREATE POLICY "Users can insert own conversations"
    ON public.conversations FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own conversations" ON public.conversations;
CREATE POLICY "Users can update own conversations"
    ON public.conversations FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own conversations" ON public.conversations;
CREATE POLICY "Users can delete own conversations"
    ON public.conversations FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 7b. conversation_messages (owned via conversations.user_id)
DROP POLICY IF EXISTS "Users can view own conversation messages" ON public.conversation_messages;
CREATE POLICY "Users can view own conversation messages"
    ON public.conversation_messages FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = conversation_messages.conversation_id AND c.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can insert own conversation messages" ON public.conversation_messages;
CREATE POLICY "Users can insert own conversation messages"
    ON public.conversation_messages FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = conversation_messages.conversation_id AND c.user_id = auth.uid()
        )
    );

-- 7c. voice_sessions
DROP POLICY IF EXISTS "Users can view own voice sessions" ON public.voice_sessions;
CREATE POLICY "Users can view own voice sessions"
    ON public.voice_sessions FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own voice sessions" ON public.voice_sessions;
CREATE POLICY "Users can insert own voice sessions"
    ON public.voice_sessions FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- 7d. notifications (client can read & mark read; backend service_role inserts)
DROP POLICY IF EXISTS "Users can view own notifications" ON public.notifications;
CREATE POLICY "Users can view own notifications"
    ON public.notifications FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own notifications" ON public.notifications;
CREATE POLICY "Users can update own notifications"
    ON public.notifications FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 7e. opportunity_monitors
DROP POLICY IF EXISTS "Users can view own opportunity monitors" ON public.opportunity_monitors;
CREATE POLICY "Users can view own opportunity monitors"
    ON public.opportunity_monitors FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own opportunity monitors" ON public.opportunity_monitors;
CREATE POLICY "Users can insert own opportunity monitors"
    ON public.opportunity_monitors FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own opportunity monitors" ON public.opportunity_monitors;
CREATE POLICY "Users can update own opportunity monitors"
    ON public.opportunity_monitors FOR UPDATE TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own opportunity monitors" ON public.opportunity_monitors;
CREATE POLICY "Users can delete own opportunity monitors"
    ON public.opportunity_monitors FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 7f. analytics_events (authenticated users can log own events; reads restricted to service_role)
DROP POLICY IF EXISTS "Users can insert own analytics events" ON public.analytics_events;
CREATE POLICY "Users can insert own analytics events"
    ON public.analytics_events FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);
