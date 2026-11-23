# Opportunity OS — Feature Traceability Matrix

## 1. Traceability Framework & Governance

This matrix maps every agreed product capability of **Opportunity OS** from the student problem statement down to technical components, database dependencies, external integrations, security checkpoints, and verifiable test scenarios.

### Ownership Standard
- **Sanju:** All Frontend Architecture & Implementation, UI/UX, Voice Orb Client, **All Machine Learning (ML)** Model Selection, Embeddings, Training Experiments under `experiments/`, and Offline Evaluation.
- **Ramaraju:** All Backend API Services (`apps/api`), Database Architecture (`supabase/migrations`), LangGraph State Machines, Voice Backend Proxy, Olostep & Crustdata Integrations, Playwright Execution.
- **Shared:** System Architecture, Contracts, End-to-End Integration, Deployment.

---

## 2. Feature Traceability Register

### 2.1 Multilingual Student Onboarding & Preference Profile
- **Student Problem Solved:** Indian students face language barriers and confusing account setup on traditional job boards.
- **User Journey:** Student selects native language (`hi`, `te`, `ta`, etc.), inputs college details, branch, graduation batch, and desired career tracks.
- **Frontend Component:** `apps/web/src/app/(auth)/register/page.tsx`, `LanguageSelector.tsx`
- **Backend Responsibility:** User registration, JWT issuance, profile ingestion endpoint.
- **Database Dependency:** `public.profiles`, `public.student_profiles`, `public.user_preferences`
- **AI/ML/Agent Dependency:** Language detection fallback; student intent extraction.
- **External Provider Dependency:** Supabase Auth.
- **Security & Privacy:** Passwords managed exclusively by Supabase Auth; no plain passwords in backend memory.
- **Acceptance Criteria:** Profile successfully saved with validated graduation year ($2024 \le \text{year} \le 2030$) and supported regional language.
- **Test Scenario:** `TEST-AUTH-01`: Register user with Telugu language selection; verify profile row created and language persisted.
- **Primary Owner:** Sanju (Frontend) / Ramaraju (Backend Profile Endpoints).

---

### 2.2 Living Career Passport (Zero-Hallucination Achievement Store)
- **Student Problem Solved:** Students forget projects, certifications, or coursework, leading to inconsistent or fabricated resume data.
- **User Journey:** Student builds a verified portfolio of coursework, GitHub projects, hackathon finishes, and skills.
- **Frontend Component:** `apps/web/src/app/career-passport/page.tsx`, `AcademicSummary.tsx`, `VerifiedSkills.tsx`
- **Backend Responsibility:** CRUD endpoints for career passport items; verification audit tags.
- **Database Dependency:** `public.career_passports`, `public.education`, `public.skills`
- **AI/ML/Agent Dependency:** Sanju's skill classification and ontology mapping model.
- **External Provider Dependency:** None.
- **Security & Privacy:** Enforce RLS (`auth.uid() = user_id`); prevent unauthorized access to student academic records.
- **Acceptance Criteria:** Items saved to passport cannot be altered by autonomous agents without user confirmation.
- **Test Scenario:** `TEST-PASSPORT-01`: Add B.Tech coursework and Python skill; verify retrieval via `@opportunity-os/api-client`.
- **Primary Owner:** Sanju (UI & Skill Ontology) / Ramaraju (Backend & Persistence).

---

### 2.3 Multilingual Voice-First Interaction (Voice Orb)
- **Student Problem Solved:** Students from non-English backgrounds struggle to navigate dense, text-heavy desktop career portals.
- **User Journey:** Student taps the 3D Voice Orb and speaks naturally in native or code-mixed language (e.g. Hinglish: *"Mujhe remote frontend internship chahiye"*).
- **Frontend Component:** `apps/web/src/components/voice/VoiceOrb.tsx`, Web Audio API streaming hook (`useVoiceStream.ts`).
- **Backend Responsibility:** WebSocket gateway (`/voice/stream`), PCM audio buffering, session state manager.
- **Database Dependency:** `public.voice_sessions`, `public.conversation_messages`
- **AI/ML/Agent Dependency:** Gemini Live bidirectional audio streaming; Sanju's voice latency & phonetic WER evaluation pipeline.
- **External Provider Dependency:** Google Gemini Live Audio API.
- **Security & Privacy:** Audio streams are ephemeral in RAM; no permanent raw audio storage; transcripts stored only with student consent.
- **Acceptance Criteria:** Round-trip latency $< 650\text{ ms}$; natural code-switching comprehension without speech recognition crash.
- **Test Scenario:** `TEST-VOICE-01`: Stream 16kHz PCM audio chunk to `/voice/stream`; verify audio response packet returned within timeout.
- **Primary Owner:** Sanju (Voice UI & Audio Evaluation) / Ramaraju (WebSocket Gateway & Gemini Live Proxy).

---

### 2.4 Opportunity Discovery & Intelligent Web Scraping
- **Student Problem Solved:** High-quality internships and government schemes in India are scattered across hundreds of disparate company and college sites.
- **User Journey:** Student queries or browses freshly discovered internships, scholarships, and fellowships.
- **Frontend Component:** `apps/web/src/app/opportunities/page.tsx`, `OpportunityCard.tsx`, `FilterBar.tsx`
- **Backend Responsibility:** Ingestion pipeline, Olostep search/scrape adapter, Crustdata firmographic enrichment.
- **Database Dependency:** `public.opportunities`, `public.opportunity_sources`
- **AI/ML/Agent Dependency:** LangGraph Opportunity Discovery state machine.
- **External Provider Dependency:** Olostep API (`/v1/searches`, `/v1/scrapes`), Crustdata API (`/company/enrich`).
- **Security & Privacy:** Scraped listings must retain source URL and retrieval timestamp; prevent malicious script injection in scraped HTML.
- **Acceptance Criteria:** Scraped opportunities contain verified organization, deadline, stipend, and source provenance.
- **Test Scenario:** `TEST-DISC-01`: Trigger discovery job; verify mock/real listings parse into `OpportunityDTO` schema.
- **Primary Owner:** Ramaraju (Olostep & Crustdata Ingestion) / Sanju (Discovery UI).

---

### 2.5 Deterministic Eligibility & Explainable Matching
- **Student Problem Solved:** Students apply blindly to opportunities only to get auto-rejected due to hidden criteria (wrong batch, branch, or CGPA).
- **User Journey:** Student opens an opportunity and instantly sees a clear Green/Red eligibility breakdown with plain-language explanations.
- **Frontend Component:** `apps/web/src/app/opportunities/[id]/page.tsx`, `EligibilityBreakdown.tsx`
- **Backend Responsibility:** Deterministic filter engine (branch, graduation year, CGPA) + pgvector semantic matching.
- **Database Dependency:** `public.opportunity_eligibility`, `public.opportunity_embeddings` (pgvector 768-dim)
- **AI/ML/Agent Dependency:** Sanju's embedding model selection (`text-embedding-004`) and reranking evaluation.
- **External Provider Dependency:** Gemini API (embeddings).
- **Security & Privacy:** Transparent decision logic; no "black-box" rejections without visible criteria.
- **Acceptance Criteria:** 100% precision on deterministic disqualifiers (e.g., student from 2024 batch is rejected if job requires 2026).
- **Test Scenario:** `TEST-ELIG-01`: Evaluate student (CGPA 7.5, batch 2026) against job (min CGPA 8.0); verify `isEligible=false` with specific reason.
- **Primary Owner:** Sanju (ML Model Selection & Semantic Scoring) / Ramaraju (Deterministic Rule Engine & SQL Execution).

---

### 2.6 ATS Resume Studio & Grounded Customization
- **Student Problem Solved:** Generic resumes fail ATS screeners; AI resume tools hallucinate false experience that backfires in interviews.
- **User Journey:** Student generates an ATS-compliant resume strictly derived from their Career Passport, tailored to a specific job description.
- **Frontend Component:** `apps/web/src/app/resume/page.tsx`, `ResumeSplitEditor.tsx`, `ATSScoreGauge.tsx`
- **Backend Responsibility:** Resume compilation service, PDF generation, tailoring state machine.
- **Database Dependency:** `public.resumes`, `public.resume_versions`, `public.resume_customizations`
- **AI/ML/Agent Dependency:** Grounded LLM prompting with strict context boundaries; Sanju's resume alignment evaluation metrics.
- **External Provider Dependency:** Gemini 2.0 Flash.
- **Security & Privacy:** Student resumes contain PII (phone, email); strict RLS isolation required.
- **Acceptance Criteria:** Generated resume contains **zero** facts outside the student's Career Passport.
- **Test Scenario:** `TEST-RESUME-01`: Tailor resume for Backend Intern; verify all listed projects exist in student's passport.
- **Primary Owner:** Sanju (Resume Studio UI & Grounding Verification) / Ramaraju (Backend PDF Service & Tailoring Graph).

---

### 2.7 Application Preparation & Dry-Run Form Filling
- **Student Problem Solved:** Repetitive manual entry across multiple portal application forms causes application fatigue and submission errors.
- **User Journey:** Student selects an opportunity; agent opens portal in a headless browser, inspects fields, and fills them in dry-run mode.
- **Frontend Component:** `apps/web/src/app/applications/page.tsx`, `FormPreviewDrawer.tsx`
- **Backend Responsibility:** Playwright form inspection, field extraction, dry-run filling, screenshot capture.
- **Database Dependency:** `public.applications`, `public.browser_execution_logs`
- **AI/ML/Agent Dependency:** LangGraph Application Preparation state machine.
- **External Provider Dependency:** Playwright (Chromium).
- **Security & Privacy:** No credentials stored; portal Terms of Service respected.
- **Acceptance Criteria:** Full-page dry-run screenshot and extracted key-value field diff generated without clicking "Submit".
- **Test Scenario:** `TEST-APP-01`: Run dry-run on mock portal form; verify screenshot saved and field diff recorded.
- **Primary Owner:** Ramaraju (Playwright Engine) / Sanju (Application UX).

---

### 2.8 Human-in-the-Loop Approval Gate (CRITICAL SAFETY GATE)
- **Student Problem Solved:** Fear of rogue autonomous agents submitting incorrect or embarrassing applications without consent.
- **User Journey:** Student receives an approval prompt showing the exact filled fields and rendered screenshot, with explicit "Approve" or "Reject" buttons.
- **Frontend Component:** `ApprovalModal.tsx`, `ActionDiffViewer.tsx`
- **Backend Responsibility:** Approval request creation, cryptographic state halting, decision endpoint (`POST /agents/approvals/{id}/decision`).
- **Database Dependency:** `public.approval_requests` (`status: pending | approved | rejected`)
- **AI/ML/Agent Dependency:** LangGraph `interrupt_before` approval checkpoint node.
- **External Provider Dependency:** None.
- **Security & Privacy:** Irreversible external submission is blocked until student explicitly confirms with authenticated token.
- **Acceptance Criteria:** Agent state machine halts permanently until decision is submitted; timeout cancels action safely.
- **Test Scenario:** `TEST-APPROVE-01`: Create approval request; verify Playwright worker does not proceed until approval API returns 200.
- **Primary Owner:** Shared (Sanju: Review UI / Ramaraju: Workflow Halt & Execution Gate).

---

### 2.9 Playwright Automated Execution & Audit Trail
- **Student Problem Solved:** High cognitive load of tracking confirmation receipts and application numbers.
- **User Journey:** Upon student approval, agent completes submission, captures confirmation receipt screenshot, and logs submission timestamp.
- **Frontend Component:** `ApplicationCard.tsx` (Status badge: `SUBMITTED`, View Receipt button).
- **Backend Responsibility:** Resuming Playwright context, clicking final submit button, capturing receipt, closing context.
- **Database Dependency:** `public.applications`, `public.browser_execution_logs`
- **AI/ML/Agent Dependency:** Playwright worker execution.
- **External Provider Dependency:** Target career portal.
- **Security & Privacy:** Zero bypass of CAPTCHA or anti-bot defenses; ephemeral browser contexts wiped post-execution.
- **Acceptance Criteria:** Immutable audit log recorded with step descriptions, timestamps, and receipt screenshot URL.
- **Test Scenario:** `TEST-EXEC-01`: Simulate approved action; verify `applications.status` updates to `submitted` with receipt logged.
- **Primary Owner:** Ramaraju.

---

### 2.10 Scheduled Opportunity Monitoring & Content Diffing
- **Student Problem Solved:** Missing short-window application deadlines on top company portals.
- **User Journey:** Student monitors target employers (e.g. Google India, ISRO, TCS Research); receives alerts when new batches open.
- **Frontend Component:** `apps/web/src/app/settings/page.tsx` (Monitored Companies section).
- **Backend Responsibility:** ARQ background cron task, Olostep schedule check, content hash diffing.
- **Database Dependency:** `public.opportunity_monitors`, `public.notifications`
- **AI/ML/Agent Dependency:** LangGraph Monitoring state machine.
- **External Provider Dependency:** Olostep API (`/v1/schedules`).
- **Security & Privacy:** Rate limits on polling frequencies to prevent target portal IP bans.
- **Acceptance Criteria:** Alerts triggered within 1 hour of portal posting change.
- **Test Scenario:** `TEST-MON-01`: Ingest modified HTML hash for monitored URL; verify notification record created.
- **Primary Owner:** Ramaraju.

---

### 2.11 Multilingual Interview Simulator
- **Student Problem Solved:** Anxiety and lack of interview practice in regional languages or English technical interviews.
- **User Journey:** Student selects a role (e.g. SDE Intern) and conducts a live spoken mock interview, receiving feedback on communication and tech depth.
- **Frontend Component:** `apps/web/src/app/interview/page.tsx`, `InterviewRoom.tsx`, `ScorecardModal.tsx`
- **Backend Responsibility:** Interview session state management, question generation, audio evaluation webhook.
- **Database Dependency:** `public.conversations`, `public.conversation_messages`
- **AI/ML/Agent Dependency:** Gemini Live voice interaction; Sanju's interview evaluation rubric and scoring algorithms.
- **External Provider Dependency:** Gemini Live API.
- **Security & Privacy:** Mock interview transcripts confidential to student.
- **Acceptance Criteria:** Student can complete a 5-question mock interview entirely via voice in Hindi, Telugu, or English.
- **Test Scenario:** `TEST-INT-01`: Start interview session; verify question generation and evaluation score payload.
- **Primary Owner:** Sanju (Interview UX, Scoring Models & Voice Evaluation) / Ramaraju (Audio Gateway & Session Router).

---

### 2.12 Career Analytics & Skill Gap Intelligence
- **Student Problem Solved:** Lack of visibility into which skills are currently trending across Indian entry-level tech roles.
- **User Journey:** Student views market demand trends, average stipends by city, and their personal skill gap against target roles.
- **Frontend Component:** `apps/web/src/app/analytics/page.tsx`, `SkillGapRadar.tsx`, `StipendBenchmarkChart.tsx`
- **Backend Responsibility:** Aggregation queries on ingested opportunity data.
- **Database Dependency:** `public.analytics_events`, `public.opportunities`, `public.skills`
- **AI/ML/Agent Dependency:** Sanju's skill gap clustering and market trend forecasting model.
- **External Provider Dependency:** None.
- **Security & Privacy:** Aggregated and anonymized data only.
- **Acceptance Criteria:** Displays top 10 in-demand skills and student's missing prerequisites for selected domain.
- **Test Scenario:** `TEST-ANA-01`: Query analytics endpoint; verify correct aggregation of required skills.
- **Primary Owner:** Sanju (Analytics Dashboard & ML Skill Trends) / Ramaraju (Aggregation Endpoints).
