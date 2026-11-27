import type {
  AgentCommandResult,
  AgentEventRecord,
  AgentRunRequestPayload,
  AgentRunResult,
  AgentSessionDetail,
  AgentSessionRecord,
  AiChatResponse,
  AnalyticsOverview,
  ApiEligibilityResult,
  ApiOpportunity,
  ApiStudentProfile,
  ApplicationRecord,
  ApprovalDecisionResult,
  ApprovalRequest,
  AutomationPrepareResult,
  BackgroundJobStatus,
  BrowserExecutionLogRecord,
  CareerPassport,
  CompanyApplicantItem,
  ConversationDetail,
  ConversationSummary,
  EducationCreatePayload,
  EducationItem,
  InterviewSessionRecord,
  MlHealthStatus,
  NotificationItem,
  OrganizationRecord,
  PaginatedOpportunities,
  RecruiterCandidateSummary,
  ResumeAnalyzeResult,
  ResumeCustomizationResult,
  ResumeRecord,
  StudentProfileUpsertPayload,
  UniversityOverview,
  UserProfile,
  VoiceSessionRecord,
  VoiceTicket,
  WatchtowerMonitor,
} from '@opportunity-os/shared-types';

export type UnauthorizedRefreshHandler = () => Promise<string | null>;

export interface ListOpportunitiesParams {
  cursor?: string;
  limit?: number;
  type?: string;
  q?: string;
  activeOnly?: boolean;
  sortOrder?: 'asc' | 'desc';
}

export interface DiscoverOpportunitiesParams {
  query: string;
  type?: string;
  limit?: number;
}

export class OpportunityApiClient {
  private baseUrl: string;
  private token?: string;
  private onUnauthorized?: UnauthorizedRefreshHandler;
  private refreshInFlight: Promise<string | null> | null = null;

  constructor(
    baseUrl: string = '/api/v1',
    token?: string,
    onUnauthorized?: UnauthorizedRefreshHandler
  ) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.token = token;
    this.onUnauthorized = onUnauthorized;
  }

  setToken(token: string) {
    this.token = token || undefined;
  }

  setUnauthorizedHandler(handler?: UnauthorizedRefreshHandler) {
    this.onUnauthorized = handler;
  }

  private async refreshAccessToken(): Promise<string | null> {
    if (!this.onUnauthorized) {
      return null;
    }
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.onUnauthorized()
        .catch(() => null)
        .finally(() => {
          this.refreshInFlight = null;
        });
    }
    return this.refreshInFlight;
  }

  private async requestResponse(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false,
    includeJsonContentType: boolean = true
  ): Promise<Response> {
    const isFormData =
      typeof FormData !== 'undefined' && options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(!includeJsonContentType || isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && !isRetry && this.onUnauthorized) {
      const refreshedToken = await this.refreshAccessToken();
      if (refreshedToken) {
        this.token = refreshedToken;
        return this.requestResponse(endpoint, options, true, includeJsonContentType);
      }
      this.token = undefined;
    }

    if (!response.ok) {
      const errorBody = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      const message =
        (typeof errorBody?.detail === 'string' && errorBody.detail) ||
        (typeof errorBody?.detail?.detail === 'string' && errorBody.detail.detail) ||
        (typeof errorBody?.message === 'string' && errorBody.message) ||
        (typeof errorBody?.title === 'string' && errorBody.title) ||
        `API error: ${response.status}`;
      throw new Error(message);
    }

    return response;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false
  ): Promise<T> {
    const response = await this.requestResponse(endpoint, options, isRetry, true);

    if (response.status === 204 || response.status === 205) {
      return undefined as T;
    }

    const text = await response.text();
    if (!text) {
      return undefined as T;
    }
    return JSON.parse(text) as T;
  }

  // -------------------------------------------------------------------------
  // Health & Users / Student Profiles
  // -------------------------------------------------------------------------

  async getHealth(): Promise<{ status: string; version: string; environment: string }> {
    return this.request('/health');
  }

  async getMyProfile(): Promise<UserProfile> {
    return this.request<UserProfile>('/users/me');
  }

  async updateMyProfile(payload: {
    fullName?: string | null;
    avatarUrl?: string | null;
    preferredLanguage?: string | null;
  }): Promise<UserProfile> {
    return this.request<UserProfile>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async getStudentProfile(): Promise<ApiStudentProfile> {
    return this.request<ApiStudentProfile>('/users/me/student-profile');
  }

  async upsertStudentProfile(payload: StudentProfileUpsertPayload): Promise<ApiStudentProfile> {
    return this.request<ApiStudentProfile>('/users/me/student-profile', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async getProfile(): Promise<ApiStudentProfile> {
    return this.getStudentProfile();
  }

  async listEducation(): Promise<EducationItem[]> {
    return this.request<EducationItem[]>('/users/me/education');
  }

  async addEducation(payload: EducationCreatePayload): Promise<EducationItem> {
    return this.request<EducationItem>('/users/me/education', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async deleteEducation(educationId: string): Promise<void> {
    await this.request<void>(`/users/me/education/${encodeURIComponent(educationId)}`, {
      method: 'DELETE',
    });
  }

  // -------------------------------------------------------------------------
  // Career Passport
  // -------------------------------------------------------------------------

  async getCareerPassport(): Promise<CareerPassport> {
    return this.request<CareerPassport>('/career-passport');
  }

  async addCareerPassportItem(
    category: 'verified_achievements' | 'coursework' | 'certifications' | 'projects',
    data: Record<string, unknown>
  ): Promise<CareerPassport> {
    return this.request<CareerPassport>('/career-passport/items', {
      method: 'POST',
      body: JSON.stringify({ category, data }),
    });
  }

  async deleteCareerPassportItem(itemId: string): Promise<CareerPassport> {
    return this.request<CareerPassport>(`/career-passport/items/${encodeURIComponent(itemId)}`, {
      method: 'DELETE',
    });
  }

  // -------------------------------------------------------------------------
  // Opportunities & Saved Bookmarks
  // -------------------------------------------------------------------------

  async listOpportunities(params: ListOpportunitiesParams = {}): Promise<PaginatedOpportunities> {
    const search = new URLSearchParams();
    if (params.cursor) search.set('cursor', params.cursor);
    if (params.limit !== undefined) search.set('limit', String(params.limit));
    if (params.type) search.set('type', params.type);
    if (params.q) search.set('q', params.q);
    if (params.activeOnly !== undefined) search.set('active_only', String(params.activeOnly));
    if (params.sortOrder) search.set('sort_order', params.sortOrder);
    const qs = search.toString();
    return this.request<PaginatedOpportunities>(`/opportunities${qs ? `?${qs}` : ''}`);
  }

  async getOpportunity(opportunityId: string): Promise<ApiOpportunity> {
    return this.request<ApiOpportunity>(`/opportunities/${encodeURIComponent(opportunityId)}`);
  }

  async discoverOpportunities(
    input?: string | DiscoverOpportunitiesParams
  ): Promise<PaginatedOpportunities> {
    const query = typeof input === 'string' ? input.trim() : input?.query?.trim() ?? '';
    if (query.length < 2) {
      return this.listOpportunities(
        typeof input === 'object' && input ? { type: input.type, limit: input.limit } : {}
      );
    }
    const payload =
      typeof input === 'string'
        ? { query }
        : { query, ...(input?.type ? { type: input.type } : {}), ...(input?.limit ? { limit: input.limit } : {}) };
    return this.request<PaginatedOpportunities>('/opportunities/discover', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listSavedOpportunities(): Promise<ApiOpportunity[]> {
    return this.request<ApiOpportunity[]>('/opportunities/saved');
  }

  async toggleSaveOpportunity(
    opportunityId: string,
    saved: boolean = true,
    notes?: string
  ): Promise<{ opportunityId: string; saved: boolean; notes?: string | null }> {
    return this.request(`/opportunities/${encodeURIComponent(opportunityId)}/save`, {
      method: 'POST',
      body: JSON.stringify({ saved, ...(notes !== undefined ? { notes } : {}) }),
    });
  }

  // -------------------------------------------------------------------------
  // Eligibility Evaluation
  // -------------------------------------------------------------------------

  async checkEligibility(opportunityId: string): Promise<ApiEligibilityResult> {
    return this.request<ApiEligibilityResult>('/eligibility/evaluate', {
      method: 'POST',
      body: JSON.stringify({ opportunityId }),
    });
  }

  // -------------------------------------------------------------------------
  // Applications & Human-in-the-Loop Approvals
  // -------------------------------------------------------------------------

  async listApplications(): Promise<ApplicationRecord[]> {
    return this.request<ApplicationRecord[]>('/applications');
  }

  async createApplication(
    opportunityId: string,
    status: 'drafting' | 'saved' = 'drafting'
  ): Promise<ApplicationRecord> {
    return this.request<ApplicationRecord>('/applications', {
      method: 'POST',
      body: JSON.stringify({ opportunityId, status }),
    });
  }

  async getApplication(applicationId: string): Promise<ApplicationRecord> {
    return this.request<ApplicationRecord>(`/applications/${encodeURIComponent(applicationId)}`);
  }

  async updateApplicationStatus(
    applicationId: string,
    status: string,
    expectedStatus: string
  ): Promise<ApplicationRecord> {
    return this.request<ApplicationRecord>(
      `/applications/${encodeURIComponent(applicationId)}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status, expectedStatus }),
      }
    );
  }

  async deleteApplication(applicationId: string): Promise<void> {
    await this.request<void>(`/applications/${encodeURIComponent(applicationId)}`, {
      method: 'DELETE',
    });
  }

  async listPendingApprovals(): Promise<ApprovalRequest[]> {
    return this.request<ApprovalRequest[]>('/agents/approvals/pending');
  }

  async getApproval(approvalId: string): Promise<ApprovalRequest> {
    return this.request<ApprovalRequest>(`/agents/approvals/${encodeURIComponent(approvalId)}`);
  }

  async approveAction(
    approvalId: string,
    approved: boolean,
    rejectionReason?: string,
    executeSubmission: boolean = false
  ): Promise<ApprovalDecisionResult> {
    return this.request<ApprovalDecisionResult>(
      `/agents/approvals/${encodeURIComponent(approvalId)}/decision`,
      {
        method: 'POST',
        body: JSON.stringify({
          approved,
          ...(rejectionReason !== undefined ? { rejectionReason } : {}),
          ...(executeSubmission ? { executeSubmission: true } : {}),
        }),
      }
    );
  }

  // -------------------------------------------------------------------------
  // Notifications & Resumes
  // -------------------------------------------------------------------------

  async listNotifications(unreadOnly: boolean = false): Promise<NotificationItem[]> {
    return this.request<NotificationItem[]>(`/notifications?unread_only=${unreadOnly}`);
  }

  async markNotificationRead(notificationId: string): Promise<NotificationItem> {
    return this.request<NotificationItem>(
      `/notifications/${encodeURIComponent(notificationId)}/read`,
      { method: 'PATCH' }
    );
  }

  async listResumes(): Promise<ResumeRecord[]> {
    return this.request<ResumeRecord[]>('/resumes');
  }

  async createResume(title: string, masterContent: Record<string, unknown>): Promise<ResumeRecord> {
    return this.request<ResumeRecord>('/resumes', {
      method: 'POST',
      body: JSON.stringify({ title, masterContent }),
    });
  }

  async getResume(resumeId: string): Promise<ResumeRecord> {
    return this.request<ResumeRecord>(`/resumes/${encodeURIComponent(resumeId)}`);
  }

  async deleteResume(resumeId: string): Promise<void> {
    await this.request<void>(`/resumes/${encodeURIComponent(resumeId)}`, {
      method: 'DELETE',
    });
  }

  async uploadResumeFile(
    file: File | Blob,
    options?: { title?: string; syncToProfile?: boolean; filename?: string }
  ): Promise<ResumeRecord> {
    const form = new FormData();
    const fname =
      options?.filename ||
      (typeof File !== 'undefined' && file instanceof File ? file.name : 'resume.pdf');
    form.append('file', file, fname);
    if (options?.title) form.append('title', options.title);
    if (options?.syncToProfile !== undefined) {
      form.append('sync_to_profile', String(options.syncToProfile));
    }
    return this.request<ResumeRecord>('/resumes/upload', {
      method: 'POST',
      body: form,
    });
  }

  async getResumeDownloadUrl(resumeId: string): Promise<{
    resumeId: string;
    storageBucket?: string | null;
    storagePath?: string | null;
    signedUrl?: string | null;
    fallbackPdfEndpoint: string;
  }> {
    return this.request(`/resumes/${encodeURIComponent(resumeId)}/download-url`);
  }

  async analyzeResume(resumeId: string, opportunityId?: string): Promise<ResumeAnalyzeResult> {
    return this.request<ResumeAnalyzeResult>(
      `/resumes/${encodeURIComponent(resumeId)}/analyze`,
      {
        method: 'POST',
        body: JSON.stringify(opportunityId ? { opportunityId } : {}),
      }
    );
  }

  async tailorResume(
    resumeId: string,
    opportunityId: string,
    customFocus?: string,
    candidateClaims?: string[]
  ): Promise<ResumeCustomizationResult> {
    return this.request<ResumeCustomizationResult>(
      `/resumes/${encodeURIComponent(resumeId)}/tailor`,
      {
        method: 'POST',
        body: JSON.stringify({
          opportunityId,
          ...(customFocus ? { customFocus } : {}),
          ...(candidateClaims ? { candidateClaims } : {}),
        }),
      }
    );
  }

  getResumePdfUrl(resumeId: string, version?: number): string {
    const qs = version ? `?version=${version}` : '';
    return `${this.baseUrl}/resumes/${encodeURIComponent(resumeId)}/pdf${qs}`;
  }

  // -------------------------------------------------------------------------
  // External Intelligence (Olostep Research, Crustdata Companies & Watchtower)
  // -------------------------------------------------------------------------

  async researchOpportunities(payload: {
    query: string;
    targetUrl?: string;
    limit?: number;
    enrichCompanies?: boolean;
  }): Promise<{
    query: string;
    discoveredCount: number;
    deduplicatedCount: number;
    opportunities: ApiOpportunity[];
    sourcesRecorded: string[];
  }> {
    return this.request('/research/discover', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async enrichCompany(payload: {
    domain?: string;
    companyName?: string;
    forceRefresh?: boolean;
  }): Promise<OrganizationRecord> {
    return this.request<OrganizationRecord>('/companies/enrich', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listCompanies(): Promise<OrganizationRecord[]> {
    return this.request<OrganizationRecord[]>('/companies');
  }

  async listWatchtowerMonitors(): Promise<WatchtowerMonitor[]> {
    return this.request<WatchtowerMonitor[]>('/watchtower/monitors');
  }

  async createWatchtowerMonitor(payload: {
    targetOrganization: string;
    targetUrl?: string;
    frequency?: 'hourly' | 'daily' | 'weekly';
    criteria?: Record<string, unknown>;
  }): Promise<WatchtowerMonitor> {
    return this.request<WatchtowerMonitor>('/watchtower/monitors', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async deleteWatchtowerMonitor(monitorId: string): Promise<void> {
    await this.request<void>(`/watchtower/monitors/${encodeURIComponent(monitorId)}`, {
      method: 'DELETE',
    });
  }

  // -------------------------------------------------------------------------
  // Voice Gateway
  // -------------------------------------------------------------------------

  async issueVoiceTicket(): Promise<VoiceTicket> {
    return this.request<VoiceTicket>('/voice/tickets', { method: 'POST' });
  }

  async listVoiceSessions(limit: number = 20): Promise<VoiceSessionRecord[]> {
    return this.request<VoiceSessionRecord[]>(`/voice/sessions?limit=${limit}`);
  }

  async createVoiceSession(payload: {
    detectedLanguage: string;
    audioDurationSeconds?: number;
    transcript?: string | null;
    status?: 'completed' | 'interrupted' | 'failed';
  }): Promise<VoiceSessionRecord> {
    return this.request<VoiceSessionRecord>('/voice/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async chatWithAssistant(payload: {
    message: string;
    language?: string;
    conversationId?: string | null;
  }): Promise<AiChatResponse> {
    return this.request<AiChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listConversations(limit: number = 20): Promise<ConversationSummary[]> {
    return this.request<ConversationSummary[]>(`/conversations?limit=${limit}`);
  }

  async getConversation(conversationId: string): Promise<ConversationDetail> {
    return this.request<ConversationDetail>(`/conversations/${encodeURIComponent(conversationId)}`);
  }

  // -------------------------------------------------------------------------
  // Automation, Background Jobs & Agent Telemetry
  // -------------------------------------------------------------------------

  async prepareApplicationAutomation(
    applicationId: string,
    portalUrl?: string | null
  ): Promise<AutomationPrepareResult> {
    return this.request<AutomationPrepareResult>(
      `/applications/${encodeURIComponent(applicationId)}/prepare-automation`,
      {
        method: 'POST',
        body: JSON.stringify({ portalUrl: portalUrl ?? null }),
      }
    );
  }

  async executeApprovedApplication(
    applicationId: string,
    approvalRequestId: string
  ): Promise<AutomationPrepareResult> {
    return this.request<AutomationPrepareResult>(
      `/applications/${encodeURIComponent(applicationId)}/execute-approved`,
      {
        method: 'POST',
        body: JSON.stringify({ approvalRequestId }),
      }
    );
  }

  async listBrowserLogs(limit: number = 30): Promise<BrowserExecutionLogRecord[]> {
    return this.request<BrowserExecutionLogRecord[]>(`/browser-logs?limit=${limit}`);
  }

  async fetchBrowserLogScreenshot(logId: string): Promise<Blob> {
    const res = await this.requestResponse(
      `/browser-logs/${encodeURIComponent(logId)}/screenshot`,
      {},
      false,
      false
    );
    return res.blob();
  }

  async runAgentWorkflow(payload: AgentRunRequestPayload): Promise<AgentRunResult> {
    return this.request<AgentRunResult>('/agents/runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listAgentSessions(limit: number = 20): Promise<AgentSessionRecord[]> {
    return this.request<AgentSessionRecord[]>(`/agents/sessions?limit=${limit}`);
  }

  async getAgentSession(sessionId: string): Promise<AgentSessionDetail> {
    return this.request<AgentSessionDetail>(`/agents/sessions/${encodeURIComponent(sessionId)}`);
  }

  async getAgentSessionEvents(sessionId: string): Promise<AgentEventRecord[]> {
    return this.request<AgentEventRecord[]>(
      `/agents/sessions/${encodeURIComponent(sessionId)}/events`
    );
  }

  async commandAgentSession(
    sessionId: string,
    payload: { action: 'query' | 'pause' | 'resume'; command?: string; language?: string }
  ): Promise<AgentCommandResult> {
    return this.request<AgentCommandResult>(
      `/agents/sessions/${encodeURIComponent(sessionId)}/command`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  getAgentSessionStreamUrl(sessionId: string, once: boolean = false): string {
    const suffix = once ? '?once=true' : '';
    return `${this.baseUrl}/agents/sessions/${encodeURIComponent(sessionId)}/stream${suffix}`;
  }

  async enqueueBackgroundJob(
    jobType:
      | 'process_uploaded_resume'
      | 'run_olostep_research_job'
      | 'sync_crustdata_company'
      | 'aggregate_analytics_metrics',
    payload: Record<string, unknown> = {}
  ): Promise<BackgroundJobStatus> {
    return this.request<BackgroundJobStatus>('/jobs', {
      method: 'POST',
      body: JSON.stringify({ jobType, payload }),
    });
  }

  async getBackgroundJobStatus(jobId: string): Promise<BackgroundJobStatus> {
    return this.request<BackgroundJobStatus>(`/jobs/${encodeURIComponent(jobId)}`);
  }

  // -------------------------------------------------------------------------
  // Interview Simulator, Analytics & Role Portals
  // -------------------------------------------------------------------------

  async listInterviewSessions(limit: number = 15): Promise<InterviewSessionRecord[]> {
    return this.request<InterviewSessionRecord[]>(`/interview/sessions?limit=${limit}`);
  }

  async createInterviewSession(payload: {
    targetRole: string;
    language?: string;
  }): Promise<InterviewSessionRecord> {
    return this.request<InterviewSessionRecord>('/interview/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async submitInterviewResponse(
    sessionId: string,
    payload: { questionIndex: number; answerText: string }
  ): Promise<InterviewSessionRecord> {
    return this.request<InterviewSessionRecord>(
      `/interview/sessions/${encodeURIComponent(sessionId)}/respond`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>('/analytics/overview');
  }

  async recordAnalyticsEvent(
    eventName: string,
    eventMetadata: Record<string, unknown> = {}
  ): Promise<{ id: string; eventName: string; recorded: boolean }> {
    return this.request('/analytics/events', {
      method: 'POST',
      body: JSON.stringify({ eventName, eventMetadata }),
    });
  }

  async createCompanyOpportunity(payload: {
    title: string;
    organization: string;
    location: string;
    type?: string;
    stipendOrSalary?: string | null;
    deadline?: string | null;
    description: string;
    sourceUrl: string;
    requiredSkills?: string[];
    eligibleBatches?: number[];
    eligibleDegrees?: string[];
    minCgpa?: number | null;
  }): Promise<Record<string, unknown>> {
    return this.request('/company/opportunities', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listCompanyCandidates(query?: string): Promise<RecruiterCandidateSummary[]> {
    const qs = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<RecruiterCandidateSummary[]>(`/company/candidates${qs}`);
  }

  async listCompanyApplicants(): Promise<CompanyApplicantItem[]> {
    return this.request<CompanyApplicantItem[]>('/company/applicants');
  }

  async advanceCompanyApplication(
    applicationId: string,
    status: 'evaluating' | 'eligible' | 'accepted' | 'rejected'
  ): Promise<CompanyApplicantItem> {
    return this.request<CompanyApplicantItem>(
      `/company/applications/${encodeURIComponent(applicationId)}/advance`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }
    );
  }

  async getUniversityOverview(): Promise<UniversityOverview> {
    return this.request<UniversityOverview>('/university/overview');
  }

  async listUniversityStudents(query?: string): Promise<RecruiterCandidateSummary[]> {
    const qs = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<RecruiterCandidateSummary[]>(`/university/students${qs}`);
  }

  async verifyUniversityStudent(
    studentProfileId: string,
    payload: { credentialType?: string; notes?: string } = {}
  ): Promise<Record<string, unknown>> {
    return this.request(`/university/students/${encodeURIComponent(studentProfileId)}/verify`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // -------------------------------------------------------------------------
  // ML Subsystem
  // -------------------------------------------------------------------------

  async getMlHealth(): Promise<MlHealthStatus> {
    return this.request<MlHealthStatus>('/ml/health');
  }

  async extractResumeText(resumeText: string): Promise<Record<string, unknown>> {
    return this.request('/ml/extract-resume', {
      method: 'POST',
      body: JSON.stringify({ resume_text: resumeText }),
    });
  }

  async understandMultilingual(
    queryText: string,
    documentTexts: string[]
  ): Promise<Record<string, unknown>> {
    return this.request('/ml/multilingual/understand', {
      method: 'POST',
      body: JSON.stringify({ query_text: queryText, document_texts: documentTexts }),
    });
  }

  async semanticMatch(
    studentQuery: string,
    opportunities: Array<{ doc_id: string; title?: string; doc_text: string }>,
    topK: number = 5
  ): Promise<Record<string, unknown>> {
    return this.request('/ml/semantic-match', {
      method: 'POST',
      body: JSON.stringify({ student_query: studentQuery, opportunities, top_k: topK }),
    });
  }

  async evaluateMlEligibility(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request('/ml/eligibility/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async rankMlOpportunities(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request('/ml/rank-opportunities', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async verifyEvidence(
    claimId: string,
    premiseText: string,
    hypothesisClaim: string
  ): Promise<Record<string, unknown>> {
    return this.request('/ml/verify-evidence', {
      method: 'POST',
      body: JSON.stringify({
        claim_id: claimId,
        premise_text: premiseText,
        hypothesis_claim: hypothesisClaim,
      }),
    });
  }

  async recommendPipeline(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request('/ml/recommend-pipeline', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}
