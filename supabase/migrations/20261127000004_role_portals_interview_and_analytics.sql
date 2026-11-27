-- Migration 20261127000004: Role Portals, Mock Interview Sessions & Institutional Verifications
-- Additive-only schema supporting persisted workspace role selection (student/company/university),
-- Gemini-powered multilingual interview sessions, and university credential verifications.

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS user_role VARCHAR(30) DEFAULT 'student';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_profiles_user_role'
    ) THEN
        ALTER TABLE public.profiles
            ADD CONSTRAINT chk_profiles_user_role
            CHECK (user_role IN ('student', 'company', 'university'));
    END IF;
END $$;

GRANT UPDATE (user_role) ON public.profiles TO authenticated;

CREATE TABLE IF NOT EXISTS public.interview_sessions (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    target_role VARCHAR(200) NOT NULL,
    language VARCHAR(15) DEFAULT 'en',
    questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    responses JSONB NOT NULL DEFAULT '[]'::jsonb,
    feedback JSONB NOT NULL DEFAULT '[]'::jsonb,
    overall_score NUMERIC(5,2),
    status VARCHAR(30) DEFAULT 'in_progress',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.university_verifications (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    student_profile_id UUID NOT NULL REFERENCES public.student_profiles(id) ON DELETE CASCADE,
    verified_by_user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'verified',
    credential_type VARCHAR(100) NOT NULL DEFAULT 'academic_transcript',
    notes TEXT,
    verified_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_university_verifications_student UNIQUE (student_profile_id)
);

ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.university_verifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own interview sessions" ON public.interview_sessions;
CREATE POLICY "Users can view own interview sessions"
    ON public.interview_sessions FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own interview sessions" ON public.interview_sessions;
CREATE POLICY "Users can manage own interview sessions"
    ON public.interview_sessions FOR ALL TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Authenticated users can view university verifications" ON public.university_verifications;
CREATE POLICY "Authenticated users can view university verifications"
    ON public.university_verifications FOR SELECT TO authenticated
    USING (true);
