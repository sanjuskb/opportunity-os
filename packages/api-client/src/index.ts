import type {
  ApiEligibilityResult,
  ApiOpportunity,
  ApiStudentProfile,
  ApplicationRecord,
  ApprovalDecisionResult,
  ApprovalRequest,
  CareerPassport,
  EducationCreatePayload,
  EducationItem,
  MlHealthStatus,
  NotificationItem,
  OrganizationRecord,
  PaginatedOpportunities,
  ResumeAnalyzeResult,
  ResumeCustomizationResult,
  ResumeRecord,
  StudentProfileUpsertPayload,
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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false
  ): Promise<T> {
    const isFormData =
      typeof FormData !== 'undefined' && options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
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
        return this.request<T>(endpoint, options, true);
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
    rejectionReason?: string
  ): Promise<ApprovalDecisionResult> {
    return this.request<ApprovalDecisionResult>(
      `/agents/approvals/${encodeURIComponent(approvalId)}/decision`,
      {
        method: 'POST',
        body: JSON.stringify({
          approved,
          ...(rejectionReason !== undefined ? { rejectionReason } : {}),
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
