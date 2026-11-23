import type {
  StudentProfile,
  Opportunity,
  EligibilityResult,
  ApprovalRequest
} from '@opportunity-os/shared-types';

export class OpportunityApiClient {
  private baseUrl: string;
  private token?: string;

  constructor(baseUrl: string = '/api/v1', token?: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorBody.message || `API error: ${response.status}`);
    }

    return response.json();
  }

  async getProfile(): Promise<StudentProfile> {
    return this.request<StudentProfile>('/users/me/profile');
  }

  async discoverOpportunities(query?: string): Promise<Opportunity[]> {
    const q = query ? `?q=${encodeURIComponent(query)}` : '';
    return this.request<Opportunity[]>(`/opportunities/discover${q}`);
  }

  async checkEligibility(opportunityId: string): Promise<EligibilityResult> {
    return this.request<EligibilityResult>(`/eligibility/evaluate/${opportunityId}`);
  }

  async approveAction(approvalId: string, approved: boolean): Promise<ApprovalRequest> {
    return this.request<ApprovalRequest>(`/agents/approval/${approvalId}`, {
      method: 'POST',
      body: JSON.stringify({ approved }),
    });
  }
}
