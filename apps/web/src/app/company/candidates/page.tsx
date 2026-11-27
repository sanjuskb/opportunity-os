'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Input } from '../../../components/ui/Input';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS } from '@/lib/queries/useOpportunityOs';

export default function CandidateDiscoveryPage() {
  const { user, apiClient } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const { data: candidates, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.companyCandidates(searchQuery),
    queryFn: () => apiClient.listCompanyCandidates(searchQuery || undefined),
    enabled: Boolean(user),
    retry: false,
  });

  const rows = candidates ?? [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Candidate Discovery Feed</h1>
              <Badge variant="sapphire">Pre-Screened Talent</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Discover verified student profiles directly from PostgreSQL.
            </p>
          </div>
          <div className="text-xs text-slate-400 font-mono">
            Showing <span className="text-blue-400 font-bold">{rows.length}</span> profiles
          </div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19]">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter candidates by name, college, branch, or skill..."
          />
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200">
            Switch workspace role to Company or University to access candidate talent directory.
          </div>
        )}

        {isLoading ? (
          <div className="h-40 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rows.map((cand) => (
              <Card key={cand.studentProfileId}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-bold text-base text-white">{cand.fullName}</div>
                      <div className="text-xs text-slate-400">
                        {cand.degree} {cand.branch} • {cand.collegeName} (Batch {cand.graduationYear})
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="font-bold text-emerald-400 text-sm">
                        {cand.cgpa != null ? `${cand.cgpa} CGPA` : '—'}
                      </div>
                      <Badge variant={cand.isVerified ? 'emerald' : 'slate'}>
                        {cand.isVerified ? 'Verified' : 'Unverified'}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {cand.skills.map((sk) => (
                      <span key={sk} className="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800">
                        {sk}
                      </span>
                    ))}
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
