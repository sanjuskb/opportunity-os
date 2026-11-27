-- Seed data for Opportunity OS development
INSERT INTO public.skills (name, category) VALUES
('Python', 'technical'),
('TypeScript', 'technical'),
('React', 'technical'),
('FastAPI', 'technical'),
('SQL', 'technical'),
('Machine Learning', 'technical'),
('Data Analysis', 'technical'),
('Docker', 'devops'),
('Communication', 'soft_skills')
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.opportunities (
    id, title, organization, location, type, description, stipend_or_salary, source_url, source_provider
) VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'AI Research Intern',
    'AI4Bharat (IIT Madras)',
    'Chennai / Remote',
    'internship',
    'Work on speech and Indic language NLP models for Indian regional languages.',
    'INR 35,000 / month',
    'https://ai4bharat.iitm.ac.in/careers',
    'olostep'
),
(
    '00000000-0000-0000-0000-000000000002',
    'Software Engineering Intern - Frontend',
    'Postman India',
    'Bengaluru, Karnataka',
    'internship',
    'Design modern developer experiences with Next.js and TypeScript.',
    'INR 50,000 / month',
    'https://www.postman.com/careers',
    'crustdata'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.opportunity_eligibility (
    opportunity_id,
    eligible_batches,
    eligible_degrees,
    eligible_branches,
    min_cgpa,
    required_skills,
    preferred_skills,
    allowed_locations,
    remote_allowed,
    max_active_backlogs
) VALUES
(
    '00000000-0000-0000-0000-000000000001',
    ARRAY[2026, 2027, 2028],
    ARRAY['B.Tech', 'B.E.', 'M.Tech'],
    ARRAY['Computer Science', 'AI & Data Science', 'Electrical Engineering'],
    7.00,
    ARRAY['Python', 'Machine Learning'],
    ARRAY['PyTorch', 'NLP'],
    ARRAY['Chennai', 'Remote'],
    TRUE,
    0
),
(
    '00000000-0000-0000-0000-000000000002',
    ARRAY[2026, 2027],
    ARRAY['B.Tech', 'B.E.', 'BCA', 'MCA'],
    ARRAY['Computer Science', 'Information Technology'],
    7.50,
    ARRAY['TypeScript', 'React'],
    ARRAY['Next.js', 'REST APIs'],
    ARRAY['Bengaluru'],
    FALSE,
    0
)
ON CONFLICT (opportunity_id) DO NOTHING;
