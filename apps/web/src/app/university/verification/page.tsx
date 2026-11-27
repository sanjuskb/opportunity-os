'use client';

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS } from '@/lib/queries/useOpportunityOs';

export default function UniversityVerificationPage() {
  const { user, apiClient } = useAuth();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<'pending' | 'verified'>('pending');

  const { data: students, error } = useQuery({
    queryKey: QUERY_KEYS.universityStudents(),
    queryFn: () => apiClient.listUniversityStudents(),
    enabled: Boolean(user),
    retry: false,
  });

  const verifyMutation = useMutation({
    mutationFn: (studentProfileId: string) => apiClient.verifyUniversityStudent(studentProfileId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.universityStudents() });
      void qc.invalidateQueries({ queryKey: QUERY_KEYS.universityOverview });
    },
  });

  const allRows = students ?? [];
  const pendingList = allRows.filter((c) => !c.isVerified);
  const verifiedList = allRows.filter((c) => c.isVerified);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Institutional Verification</h1>
            <Badge variant="emerald">Academic Attestation</Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Attest official CGPA transcripts and degree credentials for your student cohort.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200">
            University role required to verify student credentials.
          </div>
        )}

        <div className="flex items-center gap-2 border-b border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 text-xs font-bold border-b-2 transition ${
              activeTab === 'pending' ? 'border-emerald-500 text-white' : 'border-transparent text-slate-400'
            }`}
          >
            Pending Verification ({pendingList.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('verified')}
            className={`px-4 py-2 text-xs font-bold border-b-2 transition ${
              activeTab === 'verified' ? 'border-emerald-500 text-white' : 'border-transparent text-slate-400'
            }`}
          >
            Verified ({verifiedList.length})
          </button>
        </div>

        <div className="space-y-3">
          {(activeTab === 'pending' ? pendingList : verifiedList).map((cand) => (
            <Card key={cand.studentProfileId}>
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="font-bold text-white text-sm">{cand.fullName}</div>
                  <div className="text-xs text-slate-400">
                    {cand.degree} in {cand.branch} • {cand.collegeName} • CGPA:{' '}
                    <span className="text-emerald-400 font-bold">{cand.cgpa ?? '—'}</span>
                  </div>
                </div>

                {activeTab === 'pending' ? (
                  <Button
                    variant="glow"
                    size="sm"
                    isLoading={verifyMutation.isPending}
                    onClick={() => void verifyMutation.mutate(cand.studentProfileId)}
                  >
                    <ShieldCheck className="h-4 w-4 mr-1 text-emerald-300" />
                    <span>Approve Credential</span>
                  </Button>
                ) : (
                  <Badge variant="emerald">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                    Verified
                  </Badge>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
