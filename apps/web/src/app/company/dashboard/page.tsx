'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PlusCircle, Users, Briefcase, Sparkles, ShieldCheck } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { MetricCard } from '../../../components/ui/MetricCard';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS, useOpportunities } from '@/lib/queries/useOpportunityOs';

export default function CompanyDashboardPage() {
  const { user, apiClient } = useAuth();
  const { data: oppPage } = useOpportunities({ limit: 30 });
  const { data: candidates, error: candError } = useQuery({
    queryKey: QUERY_KEYS.companyCandidates(),
    queryFn: () => apiClient.listCompanyCandidates(),
    enabled: Boolean(user),
    retry: false,
  });
  const { data: applicants } = useQuery({
    queryKey: QUERY_KEYS.companyApplicants,
    queryFn: () => apiClient.listCompanyApplicants(),
    enabled: Boolean(user),
    retry: false,
  });

  const opportunities = oppPage?.items ?? [];
  const verifiedCount = (candidates ?? []).filter((c) => c.isVerified).length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Recruiter Command Center</h1>
              <Badge variant="sapphire">Company Portal</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Publish verified roles and inspect skill-indexed student candidates.
            </p>
          </div>

          <Link href="/company/create">
            <Button variant="glow" size="sm">
              <PlusCircle className="h-4 w-4 mr-1.5" />
              <span>Post New Opportunity</span>
            </Button>
          </Link>
        </div>

        {candError && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200 flex items-center justify-between gap-3">
            <span>Recruiter portal endpoints require your workspace role to be set to Company.</span>
            <Link href="/role-selection">
              <Button variant="outline" size="sm">Switch Workspace Role</Button>
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Active Postings" value={opportunities.length} subtitle="Live catalog" icon={Briefcase} color="sapphire" />
          <MetricCard title="Applicants" value={(applicants ?? []).length} subtitle="PostgreSQL tracked" icon={Users} color="cyan" />
          <MetricCard title="Talent Pool" value={(candidates ?? []).length} subtitle="Registered student profiles" icon={Sparkles} color="violet" />
          <MetricCard title="Institution Verified" value={verifiedCount} subtitle="University accredited" icon={ShieldCheck} color="emerald" />
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Active Postings</CardTitle>
            <Link href="/company/create" className="text-xs text-cyan-400 hover:underline">+ Create Role</Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {opportunities.slice(0, 8).map((opp) => (
              <div key={opp.id} className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19] flex items-center justify-between">
                <div className="space-y-1">
                  <div className="font-bold text-white text-sm">{opp.title}</div>
                  <div className="text-xs text-slate-400">
                    {opp.organization} • {opp.location} {opp.stipendOrSalary ? `• ${opp.stipendOrSalary}` : ''}
                  </div>
                </div>
                <Link href={`/opportunities/${opp.id}`}>
                  <Button variant="outline" size="sm">View Details</Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
