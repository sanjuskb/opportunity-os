-- =============================================================================
-- Opportunity OS - Initial PostgreSQL Migration with pgvector
-- Version: 20261123000001
-- Description: Core schema for students, opportunities, resumes, agents, voice & audit
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Profiles (linked with Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Student Profiles
CREATE TABLE IF NOT EXISTS public.student_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    college_name TEXT NOT NULL,
    degree TEXT NOT NULL,
    branch TEXT NOT NULL,
    graduation_year INT NOT NULL,
    cgpa NUMERIC(4,2),
    state TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Education
CREATE TABLE IF NOT EXISTS public.education (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES public.student_profiles(id) ON DELETE CASCADE,
    institution TEXT NOT NULL,
    degree TEXT NOT NULL,
    field_of_study TEXT NOT NULL,
    start_year INT NOT NULL,
    end_year INT,
    score TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Skills
CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) DEFAULT 'technical',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. User Preferences
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    preferred_roles TEXT[] DEFAULT '{}',
    preferred_locations TEXT[] DEFAULT '{}',
    remote_only BOOLEAN DEFAULT FALSE,
    min_stipend NUMERIC(10,2) DEFAULT 0,
    notification_frequency VARCHAR(20) DEFAULT 'daily',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Career Passports
CREATE TABLE IF NOT EXISTS public.career_passports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL UNIQUE REFERENCES public.student_profiles(id) ON DELETE CASCADE,
    verified_achievements JSONB DEFAULT '[]',
    coursework JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Opportunities
CREATE TABLE IF NOT EXISTS public.opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    location TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    stipend_or_salary TEXT,
    deadline TIMESTAMPTZ,
    source_url TEXT NOT NULL,
    source_provider VARCHAR(50) NOT NULL,
    retrieval_timestamp TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    raw_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Opportunity Sources
CREATE TABLE IF NOT EXISTS public.opportunity_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    domain TEXT NOT NULL,
    last_scraped_at TIMESTAMPTZ,
    scrape_frequency_hours INT DEFAULT 24,
    status VARCHAR(20) DEFAULT 'healthy'
);

-- 9. Opportunity Eligibility
CREATE TABLE IF NOT EXISTS public.opportunity_eligibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL REFERENCES public.opportunities(id) ON DELETE CASCADE,
    eligible_batches INT[] DEFAULT '{}',
    eligible_degrees TEXT[] DEFAULT '{}',
    eligible_branches TEXT[] DEFAULT '{}',
    min_cgpa NUMERIC(4,2),
    required_skills TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Opportunity Embeddings (pgvector: 768 dimensions for Gemini text-embedding-004)
CREATE TABLE IF NOT EXISTS public.opportunity_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID NOT NULL UNIQUE REFERENCES public.opportunities(id) ON DELETE CASCADE,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Saved Opportunities
CREATE TABLE IF NOT EXISTS public.saved_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES public.opportunities(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    UNIQUE(user_id, opportunity_id)
);

-- 12. Applications
CREATE TABLE IF NOT EXISTS public.applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES public.opportunities(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'drafting',
    applied_at TIMESTAMPTZ,
    submission_method VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Resumes
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    master_content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. Resume Versions
CREATE TABLE IF NOT EXISTS public.resume_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content JSONB NOT NULL,
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 15. Resume Customizations
CREATE TABLE IF NOT EXISTS public.resume_customizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES public.opportunities(id) ON DELETE CASCADE,
    tailored_content JSONB NOT NULL,
    alignment_score NUMERIC(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 16. Agent Sessions
CREATE TABLE IF NOT EXISTS public.agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    state JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 17. Agent Events
CREATE TABLE IF NOT EXISTS public.agent_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
    node_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 18. Approval Requests (CRITICAL HUMAN-IN-THE-LOOP GATE)
CREATE TABLE IF NOT EXISTS public.approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES public.opportunities(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    payload_summary JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    user_decision_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 19. Browser Execution Logs (Audit Trail)
CREATE TABLE IF NOT EXISTS public.browser_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    approval_request_id UUID REFERENCES public.approval_requests(id) ON DELETE SET NULL,
    session_id UUID NOT NULL REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
    step_description TEXT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_selector TEXT,
    screenshot_url TEXT,
    is_success BOOLEAN NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 20. Conversations
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'Career Consultation',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 21. Conversation Messages
CREATE TABLE IF NOT EXISTS public.conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 22. Voice Sessions
CREATE TABLE IF NOT EXISTS public.voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    detected_language VARCHAR(10) DEFAULT 'en',
    audio_duration_seconds NUMERIC(8,2) DEFAULT 0,
    transcript TEXT,
    status VARCHAR(30) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 23. Notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'opportunity_match',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 24. Opportunity Monitors (Scheduled Tracking)
CREATE TABLE IF NOT EXISTS public.opportunity_monitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    target_organization VARCHAR(255) NOT NULL,
    criteria JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 25. Analytics Events
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    event_name VARCHAR(100) NOT NULL,
    event_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for high-throughput queries
CREATE INDEX IF NOT EXISTS idx_opportunities_type ON public.opportunities(type);
CREATE INDEX IF NOT EXISTS idx_opportunities_created ON public.opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON public.approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON public.opportunity_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Row Level Security (RLS) Enablement
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.career_passports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Standard RLS Policies: Users own their private data
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Public opportunities are viewable by all authenticated users"
ON public.opportunities FOR SELECT TO authenticated USING (true);
