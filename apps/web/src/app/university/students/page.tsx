'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS } from '@/lib/queries/useOpportunityOs';

export default function UniversityStudentsPage() {
  const { user, apiClient } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const { data: students, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.universityStudents(searchQuery),
    queryFn: () => apiClient.listUniversityStudents(searchQuery || undefined),
    enabled: Boolean(user),
    retry: false,
  });

  const rows = students ?? [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Student Cohort Directory</h1>
            <Badge variant="emerald">Institutional Roster</Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Live student roster backed by PostgreSQL student profiles and verification status.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Filter students by name, branch, or skill..." />
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200">
            University role required to view student roster.
          </div>
        )}

        {isLoading ? (
          <div className="h-36 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {rows.map((cand) => (
              <Card key={cand.studentProfileId}>
                <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm">{cand.fullName}</span>
                      <Badge variant={cand.isVerified ? 'emerald' : 'slate'}>
                        {cand.isVerified ? 'Verified' : 'Pending'}
                      </Badge>
                      {cand.cgpa != null && (
                        <span className="font-mono text-xs text-cyan-400 font-bold">{cand.cgpa} CGPA</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400">
                      {cand.degree} in {cand.branch} • {cand.collegeName} • Batch {cand.graduationYear}
                    </div>
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
