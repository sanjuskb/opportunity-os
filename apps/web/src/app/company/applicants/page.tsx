'use client';

import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS } from '@/lib/queries/useOpportunityOs';

export default function ApplicantPipelinePage() {
  const { user, apiClient } = useAuth();
  const qc = useQueryClient();
  const { data: applicants, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.companyApplicants,
    queryFn: () => apiClient.listCompanyApplicants(),
    enabled: Boolean(user),
    retry: false,
  });

  const advanceMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'evaluating' | 'eligible' | 'accepted' | 'rejected' }) =>
      apiClient.advanceCompanyApplication(id, status),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.companyApplicants });
    },
  });

  const rows = applicants ?? [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Applicant Review Pipeline</h1>
            <Badge variant="sapphire">Live PostgreSQL Pipeline</Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Review incoming candidate applications and advance shortlisted students.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200">
            Recruiter role required to inspect company applicants.
          </div>
        )}

        {isLoading ? (
          <div className="h-36 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : rows.length === 0 ? (
          <div className="p-8 rounded-xl border border-slate-800 bg-[#0B0F19] text-center text-xs text-slate-400">
            No candidate applications submitted yet.
          </div>
        ) : (
          <div className="space-y-3">
            {rows.map((app) => (
              <Card key={app.applicationId}>
                <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white text-base">{app.candidateName}</span>
                      <span className="text-xs text-cyan-300">{app.opportunityTitle}</span>
                      <Badge variant="slate">{app.status}</Badge>
                    </div>
                    <div className="text-xs text-slate-400">
                      {app.collegeName} {app.cgpa != null ? `• CGPA ${app.cgpa}` : ''}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      isLoading={advanceMutation.isPending}
                      onClick={() => void advanceMutation.mutate({ id: app.applicationId, status: 'accepted' })}
                    >
                      Advance / Shortlist
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
