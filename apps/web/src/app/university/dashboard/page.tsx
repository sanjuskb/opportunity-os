'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { School, Users, Award, ShieldCheck, Briefcase } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { MetricCard } from '../../../components/ui/MetricCard';
import { useAuth } from '@/components/auth/AuthProvider';
import { QUERY_KEYS } from '@/lib/queries/useOpportunityOs';

export default function UniversityDashboardPage() {
  const { user, apiClient } = useAuth();
  const { data: overview, error } = useQuery({
    queryKey: QUERY_KEYS.universityOverview,
    queryFn: () => apiClient.getUniversityOverview(),
    enabled: Boolean(user),
    retry: false,
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">University Placement Cell</h1>
              <Badge variant="emerald">Institutional Portal</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Cohort placement analytics and institutional academic verification.
            </p>
          </div>

          <Link href="/university/verification">
            <Button variant="glow" size="sm">
              <ShieldCheck className="h-4 w-4 mr-1.5 text-emerald-300" />
              <span>Verify Pending Credentials</span>
            </Button>
          </Link>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/30 text-xs text-amber-200 flex items-center justify-between gap-3">
            <span>Switch workspace role to University to access institutional cohort metrics.</span>
            <Link href="/role-selection">
              <Button variant="outline" size="sm">Switch Workspace Role</Button>
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard title="Registered Students" value={overview?.totalStudents ?? 0} subtitle="Live cohort" icon={Users} color="emerald" />
          <MetricCard title="Verified Credentials" value={overview?.verifiedStudents ?? 0} subtitle="Institution attested" icon={Award} color="cyan" />
          <MetricCard title="Active Applications" value={overview?.activeApplications ?? 0} subtitle="Across cohort" icon={Briefcase} color="sapphire" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <School className="h-4 w-4 text-emerald-400" />
              <span>Department Cohort Distribution</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-slate-800 text-xs">
            {(overview?.departmentBreakdown ?? []).length === 0 ? (
              <p className="text-slate-400 py-4">No department records loaded.</p>
            ) : (
              overview?.departmentBreakdown.map((d) => (
                <div key={d.department} className="py-3 flex items-center justify-between">
                  <span className="font-bold text-white">{d.department}</span>
                  <span className="font-mono text-emerald-400 font-bold">{d.students} students</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
