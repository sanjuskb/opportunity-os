'use client';

import React from 'react';
import Link from 'next/link';
import { Building2, PlusCircle, Users, Briefcase, Sparkles, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { MetricCard } from '../../../components/ui/MetricCard';
import { useMockStore } from '../../../lib/mock-data/mockStore';

export default function CompanyDashboardPage() {
  const { opportunities, candidates, applications } = useMockStore();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Recruiter Command Center</h1>
              <Badge variant="sapphire">Company Portal</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Direct access to pre-verified Indian collegiate talent with zero hallucination credentials.
            </p>
          </div>

          <Link href="/company/create">
            <Button variant="glow" size="sm">
              <PlusCircle className="h-4 w-4 mr-1.5" />
              <span>Post New Opportunity</span>
            </Button>
          </Link>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Active Postings"
            value={opportunities.length}
            subtitle="Live across NexteRaS"
            icon={Briefcase}
            color="sapphire"
          />
          <MetricCard
            title="Total Applicants"
            value={applications.length + 14}
            subtitle="100% verified colleges"
            trend="+8 today"
            icon={Users}
            color="cyan"
          />
          <MetricCard
            title="Avg Candidate Score"
            value="94.2%"
            subtitle="Verified technical rubric"
            icon={Sparkles}
            color="violet"
          />
          <MetricCard
            title="DigiLocker Accredited"
            value="100%"
            subtitle="AICTE verified records"
            icon={ShieldCheck}
            color="emerald"
          />
        </div>

        {/* Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Job Openings (2 Cols) */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Active Campus Postings</CardTitle>
                <Link href="/company/create" className="text-xs text-cyan-400 hover:underline">
                  + Create Role
                </Link>
              </CardHeader>

              <CardContent className="space-y-3">
                {opportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19] flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="font-bold text-white text-sm">{opp.title}</div>
                      <div className="text-xs text-slate-400">
                        {opp.location} • <span className="text-emerald-400 font-semibold">{opp.stipendOrSalary}</span> • Deadline: {opp.deadline || 'Rolling'}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Link href={`/opportunities/${opp.id}`}>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Recent Candidate Matches (1 Col) */}
          <div className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-sm">Verified Candidates</CardTitle>
                <Link href="/company/candidates" className="text-xs text-cyan-400 hover:underline">
                  View All ({candidates.length})
                </Link>
              </CardHeader>

              <CardContent className="space-y-3">
                {candidates.map((cand) => (
                  <div
                    key={cand.id}
                    className="p-3 rounded-lg border border-slate-800 bg-[#0B0F19] space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{cand.fullName}</span>
                      <span className="font-mono text-cyan-400 font-bold">{cand.cgpa} CGPA</span>
                    </div>
                    <div className="text-slate-400 text-[11px] truncate">
                      {cand.degree} • {cand.collegeName}
                    </div>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {cand.skills.slice(0, 3).map((sk) => (
                        <span key={sk} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-900 text-slate-300 border border-slate-800">
                          {sk}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
