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
