'use client';

import React from 'react';
import Link from 'next/link';
import {
  Compass,
  FileText,
  Briefcase,
  Award,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Mic,
} from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { MetricCard } from '../../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { MOCK_ELIGIBILITY_CACHE } from '../../lib/mock-data/opportunities';

export default function OverviewPage() {
  const { studentProfile, opportunities, applications, setIsVoiceAssistantOpen, applyToOpportunity } = useMockStore();

  const topOpportunities = opportunities.slice(0, 3);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Greeting & Action Strip */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                Welcome, {studentProfile.fullName.split(' ')[0]}
              </h1>
              <Badge variant="cyan">Student Workspace</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              {studentProfile.degree} in {studentProfile.branch} • {studentProfile.collegeName}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsVoiceAssistantOpen(true)}
              className="border-violet-500/40 text-violet-300 bg-violet-950/20 hover:bg-violet-900/30"
            >
              <Mic className="h-4 w-4 mr-1.5 text-violet-400" />
              <span>Voice Assistant</span>
            </Button>
            <Link href="/opportunities">
              <Button variant="glow" size="sm">
                <span>Discover Opportunities</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>

        {/* 4 Core Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="ATS Match Score"
            value={`${studentProfile.atsScore}%`}
            subtitle="Top 5% across Indian applicants"
            trend="+6% tailored"
            icon={FileText}
            color="cyan"
          />
          <MetricCard
            title="Ingested Opportunities"
            value="10,480"
            subtitle="Verified across 14 platforms"
            trend="+142 today"
            icon={Compass}
            color="amber"
          />
          <MetricCard
            title="Active Applications"
            value={applications.length}
            subtitle="1 submitted, 2 in drafting"
            icon={Briefcase}
            color="sapphire"
          />
          <MetricCard
            title="Verified Credentials"
            value={studentProfile.verifiedCredentials.length}
            subtitle="AICTE DigiLocker accredited"
            icon={ShieldCheck}
            color="emerald"
          />
        </div>

        {/* Two-Column Command Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 Cols): Top AI Matched Opportunities */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    <span>Top AI-Matched Opportunities</span>
                  </CardTitle>
                  <p className="text-xs text-slate-400 mt-1">
                    Ranked by deterministic eligibility checks and skill graph overlap.
                  </p>
                </div>
                <Link href="/opportunities" className="text-xs text-cyan-400 hover:underline">
                  View All ({opportunities.length})
                </Link>
              </CardHeader>

              <CardContent className="space-y-3">
                {topOpportunities.map((opp) => {
                  const match = MOCK_ELIGIBILITY_CACHE[opp.id];
                  const isApplied = applications.some((a) => a.opportunityId === opp.id);

                  return (
                    <div
                      key={opp.id}
                      className="p-4 rounded-xl border border-slate-800 bg-[#0B0F19] hover:border-slate-700 transition flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Link href={`/opportunities/${opp.id}`} className="font-bold text-white text-sm hover:text-cyan-300 transition">
                            {opp.title}
                          </Link>
                          {match && (
                            <Badge variant={match.score >= 90 ? 'cyan' : 'emerald'}>
                              {match.score}% Match
                            </Badge>
                          )}
                        </div>

                        <div className="text-xs text-slate-400 flex items-center gap-3">
                          <span className="font-medium text-slate-300">{opp.organization}</span>
                          <span>•</span>
                          <span>{opp.location}</span>
                          <span>•</span>
                          <span className="text-emerald-400 font-semibold">{opp.stipendOrSalary}</span>
                        </div>

                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {opp.requiredSkills.slice(0, 4).map((sk) => (
                            <span key={sk} className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 w-full sm:w-auto">
                        <Link href={`/opportunities/${opp.id}`}>
                          <Button variant="outline" size="sm">
                            Inspect
                          </Button>
                        </Link>
                        {isApplied ? (
                          <Button variant="secondary" size="sm" disabled>
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mr-1" />
                            Applied
                          </Button>
                        ) : (
                          <Button variant="primary" size="sm" onClick={() => applyToOpportunity(opp.id)}>
                            Apply
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Application Pipeline Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-violet-400" />
                  <span>Application Tracking Pipeline</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {applications.map((app) => {
                  const opp = opportunities.find((o) => o.id === app.opportunityId);
                  return (
                    <div
                      key={app.id}
                      className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center justify-between text-xs"
                    >
                      <div className="space-y-1">
                        <div className="font-bold text-white">{opp?.title || 'Opportunity Application'}</div>
                        <div className="text-slate-400">{opp?.organization} • Applied {new Date(app.appliedAt).toLocaleDateString()}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={app.status === 'submitted' ? 'cyan' : app.status === 'ready_for_review' ? 'amber' : 'slate'}>
                          {app.status.replace(/_/g, ' ')}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Career Passport Snapshot */}
          <div className="space-y-6">
            <Card className="border-cyan-500/20 bg-gradient-to-b from-[#0D1322] to-[#0B0F19]">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="cyan">Career Passport</Badge>
                  <span className="font-mono text-[10px] text-slate-400">{studentProfile.careerPassportId}</span>
                </div>
                <CardTitle className="pt-2">{studentProfile.fullName}</CardTitle>
                <p className="text-xs text-slate-400">{studentProfile.headline}</p>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="rounded-lg border border-slate-800 bg-[#0B0F19] p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Accredited CGPA:</span>
                    <span className="font-bold text-emerald-400">{studentProfile.cgpa} / 10.0</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">College:</span>
                    <span className="font-medium text-slate-200 truncate max-w-[160px]">{studentProfile.collegeName}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Verification:</span>
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      DigiLocker AICTE
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Verified Skill Badges:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {studentProfile.skills.slice(0, 6).map((sk) => (
                      <span key={sk} className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-cyan-300 border border-slate-700">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800">
                  <Link href="/career-passport">
                    <Button variant="outline" size="sm" className="w-full">
                      <span>View Full Career Passport</span>
                      <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Quick Voice Assistant Card */}
            <Card className="border-violet-500/20 bg-gradient-to-b from-violet-950/20 to-[#0B0F19]">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mic className="h-4 w-4 text-violet-400 animate-pulse" />
                  <CardTitle className="text-sm">Multilingual Voice Mode</CardTitle>
                </div>
                <p className="text-xs text-slate-300">
                  Explore opportunities or practice mock interviews in 7 Indian regional languages.
                </p>
              </CardHeader>
              <CardContent>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsVoiceAssistantOpen(true)}
                  className="w-full bg-violet-600 hover:bg-violet-500 text-white"
                >
                  <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                  <span>Start Voice Session</span>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
