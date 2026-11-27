'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { StudentProfileUpsertPayload } from '@opportunity-os/shared-types';
import { useAuth } from '@/components/auth/AuthProvider';

export const QUERY_KEYS = {
  userProfile: ['userProfile'] as const,
  studentProfile: ['studentProfile'] as const,
  education: ['education'] as const,
  careerPassport: ['careerPassport'] as const,
  opportunities: (params?: Record<string, unknown>) => ['opportunities', params ?? {}] as const,
  opportunityDetail: (id: string) => ['opportunityDetail', id] as const,
  savedOpportunities: ['savedOpportunities'] as const,
  applications: ['applications'] as const,
  approvals: ['approvals'] as const,
  notifications: ['notifications'] as const,
  resumes: ['resumes'] as const,
  companies: ['companies'] as const,
  monitors: ['monitors'] as const,
  interviewSessions: ['interviewSessions'] as const,
  analyticsOverview: ['analyticsOverview'] as const,
  agentSessions: ['agentSessions'] as const,
  browserLogs: ['browserLogs'] as const,
  companyCandidates: (q?: string) => ['companyCandidates', q ?? ''] as const,
  companyApplicants: ['companyApplicants'] as const,
  universityOverview: ['universityOverview'] as const,
  universityStudents: (q?: string) => ['universityStudents', q ?? ''] as const,
};

export function useUserProfile() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.userProfile,
    queryFn: () => apiClient.getMyProfile(),
    enabled: Boolean(user) && !loading,
  });
}

export function useUpdateUserProfile() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      fullName?: string;
      avatarUrl?: string;
      preferredLanguage?: string;
      userRole?: 'student' | 'company' | 'university';
    }) => apiClient.updateMyProfile(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.userProfile });
    },
  });
}

export function useStudentProfile() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.studentProfile,
    queryFn: () => apiClient.getStudentProfile(),
    enabled: Boolean(user) && !loading,
    retry: false,
  });
}

export function useUpsertStudentProfile() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentProfileUpsertPayload) => apiClient.upsertStudentProfile(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.studentProfile });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.careerPassport });
    },
  });
}

export function useCareerPassport() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.careerPassport,
    queryFn: () => apiClient.getCareerPassport(),
    enabled: Boolean(user) && !loading,
    retry: false,
  });
}

export function useAddCareerPassportItem() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      category: 'verified_achievements' | 'coursework' | 'certifications' | 'projects';
      item: Record<string, unknown>;
    }) => apiClient.addCareerPassportItem(payload.category, payload.item),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.careerPassport });
    },
  });
}

export function useOpportunities(params: {
  limit?: number;
  type?: string;
  q?: string;
  activeOnly?: boolean;
} = {}) {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.opportunities(params),
    queryFn: () => apiClient.listOpportunities(params),
    enabled: Boolean(user) && !loading,
  });
}

export function useDiscoverOpportunities() {
  const { apiClient } = useAuth();
  return useMutation({
    mutationFn: (params: { query: string; type?: string; limit?: number }) =>
      apiClient.discoverOpportunities(params),
  });
}

export function useOpportunityDetail(id: string) {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.opportunityDetail(id),
    queryFn: () => apiClient.getOpportunity(id),
    enabled: Boolean(user) && !loading && Boolean(id),
  });
}

export function useSavedOpportunities() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.savedOpportunities,
    queryFn: () => apiClient.listSavedOpportunities(),
    enabled: Boolean(user) && !loading,
  });
}

export function useToggleSaveOpportunity() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ opportunityId, saved }: { opportunityId: string; saved: boolean }) =>
      apiClient.toggleSaveOpportunity(opportunityId, saved),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.savedOpportunities });
    },
  });
}

export function useEvaluateEligibility() {
  const { apiClient } = useAuth();
  return useMutation({
    mutationFn: (opportunityId: string) => apiClient.checkEligibility(opportunityId),
  });
}

export function useApplications() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.applications,
    queryFn: () => apiClient.listApplications(),
    enabled: Boolean(user) && !loading,
  });
}

export function useCreateApplication() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (opportunityId: string) => apiClient.createApplication(opportunityId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.applications });
    },
  });
}

export function usePrepareAutomation() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ applicationId, portalUrl }: { applicationId: string; portalUrl?: string | null }) =>
      apiClient.prepareApplicationAutomation(applicationId, portalUrl),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.applications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.approvals });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.browserLogs });
    },
  });
}

export function useExecuteApprovedApplication() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      applicationId,
      approvalRequestId,
    }: {
      applicationId: string;
      approvalRequestId: string;
    }) => apiClient.executeApprovedApplication(applicationId, approvalRequestId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.applications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.approvals });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.browserLogs });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function usePendingApprovals() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.approvals,
    queryFn: () => apiClient.listPendingApprovals(),
    enabled: Boolean(user) && !loading,
  });
}

export function useDecideApproval() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      approvalId,
      approved,
      rejectionReason,
      executeSubmission = false,
    }: {
      approvalId: string;
      approved: boolean;
      rejectionReason?: string;
      executeSubmission?: boolean;
    }) => apiClient.approveAction(approvalId, approved, rejectionReason, executeSubmission),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.approvals });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.applications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.agentSessions });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.browserLogs });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.interviewSessions });
    },
  });
}

export function useNotifications() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: () => apiClient.listNotifications(),
    enabled: Boolean(user) && !loading,
  });
}

export function useMarkNotificationRead() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.markNotificationRead(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
    },
  });
}

export function useResumes() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.resumes,
    queryFn: () => apiClient.listResumes(),
    enabled: Boolean(user) && !loading,
  });
}

export function useUploadResume() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      title,
      syncToProfile = true,
    }: {
      file: File;
      title?: string;
      syncToProfile?: boolean;
    }) => apiClient.uploadResumeFile(file, { title, syncToProfile }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.resumes });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.studentProfile });
    },
  });
}

export function useAnalyzeResume() {
  const { apiClient } = useAuth();
  return useMutation({
    mutationFn: ({ resumeId, opportunityId }: { resumeId: string; opportunityId?: string }) =>
      apiClient.analyzeResume(resumeId, opportunityId),
  });
}

export function useTailorResume() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      resumeId,
      opportunityId,
      customFocus,
      candidateClaims,
    }: {
      resumeId: string;
      opportunityId: string;
      customFocus?: string;
      candidateClaims?: string[];
    }) => apiClient.tailorResume(resumeId, opportunityId, customFocus, candidateClaims),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.resumes });
    },
  });
}

export function useInterviewSessions() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.interviewSessions,
    queryFn: () => apiClient.listInterviewSessions(),
    enabled: Boolean(user) && !loading,
  });
}

export function useAnalyticsOverview() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.analyticsOverview,
    queryFn: () => apiClient.getAnalyticsOverview(),
    enabled: Boolean(user) && !loading,
  });
}

export function useAgentSessions() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.agentSessions,
    queryFn: () => apiClient.listAgentSessions(),
    enabled: Boolean(user) && !loading,
  });
}

export function useBrowserLogs() {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: QUERY_KEYS.browserLogs,
    queryFn: () => apiClient.listBrowserLogs(),
    enabled: Boolean(user) && !loading,
  });
}

export function useAgentSessionDetail(sessionId: string | null) {
  const { user, apiClient, loading } = useAuth();
  return useQuery({
    queryKey: ['agentSessionDetail', sessionId],
    queryFn: () => apiClient.getAgentSession(sessionId!),
    enabled: Boolean(user) && !loading && Boolean(sessionId),
    refetchInterval: 3000,
  });
}

export function useRunAgentWorkflow() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof apiClient.runAgentWorkflow>[0]) =>
      apiClient.runAgentWorkflow(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.agentSessions });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.approvals });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.applications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.browserLogs });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.resumes });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.interviewSessions });
    },
  });
}

export function useCommandAgentSession() {
  const { apiClient } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      action,
      command,
      language = 'en',
    }: {
      sessionId: string;
      action: 'query' | 'pause' | 'resume';
      command?: string;
      language?: string;
    }) => apiClient.commandAgentSession(sessionId, { action, command, language }),
    onSuccess: (_data, variables) => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.agentSessions });
      void qc.invalidateQueries({ queryKey: ['agentSessionDetail', variables.sessionId] });
    },
  });
}
