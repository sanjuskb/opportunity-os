# Opportunity OS — Frontend Page & Component Architecture Catalog

**Role & Standard:** Senior Frontend Architecture Specification  
**Designated Owner:** Sanju (Frontend & UX Lead)  
**Governance:** Implementation blueprint for Phase 5. Distinguishes implemented scaffold routes from proposed production component hierarchies.

---

## 1. Route Topology & Implementation Status

```text
apps/web/src/app/
├── (marketing)/
│   ├── layout.tsx                    [PROPOSED] Marketing Shell (Nav, Footer, 3D Hero Canvas)
│   └── page.tsx                      [EXISTING SCAFFOLD -> EXPANDING] Landing Page
├── (auth)/
│   ├── layout.tsx                    [PROPOSED] Auth Shell (Glassmorphism backdrop)
│   ├── login/page.tsx                [PROPOSED] Student Login
│   └── register/page.tsx             [PROPOSED] Student Registration
├── (onboarding)/
│   ├── layout.tsx                    [PROPOSED] Multi-step Wizard Shell
│   ├── language/page.tsx             [PROPOSED] Step 1: Regional Language Selection
│   ├── education/page.tsx            [PROPOSED] Step 2: College, Degree, Batch & CGPA
│   ├── skills/page.tsx               [PROPOSED] Step 3: Skills & Domain Tags
│   ├── preferences/page.tsx          [PROPOSED] Step 4: Role & Location Preferences
│   └── review/page.tsx               [PROPOSED] Step 5: Profile Review & Confirmation
├── (dashboard)/
│   ├── layout.tsx                    [PROPOSED] Authenticated Workspace Shell (Sidebar + TopNav + Voice Orb)
│   ├── overview/page.tsx             [PROPOSED] High-Impact Command Dashboard
│   ├── opportunities/
│   │   ├── page.tsx                  [EXISTING SCAFFOLD] Opportunity Discovery Feed
│   │   └── [id]/page.tsx             [PROPOSED] Opportunity Detail & Explainable Match
│   ├── career-passport/
│   │   └── page.tsx                  [EXISTING SCAFFOLD] Verified Career Passport
│   ├── resume/
│   │   ├── page.tsx                  [EXISTING SCAFFOLD] ATS Resume Studio
│   │   └── editor/page.tsx           [PROPOSED] Grounded Split-Screen Resume Editor
│   ├── applications/
│   │   ├── page.tsx                  [EXISTING SCAFFOLD] Application Command Center
│   │   └── [id]/page.tsx             [PROPOSED] Application Detail & Audit Timeline
│   ├── interview/
│   │   ├── page.tsx                  [EXISTING SCAFFOLD] Interview Simulator Hub
│   │   └── session/page.tsx          [PROPOSED] Live Gemini Voice Interview Room
│   ├── analytics/
│   │   └── page.tsx                  [EXISTING SCAFFOLD] Skill Gap & Demand Analytics
│   ├── notifications/
│   │   └── page.tsx                  [PROPOSED] Notification & Monitor Alert Tray
│   └── settings/
│       └── page.tsx                  [EXISTING SCAFFOLD] User Preferences & Security
```

---

## 2. Public & Marketing Pages

### 2.1 Landing Page (`/`)
- **Purpose:** Visually communicate the *Autonomous Intelligence Campus*, demonstrate voice-first Indic AI capabilities, and convert students.
- **Parent Layout:** `apps/web/src/app/(marketing)/layout.tsx`
- **Component Hierarchy:**
  ```text
  LandingPage
  ├── HeroSection
  │   ├── HeroScene (3D Spline Canvas / WebP Fallback)
  │   ├── HeroContent (Semantic H1, Indic language pill selector)
  │   ├── HeroFloatingBadges (Passport, Eligibility, ATS Score)
  │   └── HeroVoiceCTA (One-click microphone activation)
  ├── ProblemStatementSection (Pain points for Indian college students)
  ├── CampusZonesOverview (Student, Company, University, Opportunity Hubs)
  ├── VoiceDemoWidget (Interactive audio sandbox)
  ├── SecurityEthicsSection (Anti-bypass, human approval, no CAPTCHA cracking)
  └── Footer (Attributions, licensing, language switcher)
  ```
- **State Requirements:** `useVoiceStore` (isListening, activeLanguage).
- **Server Dependencies:** Static SSR; no pre-auth API calls required.
- **Loading / Empty / Error States:** Fallback hero render if WebGL unavailable; layout reserved to prevent CLS.
- **Mobile Behavior:** Single-column layout, touch-orbit locked on 3D canvas, sticky bottom voice trigger.
- **Accessibility:** Semantic HTML heading hierarchy (`H1` $\rightarrow$ `H2`), high-contrast text ($> 4.5:1$).

---

## 3. Student Onboarding Workflow (`/onboarding/*`)

### 3.1 Language Selection (`/onboarding/language`)
- **Purpose:** Set student's primary operating language across UI and voice.
- **Components:** `LanguageGrid`, `LanguageCard` (7 Indic languages: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali with native scripts), `AudioSampleButton` (plays native audio greeting).
- **State Requirements:** `usePreferencesStore` (temporary language selection).
- **API Dependencies:** `PUT /api/v1/users/me` on completion.

### 3.2 Education & Academic Profile (`/onboarding/education`)
- **Purpose:** Capture deterministic eligibility criteria (College, Degree, Branch, Graduation Year, CGPA).
- **Components:** `CollegeAutocomplete`, `DegreeSelect`, `BatchYearPicker`, `CgpaInputSlider`.
- **Validation:** Strict client-side Zod validation ($2024 \le \text{year} \le 2030$; $0.0 \le \text{CGPA} \le 10.0$).

---

## 4. Main Workspace Pages

### 4.1 Opportunity Discovery Feed (`/opportunities`)
- **Purpose:** Search and filter verified internships and career schemes across India.
- **Component Hierarchy:**
  ```text
  OpportunitiesPage
  ├── OpportunityFeedHeader (Search input, voice query trigger)
  ├── FilterToolbar (Type, Location, Stipend, Remote-only, Batch)
  ├── ActiveFilterChips
  ├── OpportunityGrid (Responsive 1/2/3 column layout)
  │   ├── OpportunityCard
  │   │   ├── CompanyLogo
  │   │   ├── TitleAndOrg
  │   │   ├── EligibilityBadge (Green/Red pill)
  │   │   ├── MatchScoreRadial (0-100%)
  │   │   ├── StipendAndDeadline
  │   │   └── ActionButtons (Save, Quick Apply)
  │   └── InfiniteScrollTrigger
  └── SavedOpportunityDrawer
  ```
- **State Requirements:** `useFilterStore` (selected locations, batches, roles).
- **Server State (TanStack Query):** `useInfiniteQuery(['opportunities', filters], fetchOpportunities, { getNextPageParam })`.
- **Loading State:** 6 animated Tailwind skeleton cards (`animate-pulse`).
- **Empty State:** `EmptyFeedState` ("No opportunities found matching your criteria — try broadening your batch or branch filters").
- **Error State:** `RetryableErrorBanner` with manual retry button.

### 4.2 Opportunity Details & Explainable Eligibility (`/opportunities/[id]`)
- **Purpose:** Deep dive into job requirements, company firmographics, and deterministic eligibility breakdown.
- **Components:**
  ```text
  OpportunityDetailPage
  ├── JobHeaderBanner (Title, Company, Verified Badge, Source Provenance URL)
  ├── FirmographicsCard (Crustdata verified headcount, tech stack, funding stage)
  ├── EligibilityDiagnosticCard
  │   ├── DeterministicChecksList (Batch check, Degree check, CGPA check)
  │   ├── SkillOverlapCloud (Matched green skills vs Missing amber skills)
  │   └── PlainLanguageExplanation (Regional language translated summary)
  ├── JobDescriptionMarkdown
  └── ApplicationActionFooter (Prepare Application via Agent button)
  ```
- **Server State:** `useQuery(['opportunity', id], fetchOpportunityDetail)`.

### 4.3 Living Career Passport (`/career-passport`)
- **Purpose:** Single source of truth for student verified achievements, eliminating AI hallucinations in resumes.
- **Components:**
  ```text
  CareerPassportPage
  ├── PassportHeader (Verified Student Badge, Academic Identity)
  ├── AcademicTimeline (College, Semester scores, Coursework)
  ├── ProjectsSection (Verified GitHub repos, live demo links, technologies)
  ├── CertificationsSection (Credentials, issue dates, validation IDs)
  ├── VerifiedSkillCloud (Categorized technical & soft skills)
  └── AddItemModal (Zod-validated form to add projects/credentials)
  ```
- **Server State:** `useQuery(['career-passport'], fetchPassport)`, `useMutation(addPassportItem, { onOptimisticUpdate })`.

### 4.4 ATS Resume Studio & Editor (`/resume`)
- **Purpose:** Compose ATS-optimized resumes tailored per job description strictly from Career Passport records.
- **Component Hierarchy:**
  ```text
  ResumeStudioPage
  ├── MasterResumeSelector
  ├── TailoredVersionsList (Version tag, target company, alignment score)
  └── SplitScreenEditor
      ├── LeftPane: SectionOrganizer (Reorder sections, toggle passport items)
      ├── LeftPane: GroundingInspector (Flags any text not sourced from passport)
      ├── RightPane: LivePDFPreview (Interactive zoom, ATS layout preview)
      └── TopToolbar: ExportPDFButton, ATSScanButton
  ```
- **Client State:** `useResumeEditorStore` (active sections, selected items, dirty status).

### 4.5 Application Command Center & Approval Gate (`/applications`)
- **Purpose:** Manage active applications and execute human approval checkpoints for Playwright browser automation.
- **Components:**
  ```text
  ApplicationsPage
  ├── ApplicationKanbanBoard (Drafting, Ready for Review, Submitted, Accepted)
  ├── PendingApprovalsBanner (Pulsing high-priority alert if action pending)
  ├── ApprovalModal (CRITICAL SAFETY GATE)
  │   ├── PortalHeader (Company portal, URL, action type)
  │   ├── DryRunScreenshotViewer (Zoomable full-page screenshot of filled form)
  │   ├── FormFieldDiffTable (Field label, Proposed value, Source passport item)
  │   ├── EthicsDisclaimer ("No CAPTCHAs were bypassed; submission requires your consent")
  │   └── DecisionActionGroup (Approve & Submit, Reject & Abort, Edit Manually)
  └── SubmissionReceiptModal (Proof of submission screenshot and timestamp)
  ```
- **State Requirements:** Real-time polling / WebSocket subscription for pending approvals.
- **Server State:** `useQuery(['applications'], fetchApplications)`, `useMutation(submitApprovalDecision)`.

### 4.6 Multilingual Interview Simulator (`/interview`)
- **Purpose:** Practice spoken behavioral and technical mock interviews in 7 Indian languages via Gemini Live.
- **Components:**
  ```text
  InterviewRoom
  ├── InterviewHeader (Role, Difficulty, Active Language)
  ├── VoiceVisualizerCanvas (3D Audio wave reacting to student and AI voice)
  ├── RealtimeTranscriptStream (Live Indic captions + English technical terms)
  ├── ControlsToolbar (Mute mic, End session, Request hint)
  └── PostInterviewScorecardModal
      ├── OverallPerformanceRadial (Communication, Technical Depth, Clarity)
      ├── QuestionByQuestionBreakdown
      └── SuggestedImprovementPills
  ```
- **Voice State:** Managed via `useVoiceSession` hook (ephemeral Web Audio, no AudioContext in Zustand).
