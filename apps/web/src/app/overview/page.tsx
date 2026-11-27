'use client';

import React from 'react';
import Link from 'next/link';
import {
  Compass,
  Briefcase,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Mic,
  Award,
} from 'lucide-react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { MetricCard } from '../../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { useMockStore } from '../../lib/mock-data/mockStore';
import { useAuth } from '@/components/auth/AuthProvider';
import {
  useApplications,
  useCareerPassport,
  useCreateApplication,
  useOpportunities,
  useStudentProfile,
  useUserProfile,
} from '@/lib/queries/useOpportunityOs';

export default function OverviewPage() {
  const { user } = useAuth();
  const { setIsVoiceAssistantOpen } = useMockStore();
  const { data: userProfile } = useUserProfile();
  const { data: studentProfile } = useStudentProfile();
  const { data: passport } = useCareerPassport();
  const { data: oppPage, isLoading: loadingOpps } = useOpportunities({ limit: 10 });
  const { data: applications } = useApplications();
  const createApp = useCreateApplication();

  const opps = oppPage?.items ?? [];
  const topOpportunities = opps.slice(0, 3);
  const apps = applications ?? [];
  const displayName = userProfile?.fullName?.split(' ')[0] || user?.email?.split('@')[0] || 'Student';
  const verifiedBadgeCount =
    (passport?.verifiedAchievements?.length ?? 0) +
    (passport?.certifications?.length ?? 0) +
    (passport?.projects?.length ?? 0);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                Welcome, {displayName}
              </h1>
              <Badge variant="cyan">Student Workspace</Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              {studentProfile
                ? `${studentProfile.degree} in ${studentProfile.branch} • ${studentProfile.collegeName}`
                : 'Complete Onboarding to personalize eligibility checks and career matching.'}
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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Verified CGPA"
            value={studentProfile?.cgpa != null ? `${studentProfile.cgpa}` : '—'}
            subtitle={studentProfile ? `Batch of ${studentProfile.graduationYear}` : 'Complete onboarding'}
            icon={Award}
            color="cyan"
          />
          <MetricCard
            title="Active Opportunities"
            value={opps.length}
            subtitle="Live pgvector & SQL catalog"
            icon={Compass}
            color="amber"
          />
          <MetricCard
            title="Tracked Applications"
            value={apps.length}
            subtitle="Drafting, review & submitted"
            icon={Briefcase}
            color="sapphire"
          />
          <MetricCard
            title="Passport Records"
            value={verifiedBadgeCount}
            subtitle="Projects, certs & achievements"
            icon={ShieldCheck}
            color="emerald"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    <span>Recommended Opportunities</span>
                  </CardTitle>
                  <p className="text-xs text-slate-400 mt-1">
                    Fetched directly from PostgreSQL opportunity index.
                  </p>
                </div>
                <Link href="/opportunities" className="text-xs text-cyan-400 hover:underline">
                  View All ({opps.length})
                </Link>
              </CardHeader>

              <CardContent className="space-y-3">
                {loadingOpps ? (
                  <div className="h-24 rounded-xl border border-slate-800 bg-[#0B0F19] animate-pulse" />
                ) : topOpportunities.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400 border border-slate-800 rounded-xl">
                    Sign in or discover external opportunities to populate your feed.
                  </div>
                ) : (
                  topOpportunities.map((opp) => {
                    const isApplied = apps.some((a) => a.opportunityId === opp.id);
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
                            {opp.matchScore != null && (
                              <Badge variant="cyan">{Math.round(opp.matchScore)}% Match</Badge>
                            )}
                          </div>

                          <div className="text-xs text-slate-400 flex items-center gap-3">
                            <span className="font-medium text-slate-300">{opp.organization}</span>
                            <span>•</span>
                            <span>{opp.location}</span>
                            {opp.stipendOrSalary && (
                              <>
                                <span>•</span>
                                <span className="text-emerald-400 font-semibold">{opp.stipendOrSalary}</span>
                              </>
                            )}
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
                              Drafted
                            </Button>
                          ) : (
                            <Button
                              variant="primary"
                              size="sm"
                              isLoading={createApp.isPending}
                              onClick={() => void createApp.mutate(opp.id)}
                            >
                              Apply
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-violet-400" />
                  <span>Application Tracking Pipeline</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {apps.length === 0 ? (
                  <p className="text-xs text-slate-400">No applications created yet.</p>
                ) : (
                  apps.slice(0, 5).map((app) => {
                    const opp = opps.find((o) => o.id === app.opportunityId);
                    return (
                      <div
                        key={app.id}
                        className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center justify-between text-xs"
                      >
                        <div className="space-y-1">
                          <div className="font-bold text-white">{opp?.title || app.opportunityId}</div>
                          <div className="text-slate-400">
                            Method: {app.submissionMethod} • Updated{' '}
                            {app.createdAt ? new Date(app.createdAt).toLocaleDateString() : 'Recent'}
                          </div>
                        </div>
                        <Badge variant={app.status === 'submitted' ? 'cyan' : app.status === 'ready_for_review' ? 'amber' : 'slate'}>
                          {app.status.replace(/_/g, ' ')}
                        </Badge>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border-cyan-500/20 bg-gradient-to-b from-[#0D1322] to-[#0B0F19]">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="cyan">Career Passport</Badge>
                  <span className="font-mono text-[10px] text-slate-400">{passport?.id?.slice(0, 8) || 'Draft'}</span>
                </div>
                <CardTitle className="pt-2">{userProfile?.fullName || displayName}</CardTitle>
                <p className="text-xs text-slate-400">{studentProfile?.bio || 'Student Profile'}</p>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="rounded-lg border border-slate-800 bg-[#0B0F19] p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">CGPA:</span>
                    <span className="font-bold text-emerald-400">{studentProfile?.cgpa ?? '—'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">College:</span>
                    <span className="font-medium text-slate-200 truncate max-w-[160px]">
                      {studentProfile?.collegeName || '—'}
                    </span>
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

            <Card className="border-violet-500/20 bg-gradient-to-b from-violet-950/20 to-[#0B0F19]">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mic className="h-4 w-4 text-violet-400 animate-pulse" />
                  <CardTitle className="text-sm">Multilingual Voice Mode</CardTitle>
                </div>
                <p className="text-xs text-slate-300">
                  Explore opportunities or practice mock interviews in 9 Indian regional languages.
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
